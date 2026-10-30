import json
import time

import boto3
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal, engine
from app.models import ProcessingJob
from app.processing import process_job


def run() -> None:
    while True:
        try:
            with engine.connect() as connection:
                connection.exec_driver_sql("SELECT 1")
            break
        except Exception:
            time.sleep(5)
    if settings.sqs_job_queue_url:
        sqs = boto3.client("sqs", region_name=settings.aws_region)
        while True:
            response = sqs.receive_message(
                QueueUrl=settings.sqs_job_queue_url, MaxNumberOfMessages=5, WaitTimeSeconds=20,
                MessageAttributeNames=["All"],
            )
            for message in response.get("Messages", []):
                body = json.loads(message["Body"])
                try:
                    process_job(int(body["job_id"]))
                    sqs.delete_message(QueueUrl=settings.sqs_job_queue_url, ReceiptHandle=message["ReceiptHandle"])
                except Exception:
                    time.sleep(2)
    else:
        while True:
            with SessionLocal() as db:
                job = db.scalar(select(ProcessingJob).where(ProcessingJob.status == "queued").order_by(ProcessingJob.id))
            if job:
                process_job(job.id)
            else:
                time.sleep(2)


if __name__ == "__main__":
    run()
