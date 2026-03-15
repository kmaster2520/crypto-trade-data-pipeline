#!/bin/bash

SUBNET_ID="subnet-0ac0bc58b5403af7b"

aws cloudformation create-stack \
  --stack-name BinanceWebsocketInstance \
  --template-body file://websocket_instance_cft.yaml \
  --parameters \
      ParameterKey=AmiId,ParameterValue=ami-04aa82396fe417f2f \
      ParameterKey=SubnetId,ParameterValue=$SUBNET_ID \
      ParameterKey=SecurityGroupId,ParameterValue=sg-06f51ddc0f1cb5760 \
      ParameterKey=IamInstanceProfile,ParameterValue=btc-binance-instance-role \
      ParameterKey=InstanceType,ParameterValue=t4g.nano \
      ParameterKey=KeyName,ParameterValue=BinanceDataFlowKP
