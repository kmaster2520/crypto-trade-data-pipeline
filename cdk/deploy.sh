#!/bin/bash

AWS_REGION="us-east-1"
VPC_ID="vpc-013914d1062557cd7"
SUBNET_ID="subnet-0ac0bc58b5403af7b"
cdk deploy CryptoTradeEndpoints --context vpc_id=$VPC_ID --context subnet_id=$SUBNET_ID

BUCKET_NAME="greatestbucketever"
cdk deploy CryptoTradeFirehose --context bucket_name=$BUCKET_NAME

ECR_IMAGE_URI="391262527903.dkr.ecr.us-east-1.amazonaws.com/coinbase-websocket:latest"
PRODUCT_ID="BTC-USD,ETH-USD"
cdk deploy CoinbaseECSCluster \
  --context subnet_id=$SUBNET_ID \
  --context vpc_id=VPC_ID \
  --context ecr_image_uri=$ECR_IMAGE_URI \
  --context product_id=$PRODUCT_ID
