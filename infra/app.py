import os

import aws_cdk as cdk

from infra.stack import BiotechPlatformStack


app = cdk.App()
stage = os.getenv("DEPLOY_STAGE", "staging")
region = os.getenv("CDK_DEFAULT_REGION", "eu-west-1")
account = os.getenv("CDK_DEFAULT_ACCOUNT")
BiotechPlatformStack(
    app, f"BiotechPlatform-{stage}", stage=stage,
    env=cdk.Environment(account=account, region=region),
)
app.synth()
