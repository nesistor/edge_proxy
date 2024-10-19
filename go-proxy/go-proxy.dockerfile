FROM alpine:latest

RUN mkdir /app

COPY proxyApp /app

CMD [ "/app/proxyApp"]