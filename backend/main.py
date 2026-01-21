"""
CardVault Backend API Server
FastAPI-based REST API for MVP
"""
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8001")

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
    
    inventory = relationship("InventoryEntry", back_populates="user")

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
    scanned_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="inventory")

class Scan(Base):
    __tablename__ = "scans"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    image_url = Column(String)
    scan_type = Column(String)  # "single" or "multi"
    status = Column(String, default="pending")  # "pending", "processing", "completed", "failed"
    results = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

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

@app.post("/api/v1/auth/login", response_model=TokenResponse)
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
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=900,
        user={"id": user.id, "email": user.email, "username": user.username}
    )

# Scan Endpoints
@app.post("/api/v1/scans/upload")
async def upload_scan(
    image: UploadFile = File(...),
    scan_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Save uploaded file
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / f"{uuid.uuid4()}_{image.filename}"
    with open(file_path, "wb") as f:
        content = await image.read()
        f.write(content)
    
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
    
    # Call ML service (async)
    try:
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {"image": (image.filename, f, image.content_type)}
                response = await client.post(
                    f"{ML_SERVICE_URL}/predict",
                    files=files,
                    data={"scan_type": scan_type},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    scan.results = str(results)
                    scan.status = "completed"
                else:
                    scan.status = "failed"
    except Exception as e:
        scan.status = "failed"
        scan.results = str(e)
    
    db.commit()
    
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
    limit: int = 50,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(InventoryEntry).filter(InventoryEntry.user_id == current_user.id)
    
    if search:
        query = query.filter(
            (InventoryEntry.card_name.contains(search)) |
            (InventoryEntry.set_code.contains(search))
        )
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "success": True,
        "data": {
            "items": [{
                "id": item.id,
                "card": {
                    "id": item.id,
                    "name": item.card_name,
                    "set": {"code": item.set_code},
                    "image_url": item.scan_image_url or ""
                },
                "quantity": item.quantity,
                "condition": item.condition,
                "current_value": {"amount": item.current_value or 0, "currency": "USD"} if item.current_value else None,
                "scanned_at": item.scanned_at.isoformat()
            } for item in items],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }
    }

@app.post("/api/v1/scans/{scan_id}/save")
async def save_scan_to_inventory(
    scan_id: str,
    card_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == current_user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if not scan.results:
        raise HTTPException(status_code=400, detail="Scan not completed")
    
    import json
    results = json.loads(scan.results)
    detected_cards = results.get("detected_cards", [])
    
    saved_count = 0
    inventory_entries = []
    
    for card_data in detected_cards:
        if card_data.get("id") in card_ids:
            entry = InventoryEntry(
                user_id=current_user.id,
                card_name=card_data.get("name", ""),
                set_code=card_data.get("set_code", ""),
                quantity=1,
                condition="Near Mint",  # Default
                current_value=0.0,  # Default, will be updated later
                scan_image_url=scan.image_url
            )
            db.add(entry)
            inventory_entries.append(entry)
            saved_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "data": {
            "saved_count": saved_count,
            "inventory_entries": [{"id": e.id, "card_name": e.card_name} for e in inventory_entries]
        }
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
