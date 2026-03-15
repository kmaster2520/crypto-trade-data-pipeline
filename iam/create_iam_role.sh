#!/bin/bash

aws cloudformation create-stack \
  --stack-name BinanceIAMRoles \
  --template-body file://websocket_instance_role.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
      ParameterKey=BucketName,ParameterValue=greatestbucketever \
      ParameterKey=KinesisStreamArn,ParameterValue="arn:aws:kinesis:us-east-1:391262527903:stream/raw-trade-data"
