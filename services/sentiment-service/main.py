import json
import os
from typing import List

import anthropic
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Sentiment Analysis Service", version="2.0.0")
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    sentiment: str
    confidence: float
    polarity: float
    subjectivity: float

class BatchSentimentRequest(BaseModel):
    texts: List[str]

class BatchSentimentResponse(BaseModel):
    results: List[SentimentResponse]


def analyze_sentiment(text: str) -> SentimentResponse:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": (
                f"Analyze the sentiment of this text and return a JSON object with exactly these fields:\n"
                f"- sentiment: one of 'positive', 'negative', or 'neutral'\n"
                f"- confidence: float 0.0-1.0 (how confident you are)\n"
                f"- polarity: float -1.0 to 1.0 (negative to positive)\n"
                f"- subjectivity: float 0.0-1.0 (objective to subjective)\n\n"
                f"Return only valid JSON, no explanation.\n\nText: {text}"
            )
        }]
    )
    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)
    return SentimentResponse(
        sentiment=data["sentiment"],
        confidence=round(float(data["confidence"]), 3),
        polarity=round(float(data["polarity"]), 3),
        subjectivity=round(float(data["subjectivity"]), 3)
    )


@app.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment_endpoint(request: SentimentRequest):
    return analyze_sentiment(request.text)


@app.post("/batch", response_model=BatchSentimentResponse)
async def batch_analyze(request: BatchSentimentRequest):
    results = [analyze_sentiment(text) for text in request.texts]
    return BatchSentimentResponse(results=results)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
