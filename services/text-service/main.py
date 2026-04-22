import os
import re
from typing import List

import anthropic
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="Text Processing Service", version="2.0.0")
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

class TextRequest(BaseModel):
    text: str

class TextResponse(BaseModel):
    processed_text: str
    word_count: int
    char_count: int

class KeywordsResponse(BaseModel):
    keywords: List[str]


@app.post("/process", response_model=TextResponse)
async def process_text(request: TextRequest):
    text = request.text.strip()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                f"Clean and summarize the following text concisely. "
                f"Return only the improved text, no explanation:\n\n{text}"
            )
        }]
    )
    processed = message.content[0].text.strip()
    return TextResponse(
        processed_text=processed,
        word_count=len(processed.split()),
        char_count=len(processed)
    )


@app.post("/keywords", response_model=KeywordsResponse)
async def extract_keywords(request: TextRequest):
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": (
                f"Extract the 10 most important keywords from this text. "
                f"Return them as a comma-separated list, nothing else:\n\n{request.text}"
            )
        }]
    )
    raw = message.content[0].text.strip()
    keywords = [k.strip() for k in raw.split(",") if k.strip()][:10]
    return KeywordsResponse(keywords=keywords)


@app.post("/stream")
async def stream_text(request: TextRequest):
    def generate():
        with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": request.text}]
        ) as stream:
            for text_chunk in stream.text_stream:
                yield f"data: {text_chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
