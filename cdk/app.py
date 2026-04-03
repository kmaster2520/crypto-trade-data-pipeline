import aws_cdk as cdk
import os

from kinesis_stack import FirehoseTransformStack
from endpoints_stack import EndpointsStack
from ecs_stack import EcsWebsocketStack

app = cdk.App()
aws_account = os.getenv("AWS_ACCOUNT", "391262527903")
aws_region = os.getenv("AWS_REGION", "us-east-1")
env = cdk.Environment(account=aws_account, region=aws_region)

#FirehoseTransformStack(app, "CryptoTradeFirehose", env=env)
#EndpointsStack(app, "CryptoTradeEndpoints", env=env)
EcsWebsocketStack(app, "CryptoWebsocketApp", env=env)

app.synth()
