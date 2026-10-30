FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr libmagic1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY templates ./templates
COPY static ./static
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
COPY worker.py ./worker.py
COPY startup.py ./startup.py
EXPOSE 8000
CMD ["python", "startup.py"]
