# Build context must be the repo root:
#   docker build -f ecs/Dockerfile -t coinbase-websocket .
#   or
#   docker buildx build --platform linux/arm64,linux/amd64 -f ecs/Dockerfile -t coinbase-websocket . --load
#
# Push to ECR:
#   aws login
#   aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com
#   docker build -f ecs/Dockerfile -t coinbase-websocket .
#   ECR_IMAGE_NAME="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/coinbase-websocket:$(date +%Y%m%d)"
#   ECR_IMAGE_NAME_LATEST="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/coinbase-websocket:latest"
#   docker tag coinbase-websocket $ECR_IMAGE_NAME
#   docker push $ECR_IMAGE_NAME
#   docker tag $ECR_IMAGE_NAME $ECR_IMAGE_NAME_LATEST
#   docker push $ECR_IMAGE_NAME_LATEST

FROM golang:1.22-bookworm AS builder

WORKDIR /build

COPY ecs/go.mod ecs/go.sum ./
RUN go mod download

COPY ecs/main.go .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o websocket_app .

FROM scratch

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=builder /build/websocket_app /websocket_app

# CoinbaseProductId is passed as CMD arg (e.g. "BTC-USD,ETH-USD") from the ECS task definition
ENTRYPOINT ["/websocket_app"]
