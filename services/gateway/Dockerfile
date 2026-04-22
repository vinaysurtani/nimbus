FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod ./
COPY enhanced_main.go ./
RUN go mod tidy

RUN go build -o gateway enhanced_main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/gateway .

EXPOSE 8080

CMD ["./gateway"]