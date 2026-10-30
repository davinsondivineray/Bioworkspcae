from pathlib import Path

import aws_cdk as cdk
from aws_cdk import (
    Duration, RemovalPolicy, SecretValue,
    aws_budgets as budgets, aws_cloudwatch_actions as cloudwatch_actions, aws_cognito as cognito, aws_ec2 as ec2,
    aws_ecs as ecs, aws_elasticloadbalancingv2 as elbv2, aws_iam as iam, aws_logs as logs,
    aws_rds as rds, aws_s3 as s3, aws_secretsmanager as secretsmanager,
    aws_sns as sns, aws_sns_subscriptions as sns_subscriptions, aws_sqs as sqs,
)
from constructs import Construct


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class BiotechPlatformStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, *, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        if self.region != "eu-west-1":
            raise ValueError("The initial data region is eu-west-1")

        production = stage == "production"
        domain_name = self.node.try_get_context("domainName")
        certificate_arn = self.node.try_get_context("certificateArn")
        app_url = self.node.try_get_context("appUrl") or (f"https://{domain_name}" if domain_name else "http://localhost:8000")
        if not domain_name or not certificate_arn:
            raise ValueError("AWS stages require domainName and certificateArn context values for HTTPS")
        if app_url.rstrip("/").lower() != f"https://{domain_name}".lower():
            raise ValueError("appUrl must match https://domainName exactly")

        vpc = ec2.Vpc(self, "Vpc", max_azs=2, nat_gateways=1,
                      subnet_configuration=[
                          ec2.SubnetConfiguration(name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24),
                          ec2.SubnetConfiguration(name="App", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24),
                          ec2.SubnetConfiguration(name="Data", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, cidr_mask=24),
                      ])

        user_pool = cognito.UserPool(
            self, "UserPool", user_pool_name=f"biotech-{stage}", self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                fullname=cognito.StandardAttribute(mutable=True),
            ),
            password_policy=cognito.PasswordPolicy(min_length=12, require_digits=True,
                                                   require_lowercase=True, require_uppercase=True,
                                                   require_symbols=True),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.RETAIN if production else RemovalPolicy.DESTROY,
        )
        prefix = self.node.try_get_context("cognitoDomainPrefix") or f"biotech-{self.account}-{stage}"
        user_pool.add_domain("HostedDomain", cognito_domain=cognito.CognitoDomainOptions(domain_prefix=prefix))

        provider_ids = [cognito.UserPoolClientIdentityProvider.COGNITO]
        google_id = self.node.try_get_context("googleClientId")
        google_secret_arn = self.node.try_get_context("googleClientSecretArn")
        if google_id and google_secret_arn:
            cognito.CfnUserPoolIdentityProvider(
                self, "GoogleProvider", user_pool_id=user_pool.user_pool_id,
                provider_name="Google", provider_type="Google",
                provider_details={
                    "client_id": google_id,
                    "client_secret": SecretValue.secrets_manager(google_secret_arn).unsafe_unwrap(),
                    "authorize_scopes": "openid email profile",
                },
                attribute_mapping={"email": "email", "name": "name"},
            )
            provider_ids.append(cognito.UserPoolClientIdentityProvider.GOOGLE)

        tenant_id = self.node.try_get_context("microsoftTenantId")
        microsoft_id = self.node.try_get_context("microsoftClientId")
        microsoft_secret_arn = self.node.try_get_context("microsoftClientSecretArn")
        if tenant_id and microsoft_id and microsoft_secret_arn:
            cognito.CfnUserPoolIdentityProvider(
                self, "MicrosoftProvider", user_pool_id=user_pool.user_pool_id,
                provider_name="Microsoft", provider_type="OIDC",
                provider_details={
                    "client_id": microsoft_id,
                    "client_secret": SecretValue.secrets_manager(microsoft_secret_arn).unsafe_unwrap(),
                    "oidc_issuer": f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                    "attributes_request_method": "GET",
                    "authorize_scopes": "openid email profile",
                },
                attribute_mapping={"email": "email", "name": "name"},
            )
            provider_ids.append(cognito.UserPoolClientIdentityProvider.custom("Microsoft"))

        app_client = user_pool.add_client(
            "WebClient", user_pool_client_name=f"biotech-web-{stage}", generate_secret=False,
            auth_flows=cognito.AuthFlow(user_srp=True, user_password=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL, cognito.OAuthScope.PROFILE],
                callback_urls=[f"{app_url.rstrip('/')}/auth/callback"],
                logout_urls=[app_url.rstrip("/") + "/"],
            ),
            supported_identity_providers=provider_ids,
            prevent_user_existence_errors=True,
        )

        bucket = s3.Bucket(
            self, "PrivateUploads", block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED, enforce_ssl=True,
            versioned=production,
            removal_policy=RemovalPolicy.RETAIN,
        )
        dead_letters = sqs.Queue(self, "ProcessingDeadLetterQueue", retention_period=Duration.days(14),
                                 encryption=sqs.QueueEncryption.SQS_MANAGED)
        jobs = sqs.Queue(self, "ProcessingJobs", visibility_timeout=Duration.minutes(8),
                         retention_period=Duration.days(4), encryption=sqs.QueueEncryption.SQS_MANAGED,
                         dead_letter_queue=sqs.DeadLetterQueue(queue=dead_letters, max_receive_count=4))

        db = rds.DatabaseInstance(
            self, "Database", engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.of("17", "17.11")),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE4_GRAVITON, ec2.InstanceSize.MICRO),
            vpc=vpc, vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            database_name="biotech", credentials=rds.Credentials.from_generated_secret("biotech_admin"),
            allocated_storage=20, max_allocated_storage=100, storage_encrypted=True,
            backup_retention=Duration.days(7), multi_az=False, publicly_accessible=False,
            deletion_protection=production,
            removal_policy=RemovalPolicy.RETAIN if production else RemovalPolicy.DESTROY,
        )

        cluster = ecs.Cluster(self, "Cluster", vpc=vpc, container_insights=True)
        session_secret = secretsmanager.Secret(
            self, "SessionSecret", description="BioWorkspace session signing secret",
            generate_secret_string=secretsmanager.SecretStringGenerator(password_length=48, exclude_punctuation=True),
        )
        image = ecs.ContainerImage.from_asset(str(PROJECT_ROOT))
        log_group = logs.LogGroup(self, "AppLogs", retention=logs.RetentionDays.ONE_MONTH,
                                  removal_policy=RemovalPolicy.RETAIN if production else RemovalPolicy.DESTROY)
        task = ecs.FargateTaskDefinition(self, "WebTask", cpu=512, memory_limit_mib=1024)
        container = task.add_container(
            "Web", image=image,
            logging=ecs.LogDrivers.aws_logs(stream_prefix=f"biotech-{stage}", log_group=log_group),
            environment={
                "APP_ENV": "production", "DEV_AUTH": "false", "AWS_REGION": self.region,
                "DB_HOST": db.db_instance_endpoint_address, "DB_NAME": "biotech",
                "S3_BUCKET": bucket.bucket_name, "SQS_JOB_QUEUE_URL": jobs.queue_url,
                "COGNITO_DOMAIN": f"https://{prefix}.auth.{self.region}.amazoncognito.com",
                "COGNITO_CLIENT_ID": app_client.user_pool_client_id,
                "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
                "COGNITO_REDIRECT_URI": app_url.rstrip("/") + "/auth/callback",
                "IDENTIFIABLE_RECORDS_ENABLED": "false", "AI_ENABLED": "false",
                "MAX_UPLOAD_MB": "20", "AI_MONTHLY_REQUEST_LIMIT": "100",
                "ALLOWED_ORIGINS": app_url.rstrip("/"), "EDITOR_EMAILS": self.node.try_get_context("editorEmails") or "",
            },
            secrets={
                "SESSION_SECRET": ecs.Secret.from_secrets_manager(session_secret),
                "DB_USER": ecs.Secret.from_secrets_manager(db.secret, "username"),
                "DB_PASSWORD": ecs.Secret.from_secrets_manager(db.secret, "password"),
            },
            health_check=ecs.HealthCheck(command=["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health')\""],
                                         interval=Duration.seconds(30), timeout=Duration.seconds(5), retries=3,
                                         start_period=Duration.seconds(60)),
        )
        container.add_port_mappings(ecs.PortMapping(container_port=8000, protocol=ecs.Protocol.TCP))
        service = ecs.FargateService(self, "WebService", cluster=cluster, task_definition=task,
                                     desired_count=1, assign_public_ip=False,
                                     vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                                     circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True))
        bucket.grant_read_write(task.task_role)
        jobs.grant_send_messages(task.task_role)
        task.task_role.add_to_policy(iam.PolicyStatement(
            actions=["cognito-idp:AdminDeleteUser"], resources=[user_pool.user_pool_arn],
        ))
        session_secret.grant_read(task.task_execution_role)
        db.secret.grant_read(task.task_execution_role)
        db.connections.allow_default_port_from(service)

        worker_task = ecs.FargateTaskDefinition(self, "WorkerTask", cpu=512, memory_limit_mib=1024)
        worker_task.add_container(
            "Worker", image=image, command=["python", "worker.py"],
            logging=ecs.LogDrivers.aws_logs(stream_prefix=f"biotech-worker-{stage}", log_group=log_group),
            environment={
                "APP_ENV": "production", "DEV_AUTH": "false", "AWS_REGION": self.region,
                "DB_HOST": db.db_instance_endpoint_address, "DB_NAME": "biotech",
                "S3_BUCKET": bucket.bucket_name, "SQS_JOB_QUEUE_URL": jobs.queue_url,
                "IDENTIFIABLE_RECORDS_ENABLED": "false", "AI_ENABLED": "false",
            },
            secrets={
                "SESSION_SECRET": ecs.Secret.from_secrets_manager(session_secret),
                "DB_USER": ecs.Secret.from_secrets_manager(db.secret, "username"),
                "DB_PASSWORD": ecs.Secret.from_secrets_manager(db.secret, "password"),
            },
        )
        worker = ecs.FargateService(self, "WorkerService", cluster=cluster, task_definition=worker_task,
                                    desired_count=1, assign_public_ip=False,
                                    vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS))
        jobs.grant_consume_messages(worker_task.task_role)
        bucket.grant_read_write(worker_task.task_role)
        db.secret.grant_read(worker_task.task_execution_role)
        session_secret.grant_read(worker_task.task_execution_role)
        db.connections.allow_default_port_from(worker)

        alb = elbv2.ApplicationLoadBalancer(self, "LoadBalancer", vpc=vpc, internet_facing=True)
        if certificate_arn:
            from aws_cdk import aws_certificatemanager as acm
            certificate = acm.Certificate.from_certificate_arn(self, "ImportedCertificate", certificate_arn)
            https = alb.add_listener("HttpsListener", port=443, certificates=[certificate], open=True)
            alb.add_listener("HttpRedirect", port=80, default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS", port="443", permanent=True))
            scheme = "https"
        else:
            https = alb.add_listener("HttpListener", port=80, open=True)
            scheme = "http"
        https.add_targets("WebTargets", port=8000, targets=[service],
                          health_check=elbv2.HealthCheck(path="/health", healthy_http_codes="200"))
        service.connections.allow_from(alb, ec2.Port.tcp(8000))

        scalable = service.auto_scale_task_count(min_capacity=1, max_capacity=3)
        scalable.scale_on_cpu_utilization("CpuScaling", target_utilization_percent=65,
                                          scale_in_cooldown=Duration.seconds(180),
                                          scale_out_cooldown=Duration.seconds(60))
        budget_email = self.node.try_get_context("budgetEmail")
        if not budget_email:
            raise ValueError("Set budgetEmail context to receive the required AWS cost alerts")
        alarm_topic = sns.Topic(self, "OperationsAlerts", topic_name=f"biotech-{stage}-alerts")
        alarm_topic.add_subscription(sns_subscriptions.EmailSubscription(budget_email))
        cpu_alarm = service.metric_cpu_utilization().create_alarm(self, "HighCpu", threshold=85,
                                                                  evaluation_periods=3, datapoints_to_alarm=2)
        cpu_alarm.add_alarm_action(cloudwatch_actions.SnsAction(alarm_topic))
        elb_error_alarm = alb.metric_http_code_elb(elb_code=elbv2.HttpCodeElb.ELB_5XX_COUNT).create_alarm(
            self, "LoadBalancerErrors", threshold=5, evaluation_periods=1,
        )
        elb_error_alarm.add_alarm_action(cloudwatch_actions.SnsAction(alarm_topic))
        budgets.CfnBudget(
                self, "MonthlyCostBudget",
                budget=budgets.CfnBudget.BudgetDataProperty(
                    budget_type="COST", time_unit="MONTHLY", budget_limit={"amount": 500, "unit": "USD"},
                ),
                notifications_with_subscribers=[
                    budgets.CfnBudget.NotificationWithSubscribersProperty(
                        notification=budgets.CfnBudget.NotificationProperty(
                            notification_type="ACTUAL", comparison_operator="GREATER_THAN",
                            threshold=80, threshold_type="PERCENTAGE"),
                        subscribers=[budgets.CfnBudget.SubscriberProperty(
                            subscription_type="EMAIL", address=budget_email)],
                    ),
                    budgets.CfnBudget.NotificationWithSubscribersProperty(
                        notification=budgets.CfnBudget.NotificationProperty(
                            notification_type="FORECASTED", comparison_operator="GREATER_THAN",
                            threshold=100, threshold_type="PERCENTAGE"),
                        subscribers=[budgets.CfnBudget.SubscriberProperty(
                            subscription_type="EMAIL", address=budget_email)],
                    ),
                ],
        )

        cdk.CfnOutput(self, "AppUrl", value=f"{scheme}://{domain_name}" if domain_name else f"{scheme}://{alb.load_balancer_dns_name}")
        cdk.CfnOutput(self, "LoadBalancerDns", value=alb.load_balancer_dns_name)
        cdk.CfnOutput(self, "CognitoDomain", value=f"https://{prefix}.auth.{self.region}.amazoncognito.com")
        cdk.CfnOutput(self, "CognitoClientId", value=app_client.user_pool_client_id)
        cdk.CfnOutput(self, "DatabaseEndpoint", value=db.db_instance_endpoint_address)
        cdk.CfnOutput(self, "UploadsBucket", value=bucket.bucket_name)
        cdk.CfnOutput(self, "ProcessingQueue", value=jobs.queue_url)
