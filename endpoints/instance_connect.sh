#!/bin/bash

aws ec2-instance-connect ssh \
  --instance-id "$1" \
  --connection-type eice \
  --region us-east-1
