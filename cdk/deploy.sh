#!/bin/bash

#AWS_REGION="us-east-1"
VPC_ID="vpc-013914d1062557cd7"
SUBNET_ID="subnet-0ac0bc58b5403af7b"

cdk deploy FirehoseTransformStack
cdk deploy EndpointsStack --context vpc_id=$VPC_ID --context subnet_id=$SUBNET_ID
