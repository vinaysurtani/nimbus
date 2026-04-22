FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download TextBlob corpora
RUN python -m textblob.download_corpora

COPY . .

RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. sentiment_service.proto

EXPOSE 8002 50052

CMD ["python", "main.py"]