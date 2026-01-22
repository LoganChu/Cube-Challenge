"""
CardVault ML Service
Uses Google's Gemini AI for card detection and identification
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
import os
from pathlib import Path
from PIL import Image
from google import genai
from google.genai.types import HttpOptions
import re

app = FastAPI(title="CardVault ML Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required. Set it in your environment or docker-compose.yml")

client = genai.Client(
    http_options=HttpOptions(api_version="v1"),
    api_key=GEMINI_API_KEY
)

def extract_value(field_obj, default=None):
    """
    Extract the 'value' field from a confidence-annotated object.
    
    Args:
        field_obj: Either a dict with 'value' key, or a direct value
        default: Default value to return if extraction fails
    
    Returns:
        The extracted value or the default
    """
    if isinstance(field_obj, dict):
        return field_obj.get("value", default)
    elif field_obj is not None:
        # If it's already a plain value, return it
        return field_obj
    else:
        return default

def parse_card_response(gemini_response: str, scan_type: str) -> list:
    """
    Parse Gemini AI response to extract card information.
    Handles both structured format (with cardIdentity, physicalCondition, etc.) and simple format.
    """
    detected_cards = []
    
    try:
        # Try to extract JSON from the response
        # Look for JSON array or object pattern
        json_match = re.search(r'(\[.*\]|\{.*\})', gemini_response, re.DOTALL)
        if json_match:
            parsed_data = json.loads(json_match.group())
            
            # Both formats return an array, so check if it's a list first
            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                container = parsed_data[0]
                
                if scan_type == "single":
                    # Single card format: array with one object containing cardIdentity, physicalCondition, etc.
                    card_identity = container.get("cardIdentity", {})
                    physical_condition = container.get("physicalCondition", {})
                    interpretation = container.get("interpretation", {})
                    
                    name = extract_value(card_identity.get("name", {}), "Unknown Card")
                    set_code = extract_value(card_identity.get("set", {}), "")
                    card_number = extract_value(card_identity.get("cardNumber", {}), "")
                    year = extract_value(card_identity.get("year", {}), None)
                    domain = extract_value(card_identity.get("domain", {}), "other")
                    
                    centering = extract_value(physical_condition.get("centering", {}), 0.0)
                    corners = extract_value(physical_condition.get("corners", {}), 0.0)
                    surface = extract_value(physical_condition.get("surface", {}), 0.0)
                    estimated_grade = extract_value(interpretation.get("estimatedGrade", {}), 0.0)
                    
                    detected_cards.append({
                        "id": str(uuid.uuid4()),
                        "name": name if name else "Unknown Card",
                        "set_code": set_code if set_code else "",
                        "card_number": card_number,
                        "year": year,
                        "domain": domain,
                        "confidence": 0.8,  # Default confidence
                        "bounding_box": {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.8},
                        "condition": {
                            "centering": centering,
                            "corners": corners,
                            "surface": surface,
                            "estimated_grade": estimated_grade
                        }
                    })
                    
                else:  # scan_type == "multi"
                    # Multi-card format: array with object containing "cards" array
                    cards_array = container.get("cards", [])
                    
                    for i, card_obj in enumerate(cards_array):
                        card_identity = card_obj.get("cardIdentity", {})
                        bounding_box_data = card_obj.get("boundingBox", {})
                        physical_condition = card_obj.get("physicalCondition", {})
                        interpretation = card_obj.get("interpretation", {})
                        
                        name = extract_value(card_identity.get("name", {}), "Unknown Card")
                        set_code = extract_value(card_identity.get("set", {}), "")
                        card_number = extract_value(card_identity.get("cardNumber", {}), "")
                        year = extract_value(card_identity.get("year", {}), None)
                        domain = extract_value(card_identity.get("domain", {}), "other")
                        
                        # Extract bounding box
                        bbox_value = extract_value(bounding_box_data, [0.1 + (i * 0.3), 0.2, 0.25, 0.4])
                        if isinstance(bbox_value, list) and len(bbox_value) >= 4:
                            bbox = {"x": bbox_value[0], "y": bbox_value[1], "width": bbox_value[2], "height": bbox_value[3]}
                        else:
                            bbox = {"x": 0.1 + (i * 0.3), "y": 0.2, "width": 0.25, "height": 0.4}
                        
                        centering = extract_value(physical_condition.get("centering", {}), 0.0)
                        corners = extract_value(physical_condition.get("corners", {}), 0.0)
                        surface = extract_value(physical_condition.get("surface", {}), 0.0)
                        estimated_grade = extract_value(interpretation.get("estimatedGrade", {}), 0.0)
                        
                        detected_cards.append({
                            "id": str(uuid.uuid4()),
                            "name": name if name else "Unknown Card",
                            "set_code": set_code if set_code else "",
                            "card_number": card_number,
                            "year": year,
                            "domain": domain,
                            "confidence": 0.8,
                            "bounding_box": bbox,
                            "condition": {
                                "centering": centering,
                                "corners": corners,
                                "surface": surface,
                                "estimated_grade": estimated_grade
                            }
                        })
            else:
                # Fallback: try to extract card names from text
                # Look for patterns like "Card Name (SET_CODE)"
                card_pattern = r'([A-Za-z0-9\s,\'\-\.]+)\s*\(([A-Z0-9]+)\)'
                matches = re.findall(card_pattern, gemini_response)
                for i, (name, set_code) in enumerate(matches[:5]):  # Limit to 5 cards
                    detected_cards.append({
                        "id": str(uuid.uuid4()),
                        "name": name.strip(),
                        "set_code": set_code.strip(),
                        "confidence": 0.85 - (i * 0.05),
                        "bounding_box": {
                            "x": 0.1 + (i * 0.3) if scan_type == "multi" else 0.1,
                            "y": 0.2,
                            "width": 0.25 if scan_type == "multi" else 0.8,
                            "height": 0.4 if scan_type == "multi" else 0.8
                        },
                    })
        else:
            # No JSON found, create placeholder
            pass
            
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        print(f"Response was: {gemini_response}")
        import traceback
        print(traceback.format_exc())
    
    # If no cards detected, return at least one placeholder
    if not detected_cards:
        detected_cards.append({
            "id": str(uuid.uuid4()),
            "name": "Unknown Card",
            "set_code": "",
            "confidence": 0.5,
            "bounding_box": {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.8},
        })
    
    return detected_cards

@app.post("/predict")
async def predict(
    image: UploadFile = File(...),
    scan_type: str = Form("single")
):
    """
    Use Google Gemini AI to detect and identify trading cards in the image
    """
    
    # Save uploaded image
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / f"{uuid.uuid4()}_{image.filename}"
    with open(file_path, "wb") as f:
        content = await image.read()
        f.write(content)
    
    try:
        # Load image with PIL
        img = Image.open(file_path)
        
        # Create prompt based on scan type
        if scan_type == "single":
            prompt = """Analyze this image of a trading card. Identify the card and extract the following information in JSON format:
[
  {
  "imageMeta": {
    "filename": { "value": "STRING", "confidence": 1.0, "source": "detected" },
    "captureTimestamp": { "value": "ISO8601_STRING", "confidence": 1.0, "source": "detected" },
    "imageQuality": { "value": 0.0, "confidence": 1.0, "source": "detected" }
  },

  "cardIdentity": {
    "name": { "value": "STRING", "confidence": 0.0, "source": "detected|inferred" },
    "set": { "value": "STRING|null", "confidence": 0.0, "source": "detected|inferred" },
    "cardNumber": { "value": "STRING|null", "confidence": 0.0, "source": "detected|inferred" },
    "year": { "value": "INTEGER|null", "confidence": 0.0, "source": "detected|inferred" },
    "domain": { "value": "enum(pokemon,mtg,sports,yugioh,other)", "confidence": 0.0, "source": "detected|inferred" }
  },

  "physicalCondition": {
    "centering": { "value": 0.0, "confidence": 0.0, "source": "detected" },
    "corners": { "value": 0.0, "confidence": 0.0, "source": "detected" },
    "surface": { "value": 0.0, "confidence": 0.0, "source": "detected" }
  },

  "interpretation": {
    "estimatedGrade": { "value": 0.0, "scale": "1-10", "confidence": 0.0, "source": "computed" }
  },

  "meta": {
    "modelVersion": { "value": "STRING", "confidence": 1.0, "source": "system" },
    "processingTimestamp": { "value": "ISO8601_STRING", "confidence": 1.0, "source": "system" }
  }
}
]

If you cannot identify the card, return an empty array []. Only return valid JSON, no additional text."""
        else:
            prompt = """Analyze this image containing multiple trading cards. Identify all visible cards and extract the following information in JSON format:
[
  {
  "imageMeta": {
    "filename": { "value": "STRING", "confidence": 1.0, "source": "detected" },
    "captureTimestamp": { "value": "ISO8601_STRING", "confidence": 1.0, "source": "detected" },
    "imageQuality": { "value": 0.0, "confidence": 1.0, "source": "detected" }
  },

  "cards": [
    {
      "boundingBox": {
        "value": [x, y, width, height],
        "confidence": 0.0,
        "source": "detected"
      },

      "cardIdentity": {
        "name": { "value": "STRING", "confidence": 0.0, "source": "detected|inferred" },
        "set": { "value": "STRING|null", "confidence": 0.0, "source": "detected|inferred" },
        "cardNumber": { "value": "STRING|null", "confidence": 0.0, "source": "detected|inferred" },
        "year": { "value": "INTEGER|null", "confidence": 0.0, "source": "detected|inferred" },
        "domain": { "value": "enum(pokemon,mtg,sports,yugioh,other)", "confidence": 0.0, "source": "detected|inferred" }
      },
    }
  ], ...

  "meta": {
    "modelVersion": { "value": "STRING", "confidence": 1.0, "source": "system" },
    "processingTimestamp": { "value": "ISO8601_STRING", "confidence": 1.0, "source": "system" }
  }
}

  ...
]

For each card, provide approximate bounding box coordinates (0.0 to 1.0) indicating where the card appears in the image.
If you cannot identify any cards, return an empty array []. Only return valid JSON, no additional text."""
        
        # Call Gemini API using the new client API
        resp = client.models.generate_content(
            model="gemini-2.0-flash",  # or "gemini-1.5-pro" for better accuracy
            contents=[img, prompt]
        )
        
        # Parse response
        gemini_text = resp.text if hasattr(resp, 'text') else str(resp)
        detected_cards = parse_card_response(gemini_text, scan_type)

        print(gemini_text)
        
        return {
            "success": True,
            "detected_cards": detected_cards,
            "total_cards": len(detected_cards),
            "raw_response": gemini_text  # For debugging
        }
        
    except Exception as e:
        print(f"Error processing image with Gemini: {e}")
        # Fallback: return empty result
        return {
            "success": False,
            "detected_cards": [],
            "total_cards": 0,
            "error": str(e)
        }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ml-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
