docker rm ic-identity
docker rmi ic-identity
docker build --platform=linux/arm64/v8 --build-arg BUILD_FROM=ghcr.io/home-assistant/aarch64-base-python:3.12-alpine3.20 -t ic-identity .
docker run -d --name ic-identity -p 8099:8099 ic-identity
sleep 3
docker logs ic-identity