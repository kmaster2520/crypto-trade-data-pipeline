#!/bin/bash

AWS_REGION="us-east-1"
AWS_ACCOUNT="391262527903"
VPC_ID="vpc-013914d1062557cd7"
SUBNET_ID="subnet-0ac0bc58b5403af7b"
BUCKET_NAME="greatestbucketever"
ECR_IMAGE_URI="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/coinbase-websocket:latest"
PRODUCT_ID="BTC-USD,ETH-USD"

cdk deploy CryptoTradeEndpoints --context vpc_id=$VPC_ID --context subnet_id=$SUBNET_ID

cdk synth CryptoTradeFirehose --context bucket_name=$BUCKET_NAME
cdk deploy CryptoTradeFirehose --context bucket_name=$BUCKET_NAME

cdk synth CryptoWebsocketApp \
  --context subnet_id=$SUBNET_ID \
  --context vpc_id=$VPC_ID \
  --context ecr_image_uri=$ECR_IMAGE_URI \
  --context product_id=$PRODUCT_ID

cdk deploy CryptoWebsocketApp \
  --context subnet_id=$SUBNET_ID \
  --context vpc_id=$VPC_ID \
  --context ecr_image_uri=$ECR_IMAGE_URI \
  --context product_id=$PRODUCT_ID
