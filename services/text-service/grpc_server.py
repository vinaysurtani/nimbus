import grpc
from concurrent import futures
import text_service_pb2
import text_service_pb2_grpc
import re

class TextProcessorServicer(text_service_pb2_grpc.TextProcessorServicer):
    def ProcessText(self, request, context):
        text = request.text.strip()
        word_count = len(text.split())
        char_count = len(text)
        processed_text = re.sub(r'\s+', ' ', text)
        
        return text_service_pb2.TextResponse(
            processed_text=processed_text,
            word_count=word_count,
            char_count=char_count
        )
    
    def ExtractKeywords(self, request, context):
        words = re.findall(r'\b\w{4,}\b', request.text.lower())
        keywords = list(set(words))[:10]
        
        return text_service_pb2.KeywordsResponse(keywords=keywords)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    text_service_pb2_grpc.add_TextProcessorServicer_to_server(
        TextProcessorServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()