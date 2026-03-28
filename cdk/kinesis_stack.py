import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_kinesis as kinesis,
    aws_kinesisfirehose as firehose,
    Duration,
)
from constructs import Construct

S3_BUCKET = "greatestbucketever"
S3_PREFIX = "coinbase/raw/!{timestamp:yyyy/MM/dd}/"
STREAM_NAME = "raw-trade-data"
FIREHOSE_NAME = "KDS-S3-trade-data"


class FirehoseTransformStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Lambda transform ---
        lambda_role = iam.Role(
            self,
            "FirehoseTransformRole",
            role_name="coinbase-firehose-transform-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "CloudWatchLogs": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=[
                                f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/coinbase-firehose-transform:*"
                            ],
                        )
                    ]
                )
            },
        )

        fn = lambda_.Function(
            self,
            "FirehoseTransformFunction",
            function_name="coinbase-firehose-transform",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("../lambda"),
            role=lambda_role,
            timeout=Duration.seconds(60),
            memory_size=128,
            description="Transforms raw Coinbase trade records for Firehose delivery to S3",
        )

        # --- Kinesis Data Stream ---
        stream = kinesis.Stream(
            self,
            "RawTradeDataStream",
            stream_name=STREAM_NAME,
            shard_count=1,
            retention_period=Duration.hours(24),
        )

        # --- IAM role for Firehose ---
        firehose_role = iam.Role(
            self,
            "FirehoseDeliveryRole",
            role_name="coinbase-firehose-delivery-role",
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
            inline_policies={
                "KinesisRead": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "kinesis:GetRecords",
                                "kinesis:GetShardIterator",
                                "kinesis:DescribeStream",
                                "kinesis:ListShards",
                            ],
                            resources=[stream.stream_arn],
                        )
                    ]
                ),
                "LambdaInvoke": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[fn.function_arn],
                        )
                    ]
                ),
                "S3Write": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:AbortMultipartUpload",
                                "s3:GetBucketLocation",
                                "s3:GetObject",
                                "s3:ListBucket",
                                "s3:ListBucketMultipartUploads",
                                "s3:PutObject",
                            ],
                            resources=[
                                f"arn:aws:s3:::{S3_BUCKET}",
                                f"arn:aws:s3:::{S3_BUCKET}/*",
                            ],
                        )
                    ]
                ),
                "CloudWatchLogs": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=[
                                f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/kinesisfirehose/{FIREHOSE_NAME}:*"
                            ],
                        )
                    ]
                ),
            },
        )

        # --- Kinesis Firehose delivery stream ---
        firehose.CfnDeliveryStream(
            self,
            "TradeDataFirehose",
            delivery_stream_name=FIREHOSE_NAME,
            delivery_stream_type="KinesisStreamAsSource",
            kinesis_stream_source_configuration=firehose.CfnDeliveryStream.KinesisStreamSourceConfigurationProperty(
                kinesis_stream_arn=stream.stream_arn,
                role_arn=firehose_role.role_arn,
            ),
            extended_s3_destination_configuration=firehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
                bucket_arn=f"arn:aws:s3:::{S3_BUCKET}",
                prefix=S3_PREFIX,
                error_output_prefix="coinbase/errors/type=!{firehose:error-output-type}/!{timestamp:yyyy/MM/dd}/",
                role_arn=firehose_role.role_arn,
                buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
                    interval_in_seconds=60,
                    size_in_m_bs=5,
                ),
                compression_format="UNCOMPRESSED",
                processing_configuration=firehose.CfnDeliveryStream.ProcessingConfigurationProperty(
                    enabled=True,
                    processors=[
                        firehose.CfnDeliveryStream.ProcessorProperty(
                            type="Lambda",
                            parameters=[
                                firehose.CfnDeliveryStream.ProcessorParameterProperty(
                                    parameter_name="LambdaArn",
                                    parameter_value=fn.function_arn,
                                ),
                                firehose.CfnDeliveryStream.ProcessorParameterProperty(
                                    parameter_name="BufferSizeInMBs",
                                    parameter_value="3",
                                ),
                                firehose.CfnDeliveryStream.ProcessorParameterProperty(
                                    parameter_name="BufferIntervalInSeconds",
                                    parameter_value="60",
                                ),
                            ],
                        )
                    ],
                ),
            ),
        )

        cdk.CfnOutput(self, "LambdaArn", value=fn.function_arn)
        cdk.CfnOutput(self, "KinesisStreamArn", value=stream.stream_arn)
        cdk.CfnOutput(self, "FirehoseName", value=FIREHOSE_NAME)
