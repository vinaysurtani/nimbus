import base64
import io
import os
from typing import Optional

import anthropic
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, ImageEnhance, ImageFilter
from pydantic import BaseModel

app = FastAPI(title="Image Processing Service", version="2.0.0")
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

class ImageInfoResponse(BaseModel):
    format: str
    width: int
    height: int
    mode: str
    size_bytes: int

class CaptionResponse(BaseModel):
    caption: str

class AnalysisResponse(BaseModel):
    description: str
    objects: list[str]
    colors: list[str]
    mood: str


def process_image(image_data: bytes, operation: str = "resize") -> bytes:
    image = Image.open(io.BytesIO(image_data))
    if operation == "resize":
        image = image.resize((800, 600))
    elif operation == "blur":
        image = image.filter(ImageFilter.BLUR)
    elif operation == "sharpen":
        image = image.filter(ImageFilter.SHARPEN)
    elif operation == "enhance":
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.2)
    output = io.BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


def image_to_base64(image_data: bytes) -> tuple[str, str]:
    image = Image.open(io.BytesIO(image_data))
    # Resize large images before sending to API to save tokens
    if image.width > 1568 or image.height > 1568:
        image.thumbnail((1568, 1568))
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
    return b64, "image/jpeg"


@app.post("/upload")
async def upload_image(file: UploadFile = File(...), operation: Optional[str] = "resize"):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    image_data = await file.read()
    processed_data = process_image(image_data, operation)
    return {
        "message": "Image processed successfully",
        "original_size": len(image_data),
        "processed_size": len(processed_data),
        "operation": operation
    }


@app.post("/info", response_model=ImageInfoResponse)
async def get_image_info(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    return ImageInfoResponse(
        format=image.format or "Unknown",
        width=image.width,
        height=image.height,
        mode=image.mode,
        size_bytes=len(image_data)
    )


@app.post("/caption", response_model=CaptionResponse)
async def caption_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    image_data = await file.read()
    b64, media_type = image_to_base64(image_data)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": "Write a single concise caption for this image (one sentence)."}
            ]
        }]
    )
    return CaptionResponse(caption=message.content[0].text.strip())


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    image_data = await file.read()
    b64, media_type = image_to_base64(image_data)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {
                    "type": "text",
                    "text": (
                        "Analyze this image and return a JSON object with:\n"
                        "- description: detailed scene description (2-3 sentences)\n"
                        "- objects: list of main objects visible\n"
                        "- colors: list of dominant colors\n"
                        "- mood: overall mood/atmosphere in one word\n"
                        "Return only valid JSON."
                    )
                }
            ]
        }]
    )
    import json
    raw = message.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)
    return AnalysisResponse(
        description=data["description"],
        objects=data["objects"],
        colors=data["colors"],
        mood=data["mood"]
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
