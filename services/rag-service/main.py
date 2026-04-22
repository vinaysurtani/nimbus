import os
import uuid
import json
import anthropic
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI()

COLLECTION = "nimbus_docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_DIM = 384  # BAAI/bge-small-en-v1.5

anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

qdrant = QdrantClient(host=os.environ.get("QDRANT_HOST", "qdrant"), port=6333)


def ensure_collection():
    existing = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION not in existing:
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def embed(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in embedder.embed(texts)]


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class IngestRequest(BaseModel):
    text: str


@app.on_event("startup")
def startup():
    ensure_collection()


@app.post("/ingest")
async def ingest(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    if file:
        raw = (await file.read()).decode("utf-8", errors="ignore")
    elif text:
        raw = text
    else:
        return JSONResponse(status_code=400, content={"error": "provide text or file"})

    chunks = chunk_text(raw)
    vectors = embed(chunks)

    points = [
        PointStruct(id=str(uuid.uuid4()), vector=vec, payload={"text": chunk})
        for chunk, vec in zip(chunks, vectors)
    ]
    qdrant.upsert(collection_name=COLLECTION, points=points)

    return {"chunks_stored": len(chunks), "collection": COLLECTION}


@app.post("/query")
def query(req: QueryRequest):
    q_vec = embed([req.question])[0]
    hits = qdrant.search(
        collection_name=COLLECTION,
        query_vector=q_vec,
        limit=req.top_k,
    )
    sources = [hit.payload["text"] for hit in hits]
    context = "\n\n".join(f"[{i+1}] {s}" for i, s in enumerate(sources))

    message = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                f"Answer the question using only the context below.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {req.question}"
            ),
        }],
    )

    return {
        "answer": message.content[0].text,
        "sources": sources,
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "rag-service"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
