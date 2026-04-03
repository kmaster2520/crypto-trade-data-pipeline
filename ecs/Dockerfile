# Build context must be the repo root:
#   docker build -f ecs/Dockerfile -t coinbase-websocket .
#   or
#   docker buildx build --platform linux/arm64,linux/amd64 -f ecs/Dockerfile -t coinbase-websocket . --load
#
# Push to ECR:
#   aws login
#   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 391262527903.dkr.ecr.us-east-1.amazonaws.com
#   docker build -f ecs/Dockerfile -t coinbase-websocket .
#   docker tag coinbase-websocket 391262527903.dkr.ecr.us-east-1.amazonaws.com/coinbase-websocket:latest
#   docker push 391262527903.dkr.ecr.us-east-1.amazonaws.com/coinbase-websocket:latest

FROM python:3.12-slim-bookworm

WORKDIR /app

RUN pip install --no-cache-dir boto3==1.42.67 websockets==16.0

COPY ecs/websocket_script_coinbase_v2.py .

# CoinbaseProductId is passed as CMD arg (e.g. "BTC-USD,ETH-USD") from the ECS task definition
ENTRYPOINT ["python", "websocket_script_coinbase_v2.py"]
