import json

import boto3

from .config import settings
from .models import ProcessingJob


def dispatch_job(job: ProcessingJob) -> None:
    if settings.sqs_job_queue_url:
        boto3.client("sqs", region_name=settings.aws_region).send_message(
            QueueUrl=settings.sqs_job_queue_url,
            MessageBody=json.dumps({"job_id": job.id}),
            MessageAttributes={"job_id": {"DataType": "Number", "StringValue": str(job.id)}},
        )
