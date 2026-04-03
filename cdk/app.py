import aws_cdk as cdk

from kinesis_stack import FirehoseTransformStack
from endpoints_stack import EndpointsStack
from cdk.ecs_stack import EcsWebsocketStack

app = cdk.App()

env = cdk.Environment(account="391262527903", region="us-east-1")

FirehoseTransformStack(app, "CryptoTradeFirehose", env=env)
EndpointsStack(app, "CryptoTradeEndpoints", env=env)
EcsWebsocketStack(app, "EcsWebsocketStack", env=env)

app.synth()
