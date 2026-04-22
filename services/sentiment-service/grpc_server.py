import grpc
from concurrent import futures
import sentiment_service_pb2
import sentiment_service_pb2_grpc
from textblob import TextBlob

class SentimentAnalyzerServicer(sentiment_service_pb2_grpc.SentimentAnalyzerServicer):
    def analyze_sentiment(self, text: str):
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        if polarity > 0.1:
            sentiment = "positive"
            confidence = polarity
        elif polarity < -0.1:
            sentiment = "negative"
            confidence = abs(polarity)
        else:
            sentiment = "neutral"
            confidence = 1 - abs(polarity)
        
        return sentiment_service_pb2.SentimentResponse(
            sentiment=sentiment,
            confidence=round(confidence, 3),
            polarity=round(polarity, 3),
            subjectivity=round(subjectivity, 3)
        )
    
    def AnalyzeSentiment(self, request, context):
        return self.analyze_sentiment(request.text)
    
    def BatchAnalyze(self, request, context):
        results = [self.analyze_sentiment(text) for text in request.texts]
        return sentiment_service_pb2.BatchSentimentResponse(results=results)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    sentiment_service_pb2_grpc.add_SentimentAnalyzerServicer_to_server(
        SentimentAnalyzerServicer(), server
    )
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Sentiment gRPC server started on port 50052")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()