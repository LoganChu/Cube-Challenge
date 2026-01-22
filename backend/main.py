"""
CardVault Backend API Server
FastAPI-based REST API for MVP
"""
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import jwt
import bcrypt
import uuid
import os
import json
import re
from pathlib import Path
import httpx

app = FastAPI(title="CardVault API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cardvault.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

# ML Service URL
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://cube-challenge-ml-service-1:8001")


class Scan(Base):
    __tablename__ = "scans"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    image_url = Column(String)
    scan_type = Column(String)  # "single" or "multi"
    status = Column(String, default="pending")  # "pending", "processing", "completed", "failed"
    results = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    inventory_public = Column(Boolean, default=False)
    marketplace_enabled = Column(Boolean, default=False)
    notification_in_app = Column(Boolean, default=True)
    # Location fields
    city = Column(String, nullable=True)
    state_province = Column(String, nullable=True)
    country = Column(String, nullable=True)
    # Subscription
    subscription_tier = Column(String, default="free")  # "free", "pro", "premium"
    
    inventory = relationship("InventoryEntry", back_populates="user")

# Image processing
def crop_card_image(original_image_path: str, bounding_box: dict, card_id: str) -> Optional[str]:
    """
    Crop a card from the original scan image based on bounding box coordinates.
    Bounding box is in normalized coordinates (0.0 to 1.0).
    Returns the path to the cropped image, or None if cropping fails.
    """
    try:
        from PIL import Image
        # Open the original image
        img = Image.open(original_image_path)
        img_width, img_height = img.size
        
        # Extract bounding box coordinates (normalized 0.0-1.0)
        x = bounding_box.get("x", 0.1)
        y = bounding_box.get("y", 0.1)
        width = bounding_box.get("width", 0.8)
        height = bounding_box.get("height", 0.8)
        
        # Convert to pixel coordinates
        left = int(x * img_width)
        top = int(y * img_height)
        right = int((x + width) * img_width)
        bottom = int((y + height) * img_height)
        
        # Ensure coordinates are within image bounds
        left = max(0, min(left, img_width))
        top = max(0, min(top, img_height))
        right = max(left, min(right, img_width))
        bottom = max(top, min(bottom, img_height))
        
        # Crop the image
        cropped_img = img.crop((left, top, right, bottom))
        if cropped_img.mode in ("RGBA", "LA", "P"):
            cropped_img = cropped_img.convert("RGB")
        
        # Create cropped images directory
        cropped_dir = Path("uploads/cropped")
        cropped_dir.mkdir(parents=True, exist_ok=True)
        
        # Save cropped image
        cropped_path = cropped_dir / f"{card_id}.jpg"
        cropped_img.save(cropped_path, "JPEG", quality=95)
        
        return str(cropped_path)
    except Exception as e:
        print(f"Error cropping image: {e}")
        return None


def attach_cropped_images_to_detected_cards(
    detected_cards: list,
    scan_image_path: Optional[str]
) -> list:
    if not scan_image_path:
        return detected_cards

    for card in detected_cards:
        if card.get("crop_image_url"):
            continue
        bounding_box = card.get("bounding_box")
        if not bounding_box:
            continue
        card_id = card.get("id") or str(uuid.uuid4())
        if not card.get("id"):
            card["id"] = card_id
        cropped_path = crop_card_image(scan_image_path, bounding_box, card_id)
        if cropped_path:
            card["crop_image_url"] = cropped_path

    return detected_cards

def save_detected_cards_to_inventory(
    detected_cards: list,
    scan: Scan,
    current_user: User,
    db: Session
) -> tuple[int, list]:
    """
    Helper function to save detected cards to inventory.
    Returns (saved_count, inventory_entries)
    """
    # Check subscription limits
    tier_info = SUBSCRIPTION_TIERS.get(current_user.subscription_tier, SUBSCRIPTION_TIERS["free"])
    current_card_count = db.query(InventoryEntry).filter(InventoryEntry.user_id == current_user.id).count()
    
    saved_count = 0
    inventory_entries = []
    
    for card_data in detected_cards:
        # Check limit before each save
        if current_card_count + saved_count >= tier_info["max_cards"]:
            print(f"Card limit reached. Stopping at {saved_count} cards saved.")
            break
        
        # Extract card name and set code
        card_name = card_data.get("name", "")
        set_code = card_data.get("set_code", "")
        
        # Extract condition information if available
        condition = "Near Mint"  # Default
        condition_grade = None
        condition_details = {}
        
        if "condition" in card_data and isinstance(card_data["condition"], dict):
            # Try to determine condition from condition metrics
            estimated_grade = card_data["condition"].get("estimated_grade", 0.0)
            condition_details = {
                "centering": card_data["condition"].get("centering", 0.0),
                "corners": card_data["condition"].get("corners", 0.0),
                "surface": card_data["condition"].get("surface", 0.0),
                "estimated_grade": estimated_grade
            }
            if estimated_grade >= 9.0:
                condition = "Near Mint"
            elif estimated_grade >= 7.0:
                condition = "Lightly Played"
            elif estimated_grade >= 5.0:
                condition = "Moderately Played"
            elif estimated_grade >= 3.0:
                condition = "Heavily Played"
            else:
                condition = "Damaged"
            condition_grade = float(estimated_grade) if estimated_grade else None
        
        # Create entry first to get ID for image filename
        entry = InventoryEntry(
            user_id=current_user.id,
            card_name=card_name,
            set_code=set_code,
            quantity=1,
            condition=condition,
            condition_grade=condition_grade,
            current_value=0.0,  # Default, will be updated later
            scan_image_url=scan.image_url,
            card_image_url=None,  # Will be set after cropping
            metadata_json=None  # Will be set after creating entry
        )
        db.add(entry)
        db.flush()  # Flush to get the entry ID
        
        # Crop card image from original scan using entry ID
        card_image_url = None
        bounding_box = card_data.get("bounding_box", {})
        if scan.image_url and bounding_box:
            cropped_path = crop_card_image(scan.image_url, bounding_box, entry.id)
            if cropped_path:
                card_image_url = cropped_path
                entry.card_image_url = card_image_url
        
        # Store additional metadata
        metadata_json = {
            "card_number": card_data.get("card_number"),
            "year": card_data.get("year"),
            "domain": card_data.get("domain", "other"),
            "confidence": card_data.get("confidence", 0.8),
            "condition_details": condition_details
        }
        entry.metadata_json = json.dumps(metadata_json)
        
        inventory_entries.append(entry)
        saved_count += 1
    
    db.commit()
    return saved_count, inventory_entries


def parse_multi_cards_from_raw_response(raw_response: str) -> list:
    if not raw_response:
        return []

    try:
        json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
        if not json_match:
            return []

        parsed_data = json.loads(json_match.group(1))
        if isinstance(parsed_data, list):
            container = parsed_data[0] if parsed_data else {}
        elif isinstance(parsed_data, dict):
            container = parsed_data
        else:
            return []

        cards_array = container.get("cards", [])
        detected_cards = []
        for index, card_obj in enumerate(cards_array):
            card_identity = card_obj.get("cardIdentity", {})
            bounding_box_data = card_obj.get("boundingBox", {})

            name = (card_identity.get("name") or {}).get("value") or "Unknown Card"
            set_code = (card_identity.get("set") or {}).get("value") or ""
            card_number = (card_identity.get("cardNumber") or {}).get("value")
            year = (card_identity.get("year") or {}).get("value")
            domain = (card_identity.get("domain") or {}).get("value") or "other"

            bbox_value = bounding_box_data.get("value") or [0.1 + (index * 0.3), 0.2, 0.25, 0.4]
            if isinstance(bbox_value, list) and len(bbox_value) >= 4:
                bbox = {
                    "x": bbox_value[0],
                    "y": bbox_value[1],
                    "width": bbox_value[2],
                    "height": bbox_value[3]
                }
            else:
                bbox = {"x": 0.1 + (index * 0.3), "y": 0.2, "width": 0.25, "height": 0.4}

            detected_cards.append({
                "id": str(uuid.uuid4()),
                "name": name,
                "set_code": set_code,
                "card_number": card_number,
                "year": year,
                "domain": domain,
                "confidence": 0.8,
                "bounding_box": bbox
            })

        return detected_cards
    except Exception as error:
        print(f"Error parsing raw_response for multi cards: {error}")
        return []



# Subscription tier limits
SUBSCRIPTION_TIERS = {
    "free": {
        "name": "Free",
        "max_cards": 100,
        "max_trend_insights": 3,
        "price": 0,
        "price_period": "month"
    },
    "pro": {
        "name": "Pro",
        "max_cards": 1000,
        "max_trend_insights": 20,
        "price": 9.99,
        "price_period": "month"
    },
    "premium": {
        "name": "Premium",
        "max_cards": 10000,
        "max_trend_insights": 100,
        "price": 19.99,
        "price_period": "month"
    }
}

class InventoryEntry(Base):
    __tablename__ = "inventory_entries"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    card_name = Column(String)
    set_code = Column(String)
    quantity = Column(Integer, default=1)
    condition = Column(String)
    condition_grade = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    scan_image_url = Column(String, nullable=True)
    card_image_url = Column(String, nullable=True)  # Cropped card image
    metadata_json = Column(Text, nullable=True)  # JSON string for additional card data
    scanned_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="inventory")


# Marketplace Wants
class Want(Base):
    __tablename__ = "wants"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    card_name = Column(String, index=True)
    set_code = Column(String, index=True, nullable=True)
    min_condition = Column(String, nullable=True)
    max_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Notifications
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    type = Column(String)  # "marketplace_match" | "trend"
    title = Column(String)
    message = Column(Text)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

def _ensure_sqlite_columns():
    """
    MVP convenience: if you're using an existing sqlite db, add newly introduced columns.
    This avoids forcing a full migration framework for a 1-day MVP.
    """
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        return
    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in cur.fetchall()}
        if "notification_in_app" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN notification_in_app BOOLEAN DEFAULT 1")
        if "city" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN city VARCHAR")
        if "state_province" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN state_province VARCHAR")
        if "country" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN country VARCHAR")
        if "subscription_tier" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN subscription_tier VARCHAR DEFAULT 'free'")
        
        # Check inventory_entries columns
        cur.execute("PRAGMA table_info(inventory_entries)")
        inv_cols = {row[1] for row in cur.fetchall()}
        if "card_image_url" not in inv_cols:
            cur.execute("ALTER TABLE inventory_entries ADD COLUMN card_image_url VARCHAR")
        if "metadata_json" not in inv_cols:
            cur.execute("ALTER TABLE inventory_entries ADD COLUMN metadata_json TEXT")
        
        conn.commit()
    finally:
        conn.close()

_ensure_sqlite_columns()

# Mount static files for serving images
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Pydantic Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    username: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: dict

class Card(BaseModel):
    id: str
    name: str
    set_code: str
    confidence: float
    bounding_box: Optional[dict] = None

class ScanResponse(BaseModel):
    scan_id: str
    status: str
    image_url: str
    detected_cards: Optional[List[Card]] = None

class InventoryEntryResponse(BaseModel):
    id: str
    card_name: str
    set_code: str
    quantity: int
    condition: str
    current_value: Optional[float]
    scanned_at: str

class WantCreate(BaseModel):
    card_name: str
    set_code: Optional[str] = None
    min_condition: Optional[str] = None
    max_price: Optional[float] = None

class SettingsUpdate(BaseModel):
    inventory_public: Optional[bool] = None
    marketplace_enabled: Optional[bool] = None
    notification_in_app: Optional[bool] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: Optional[str] = None

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Auth Endpoints
@app.post("/api/v1/auth/register", response_model=dict)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(User).filter((User.email == user_data.email) | (User.username == user_data.username)).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")
    
    # Hash password
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), salt).decode('utf-8')
    
    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=password_hash
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"success": True, "data": {"user": {"id": user.id, "email": user.email, "username": user.username}}}

@app.post("/api/v1/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not bcrypt.checkpw(user_data.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate tokens
    access_token = jwt.encode(
        {"sub": user.id, "exp": datetime.utcnow() + timedelta(minutes=15)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    refresh_token = jwt.encode(
        {"sub": user.id, "exp": datetime.utcnow() + timedelta(days=7)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 900,
            "user": {"id": user.id, "email": user.email, "username": user.username}
        }
    }

@app.post("/api/v1/scans/upload")
async def upload_scan(
    image: UploadFile = File(...),
    scan_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print(f"=== SCAN UPLOAD STARTED ===")
    print(f"User: {current_user.username} ({current_user.id})")
    print(f"Scan type: {scan_type}")
    print(f"Image filename: {image.filename}")
    print(f"Image content type: {image.content_type}")
    
    # Save uploaded file
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / f"{uuid.uuid4()}_{image.filename}"
    print(f"Saving image to: {file_path}")
    
    with open(file_path, "wb") as f:
        content = await image.read()
        f.write(content)
    
    print(f"Image saved successfully. File size: {len(content)} bytes")
    
    # Create scan record
    scan = Scan(
        user_id=current_user.id,
        image_url=str(file_path),
        scan_type=scan_type,
        status="processing"
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    print(f"Scan record created with ID: {scan.id}")
    
    # Call ML service (async)
    try:
        print(f"Calling ML service at: {ML_SERVICE_URL}/predict")
        
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {"image": (image.filename, f, image.content_type)}
                
                print(f"Sending request to ML service...")
                response = await client.post(
                    f"{ML_SERVICE_URL}/predict",
                    files=files,
                    data={"scan_type": scan_type},
                    timeout=60.0
                )
                
                print(f"ML service response status: {response.status_code}")
                print(f"ML service response headers: {response.headers}")
                
                if response.status_code == 200:
                    results = response.json()
                    print(f"ML service results: {results}")
                    detected_cards = results.get("detected_cards", [])

                    if scan_type == "multi":
                        raw_response = results.get("raw_response")
                        parsed_cards = parse_multi_cards_from_raw_response(raw_response)
                        if parsed_cards:
                            detected_cards = parsed_cards
                            results["detected_cards"] = parsed_cards
                            results["total_cards"] = len(parsed_cards)

                    detected_cards = attach_cropped_images_to_detected_cards(
                        detected_cards,
                        scan.image_url
                    )
                    results["detected_cards"] = detected_cards
                    results["total_cards"] = len(detected_cards)

                    print(f"Detected cards count: {len(detected_cards)}")
                    
                    # Store results as JSON
                    scan.results = json.dumps(results)
                    scan.status = "completed"
                    print(f"Scan marked as completed")
                    
                    # Automatically save all detected cards to inventory
                    if detected_cards:
                        print(f"=== Auto-saving {len(detected_cards)} detected cards to inventory ===")
                        try:
                            saved_count, inventory_entries = save_detected_cards_to_inventory(
                                detected_cards, scan, current_user, db
                            )
                            print(f"Successfully saved {saved_count} card(s) to inventory")
                            for entry in inventory_entries:
                                print(f"  - {entry.card_name} ({entry.set_code})")
                        except Exception as e:
                            print(f"Error auto-saving cards to inventory: {e}")
                            import traceback
                            print(traceback.format_exc())
                            # Don't fail the scan if auto-save fails
                else:
                    print(f"ML service returned non-200 status: {response.status_code}")
                    print(f"Response body: {response.text}")
                    scan.status = "failed"
                    scan.results = f"ML service error: {response.status_code} - {response.text}"
                    
    except httpx.ConnectError as e:
        print(f"!!! CONNECTION ERROR to ML service !!!")
        print(f"Error: {e}")
        print(f"ML_SERVICE_URL is set to: {ML_SERVICE_URL}")
        print(f"Make sure ML service container is running and accessible")
        scan.status = "failed"
        scan.results = f"Connection error: {str(e)}"
        
    except httpx.TimeoutException as e:
        print(f"!!! TIMEOUT ERROR from ML service !!!")
        print(f"Error: {e}")
        scan.status = "failed"
        scan.results = f"Timeout error: {str(e)}"
        
    except Exception as e:
        print(f"!!! UNEXPECTED ERROR !!!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        scan.status = "failed"
        scan.results = str(e)
    
    db.commit()
    
    print(f"=== SCAN UPLOAD FINISHED ===")
    print(f"Final status: {scan.status}")
    print(f"Scan ID: {scan.id}")
    print()
    
    return {
        "success": True,
        "data": {
            "scan_id": scan.id,
            "status": scan.status,
            "image_url": scan.image_url,
            "estimated_processing_time_seconds": 5
        }
    }

@app.get("/api/v1/scans/{scan_id}")
async def get_scan(scan_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == current_user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    detected_cards = []
    if scan.results:
        import json
        try:
            results = json.loads(scan.results)
            detected_cards = results.get("detected_cards", [])
        except:
            pass
    
    return {
        "success": True,
        "data": {
            "scan_id": scan.id,
            "status": scan.status,
            "scan_type": scan.scan_type,
            "image_url": scan.image_url,
            "detected_cards": detected_cards,
            "processed_at": scan.created_at.isoformat() if scan.status == "completed" else None
        }
    }

# Inventory Endpoints
@app.get("/api/v1/inventory")
async def get_inventory(
    page: int = 1,
    limit: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(InventoryEntry).filter(InventoryEntry.user_id == current_user.id)
    
    if search:
        query = query.filter(
            (InventoryEntry.card_name.contains(search)) |
            (InventoryEntry.set_code.contains(search))
        )
    
    if sort_by == "value":
        if sort_order == "asc":
            query = query.order_by(InventoryEntry.current_value.asc().nullslast())
        else:
            query = query.order_by(InventoryEntry.current_value.desc().nullslast())
    else:
        query = query.order_by(InventoryEntry.scanned_at.desc())

    total = query.count()
    if limit is None or limit <= 0:
        items = query.all()
        limit_value = total
        total_pages = 1 if total else 0
    else:
        items = query.offset((page - 1) * limit).limit(limit).all()
        limit_value = limit
        total_pages = (total + limit - 1) // limit
    
    # Parse metadata for each item
    items_data = []
    for item in items:
        metadata = {}
        if item.metadata:
            try:
                metadata = json.loads(item.metadata)
            except:
                pass
        
        # Use cropped card image if available, otherwise fall back to scan image
        image_url = item.card_image_url or item.scan_image_url or ""
        # Convert relative path to URL path
        if image_url and not image_url.startswith("http"):
            try:
                uploads_path = Path("uploads").resolve()
                image_path = Path(image_url).resolve()
                # Check if the image path is within uploads directory
                if str(image_path).startswith(str(uploads_path)):
                    rel_path = str(image_path.relative_to(uploads_path))
                    # Convert Windows path separators to forward slashes
                    rel_path = rel_path.replace("\\", "/")
                    image_url = f"/uploads/{rel_path}"
                else:
                    # Just use the filename if path is not relative to uploads
                    image_url = f"/uploads/{Path(image_url).name}" if Path(image_url).name else image_url
            except Exception:
                # Fallback: use filename
                image_url = f"/uploads/{Path(image_url).name}" if Path(image_url).name else image_url
        
        items_data.append({
            "id": item.id,
            "card": {
                "id": item.id,
                "name": item.card_name,
                "set": {
                    "id": item.set_code or "unknown",
                    "name": item.set_code or "Unknown Set",
                    "code": item.set_code or ""
                },
                "image_url": image_url
            },
            "quantity": item.quantity,
            "condition": item.condition,
            "condition_grade": item.condition_grade,
            "current_value": {
                "amount": item.current_value or 0,
                "currency": "USD",
                "confidence": "medium"  # Default confidence level
            } if item.current_value else None,
            "scanned_at": item.scanned_at.isoformat(),
            "metadata_json": item.metadata_json  # Include parsed metadata
        })
    
    return {
        "success": True,
        "data": {
            "items": items_data,
            "pagination": {
                "page": page,
                "limit": limit_value,
                "total": total,
                "total_pages": total_pages
            }
        }
    }

@app.delete("/api/v1/inventory/{entry_id}")
async def delete_inventory_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = db.query(InventoryEntry).filter(
        InventoryEntry.id == entry_id,
        InventoryEntry.user_id == current_user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Inventory entry not found")

    db.delete(entry)
    db.commit()
    return {"success": True}

@app.post("/api/v1/scans/{scan_id}/save")
async def save_scan_to_inventory(
    scan_id: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card_ids = payload.get("card_ids", [])
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == current_user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if not scan.results:
        raise HTTPException(status_code=400, detail="Scan not completed")
    
    # Check subscription limits
    tier_info = SUBSCRIPTION_TIERS.get(current_user.subscription_tier, SUBSCRIPTION_TIERS["free"])
    current_card_count = db.query(InventoryEntry).filter(InventoryEntry.user_id == current_user.id).count()
    
    if current_card_count + len(card_ids) > tier_info["max_cards"]:
        raise HTTPException(
            status_code=403,
            detail=f"Card limit reached. Your {tier_info['name']} plan allows {tier_info['max_cards']} cards. You currently have {current_card_count} cards. Please upgrade to add more."
        )
    
    results = json.loads(scan.results)
    detected_cards = results.get("detected_cards", [])
    
    # Use the helper function to save cards
    saved_count, inventory_entries = save_detected_cards_to_inventory(
        [card for card in detected_cards if card.get("id") in card_ids],
        scan,
        current_user,
        db
    )
    
    db.commit()
    
    return {
        "success": True,
        "data": {
            "saved_count": saved_count,
            "inventory_entries": [{"id": e.id, "card_name": e.card_name} for e in inventory_entries],
            "card_limit": tier_info["max_cards"],
            "current_count": current_card_count + saved_count
        }
    }

# Marketplace (Wants -> Matches)
@app.get("/api/v1/marketplace/wants")
async def list_wants(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wants = db.query(Want).filter(Want.user_id == current_user.id).order_by(Want.created_at.desc()).all()
    return {
        "success": True,
        "data": [{
            "id": w.id,
            "card_name": w.card_name,
            "set_code": w.set_code,
            "min_condition": w.min_condition,
            "max_price": w.max_price,
            "created_at": w.created_at.isoformat()
        } for w in wants]
    }

@app.post("/api/v1/marketplace/wants")
async def create_want(want: WantCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = Want(
        user_id=current_user.id,
        card_name=want.card_name.strip(),
        set_code=want.set_code.strip().upper() if want.set_code else None,
        min_condition=want.min_condition,
        max_price=want.max_price
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return {"success": True, "data": {"id": w.id}}

@app.delete("/api/v1/marketplace/wants/{want_id}")
async def delete_want(want_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = db.query(Want).filter(Want.id == want_id, Want.user_id == current_user.id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Want not found")
    db.delete(w)
    db.commit()
    return {"success": True}

@app.get("/api/v1/marketplace/matches")
async def get_matches(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    For each want, find other users (marketplace_enabled = true) whose inventory contains matching cards.
    Matching heuristic (MVP):
    - exact card_name match (case-insensitive contains)
    - optional set_code match if provided
    """
    wants = db.query(Want).filter(Want.user_id == current_user.id).all()
    matches = []

    for w in wants:
        q = db.query(InventoryEntry, User).join(User, InventoryEntry.user_id == User.id)
        q = q.filter(User.id != current_user.id)
        q = q.filter(User.marketplace_enabled == True)  # noqa: E712
        q = q.filter(InventoryEntry.card_name.ilike(f"%{w.card_name}%"))
        if w.set_code:
            q = q.filter(InventoryEntry.set_code == w.set_code)

        # limit matches per want
        rows = q.limit(10).all()
        for inv, owner in rows:
            matches.append({
                "want_id": w.id,
                "wanted": {"card_name": w.card_name, "set_code": w.set_code},
                "owner": {"user_id": owner.id, "username": owner.username},
                "have": {"inventory_entry_id": inv.id, "card_name": inv.card_name, "set_code": inv.set_code, "condition": inv.condition, "quantity": inv.quantity},
            })

    # Create simple notifications for new matches (MVP: always notify on fetch, but dedupe by message text per day)
    today = datetime.utcnow().date().isoformat()
    for m in matches[:20]:
        title = "Marketplace match found"
        msg = f"You want '{m['wanted']['card_name']}' and {m['owner']['username']} has '{m['have']['card_name']}' ({m['have']['set_code']})."
        existing = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.type == "marketplace_match",
            Notification.title == title,
            Notification.message == msg
        ).first()
        if not existing:
            db.add(Notification(
                user_id=current_user.id,
                type="marketplace_match",
                title=title,
                message=msg,
            ))
    db.commit()

    return {"success": True, "data": matches}

# Notifications
@app.get("/api/v1/notifications")
async def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Generate basic trend notifications (MVP mock): respect subscription tier limits
    tier_info = SUBSCRIPTION_TIERS.get(current_user.subscription_tier, SUBSCRIPTION_TIERS["free"])
    max_trends = tier_info["max_trend_insights"]
    inv = db.query(InventoryEntry).filter(InventoryEntry.user_id == current_user.id).order_by(InventoryEntry.current_value.desc().nullslast()).limit(max_trends).all()
    for item in inv:
        if item.current_value:
            title = "Portfolio trend"
            msg = f"'{item.card_name}' ({item.set_code}) is trending. Current value: ${item.current_value:.2f}."
            existing = db.query(Notification).filter(
                Notification.user_id == current_user.id,
                Notification.type == "trend",
                Notification.message == msg
            ).first()
            if not existing:
                db.add(Notification(
                    user_id=current_user.id,
                    type="trend",
                    title=title,
                    message=msg
                ))
    db.commit()

    notes = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return {
        "success": True,
        "data": [{
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "read": n.read,
            "created_at": n.created_at.isoformat()
        } for n in notes]
    }

@app.get("/api/v1/notifications/unread-count")
async def unread_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.read == False).count()  # noqa: E712
    return {"success": True, "data": {"count": c}}

@app.post("/api/v1/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read = True
    db.commit()
    return {"success": True}

# Settings
@app.get("/api/v1/settings")
async def get_settings(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "username": current_user.username,
            "email": current_user.email,
            "inventory_public": current_user.inventory_public,
            "marketplace_enabled": current_user.marketplace_enabled,
            "notification_in_app": current_user.notification_in_app,
            "city": current_user.city,
            "state_province": current_user.state_province,
            "country": current_user.country
        }
    }

@app.patch("/api/v1/settings")
async def update_settings(payload: SettingsUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.inventory_public is not None:
        current_user.inventory_public = payload.inventory_public
    if payload.marketplace_enabled is not None:
        current_user.marketplace_enabled = payload.marketplace_enabled
    if payload.notification_in_app is not None:
        current_user.notification_in_app = payload.notification_in_app
    if payload.city is not None:
        current_user.city = payload.city.strip() if payload.city else None
    if payload.state_province is not None:
        current_user.state_province = payload.state_province.strip() if payload.state_province else None
    if payload.country is not None:
        current_user.country = payload.country.strip() if payload.country else None
    db.commit()
    return {"success": True}

# Dashboard Endpoint
@app.get("/api/v1/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get dashboard summary statistics"""
    
    # Get inventory stats
    inventory_items = db.query(InventoryEntry).filter(InventoryEntry.user_id == current_user.id).all()
    total_cards = sum(item.quantity for item in inventory_items)
    total_value = sum((item.current_value or 0) * item.quantity for item in inventory_items)
    
    # Calculate value change (mock - in production, compare with previous snapshot)
    value_change = total_value * 0.05  # Mock 5% increase
    value_change_percent = 5.0 if total_value > 0 else 0.0
    
    # Get recent scans (last 7 days)
    recent_scans = db.query(Scan).filter(
        Scan.user_id == current_user.id,
        Scan.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    # Marketplace stats (wants + matches)
    active_listings = 0
    pending_trades = 0
    unread_alerts = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.read == False).count()  # noqa: E712
    
    return {
        "success": True,
        "data": {
            "total_cards": total_cards,
            "total_value": round(total_value, 2),
            "value_change": round(value_change, 2),
            "value_change_percent": value_change_percent,
            "recent_scans": recent_scans,
            "active_listings": active_listings,
            "pending_trades": pending_trades,
            "unread_alerts": unread_alerts
        }
    }

# Subscription
@app.get("/api/v1/subscription")
async def get_subscription(current_user: User = Depends(get_current_user)):
    """Get current subscription tier and limits"""
    tier_info = SUBSCRIPTION_TIERS.get(current_user.subscription_tier, SUBSCRIPTION_TIERS["free"])
    return {
        "success": True,
        "data": {
            "tier": current_user.subscription_tier,
            "tier_name": tier_info["name"],
            "max_cards": tier_info["max_cards"],
            "max_trend_insights": tier_info["max_trend_insights"],
            "price": tier_info["price"],
            "price_period": tier_info["price_period"]
        }
    }

@app.get("/api/v1/subscription/tiers")
async def get_subscription_tiers():
    """Get all available subscription tiers"""
    return {
        "success": True,
        "data": [
            {
                "tier": tier_key,
                **tier_info
            }
            for tier_key, tier_info in SUBSCRIPTION_TIERS.items()
        ]
    }

@app.post("/api/v1/subscription/upgrade")
async def upgrade_subscription(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upgrade subscription tier (MVP: no payment processing, just update tier)"""
    new_tier = payload.get("tier")
    if new_tier not in SUBSCRIPTION_TIERS:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")
    
    # In production, verify payment here before upgrading
    # For MVP, just update the tier
    current_user.subscription_tier = new_tier
    db.commit()
    
    tier_info = SUBSCRIPTION_TIERS[new_tier]
    return {
        "success": True,
        "data": {
            "tier": new_tier,
            "tier_name": tier_info["name"],
            "message": f"Successfully upgraded to {tier_info['name']}!"
        }
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
