from datetime import datetime, timezone

import httpx

from .config import settings
from .privacy import strip_identifiers


class AIUnavailable(RuntimeError):
    pass


class AIProvider:
    """Small OpenAI-compatible adapter; a reviewed provider must be configured before activation."""

    async def complete(self, messages: list[dict]) -> str:
        if not settings.ai_enabled or not settings.ai_base_url or not settings.ai_api_key or not settings.ai_model:
            raise AIUnavailable("AI assistance is not configured yet")
        url = settings.ai_base_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url += "/chat/completions"
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                json={"model": settings.ai_model, "messages": messages, "temperature": 0.2},
            )
            response.raise_for_status()
            payload = response.json()
        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIUnavailable("AI provider returned an unsupported response") from exc


provider = AIProvider()


def build_lab_context(case) -> tuple[str, list[dict]]:
    lines = [f"Case code: {case.case_code}", f"Case notes: {case.summary}"]
    citations = []
    for result in case.results:
        lines.append(
            f"{result.test_name}: {result.value} {result.unit}; reference {result.reference_range}; "
            f"status {result.status}; technical notes {result.notes}"
        )
        citations.append({"type": "test_result", "id": result.id, "label": result.test_name})
    context = "\n".join(lines)
    if case.patient_identity_ciphertext:
        try:
            from .privacy import decrypt_patient_identity
            identity = decrypt_patient_identity(case.patient_identity_ciphertext)
            if identity:
                context = context.replace(identity, "[REDACTED PATIENT IDENTITY]")
        except RuntimeError:
            pass
    return strip_identifiers(context), citations


def month_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
