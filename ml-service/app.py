"""
CardVault ML Service
Mock ML service for MVP (can be replaced with actual models)
"""
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
from typing import List
import os
from pathlib import Path

app = FastAPI(title="CardVault ML Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock card database (in production, use actual model)
MOCK_CARDS = {
    "lightning bolt": {"name": "Lightning Bolt", "set_code": "M21", "confidence": 0.95},
    "counterspell": {"name": "Counterspell", "set_code": "M21", "confidence": 0.92},
    "oko": {"name": "Oko, Thief of Crowns", "set_code": "ELD", "confidence": 0.90},
}

@app.post("/predict")
async def predict(
    image: UploadFile = File(...),
    scan_type: str = Form("single")
):
    """
    Mock ML prediction endpoint
    In production, this would use actual YOLOv8 + EfficientNet models
    """
    
    # Save uploaded image
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / f"{uuid.uuid4()}_{image.filename}"
    with open(file_path, "wb") as f:
        content = await image.read()
        f.write(content)
    
    # Mock detection (in production, use YOLOv8)
    detected_cards = []
    
    if scan_type == "single":
        # Mock single card detection
        card = MOCK_CARDS.get("lightning bolt")  # Default mock
        detected_cards.append({
            "id": str(uuid.uuid4()),
            "name": card["name"],
            "set_code": card["set_code"],
            "confidence": card["confidence"],
            "bounding_box": {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.8},
            "crop_image_url": str(file_path)
        })
    else:
        # Mock multi-card detection (2-3 cards)
        cards_to_detect = ["lightning bolt", "counterspell", "oko"][:3]
        for i, card_key in enumerate(cards_to_detect):
            card = MOCK_CARDS.get(card_key, MOCK_CARDS["lightning bolt"])
            detected_cards.append({
                "id": str(uuid.uuid4()),
                "name": card["name"],
                "set_code": card["set_code"],
                "confidence": card["confidence"] - (i * 0.02),
                "bounding_box": {
                    "x": 0.1 + (i * 0.3),
                    "y": 0.2,
                    "width": 0.25,
                    "height": 0.4
                },
                "crop_image_url": str(file_path)
            })
    
    return {
        "success": True,
        "detected_cards": detected_cards,
        "total_cards": len(detected_cards)
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ml-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
