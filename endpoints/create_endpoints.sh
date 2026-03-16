#!/bin/bash

VPC_ID="vpc-013914d1062557cd7"
AWS_REGION="us-east-1"

aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-support '{"Value": true}' \
  --region $AWS_REGION

aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-hostnames '{"Value": true}' \
  --region $AWS_REGION

aws ec2 create-vpc-endpoint \
  --region $AWS_REGION \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.${AWS_REGION}.kinesis-streams \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-0ac0bc58b5403af7b \
  --private-dns-enabled \
  --security-group-ids sg-04b8c982d429175eb \
  --ip-address-type ipv4 \
  --client-token my-kinesis-endpoint-creation

aws ec2 create-vpc-endpoint \
  --region $AWS_REGION \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.us-east-1.s3 \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-063cda800cb87198a \
