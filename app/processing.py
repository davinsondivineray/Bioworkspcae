import ipaddress
import csv
import io
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader

from .database import SessionLocal
from .models import LearningSource, ProcessingJob, Upload
from .storage import read_upload


def _extract_upload_text(upload: Upload) -> str:
    content = read_upload(upload.storage_key)
    suffix = Path(upload.filename).suffix.lower()
    if suffix == ".pdf":
        import io
        import pytesseract
        from PIL import Image
        import pypdfium2 as pdfium
        reader = PdfReader(io.BytesIO(content))
        document = pdfium.PdfDocument(content)
        pages = []
        for index, page in enumerate(reader.pages[:30]):
            text = page.extract_text() or ""
            if len(text.strip()) < 40:
                image = document[index].render(scale=1.5).to_pil()
                text = pytesseract.image_to_string(image)
            pages.append(text)
        document.close()
        return "\n".join(pages)[:250_000]
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        import io
        from PIL import Image
        import pytesseract
        return pytesseract.image_to_string(Image.open(io.BytesIO(content)))[:250_000]
    if suffix == ".csv":
        return content.decode("utf-8-sig", errors="replace")[:250_000]
    if suffix == ".xlsx":
        import io
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        return "\n".join(" | ".join(str(cell or "") for cell in row) for sheet in workbook for row in sheet.iter_rows(values_only=True))[:250_000]
    if suffix == ".docx":
        import io
        document = Document(io.BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)[:250_000]
    if suffix == ".txt":
        return content.decode("utf-8-sig", errors="replace")[:250_000]
    return ""


def _extract_spreadsheet_rows(upload: Upload) -> list[dict]:
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        return []
    content = read_upload(upload.storage_key)
    if suffix == ".csv":
        return [dict(row) for row in csv.DictReader(io.StringIO(content.decode("utf-8-sig", errors="replace")))][:500]
    from openpyxl import load_workbook
    workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    sheet = workbook.active
    rows = sheet.iter_rows(values_only=True)
    headers = [str(value or "").strip() for value in next(rows, ())]
    headers = [header or f"Column {index + 1}" for index, header in enumerate(headers)]
    parsed = []
    for row in rows:
        if not any(value is not None for value in row):
            continue
        parsed.append({header: str(value) if value is not None else "" for header, value in zip(headers, row)})
        if len(parsed) >= 500:
            break
    return parsed


def _public_https_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only public HTTPS URLs are supported")
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    if not addresses:
        raise ValueError("URL host could not be resolved")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("Private or local network URLs cannot be indexed")


def process_job(job_id: int) -> None:
    with SessionLocal() as db:
        job = db.get(ProcessingJob, job_id)
        if not job or job.status == "completed":
            return
        job.status = "processing"
        job.attempts += 1
        db.commit()
        try:
            if job.kind == "upload":
                upload = db.get(Upload, job.object_id)
                if not upload:
                    raise ValueError("Upload not found")
                upload.extracted_text = _extract_upload_text(upload)
                upload.extracted_rows = _extract_spreadsheet_rows(upload)
                upload.status = "ready"
            elif job.kind == "source":
                source = db.get(LearningSource, job.object_id)
                if not source:
                    raise ValueError("Learning source not found")
                _public_https_url(source.url)
                with httpx.Client(timeout=20, follow_redirects=False, trust_env=False,
                                  headers={"User-Agent": "BioWorkspaceStudy/1.0"}) as client:
                    with client.stream("GET", source.url) as response:
                        if response.status_code >= 300:
                            raise ValueError("The public page could not be fetched")
                        if "text/html" not in response.headers.get("content-type", ""):
                            raise ValueError("Only public HTML pages can be indexed")
                        chunks, size = [], 0
                        for chunk in response.iter_bytes():
                            size += len(chunk)
                            if size > 2_000_000:
                                raise ValueError("The page is larger than the indexing limit")
                            chunks.append(chunk)
                        html = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
                soup = BeautifulSoup(html, "html.parser")
                for node in soup(["script", "style", "noscript", "svg"]):
                    node.decompose()
                source.title = (soup.title.string.strip() if soup.title and soup.title.string else source.url)[:300]
                source.extracted_text = soup.get_text(" ", strip=True)[:250_000]
                source.status = "ready"
            else:
                raise ValueError("Unsupported processing task")
            job.status = "completed"
            job.error_code = ""
            db.commit()
        except Exception as exc:
            db.rollback()
            job = db.get(ProcessingJob, job_id)
            if job:
                job.status = "failed"
                job.error_code = type(exc).__name__[:80]
                if job.kind == "upload":
                    upload = db.get(Upload, job.object_id)
                    if upload:
                        upload.status = "failed"
                elif job.kind == "source":
                    source = db.get(LearningSource, job.object_id)
                    if source:
                        source.status = "failed"
                db.commit()
