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
    notification_in_app = Column(Boolean, default=True)
    # Location fields
    city = Column(String, nullable=True)
    state_province = Column(String, nullable=True)
    country = Column(String, nullable=True)
    
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
        conn.commit()
    finally:
        conn.close()

_ensure_sqlite_columns()

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
    # Generate basic trend notifications (MVP mock): top 3 cards by value
    inv = db.query(InventoryEntry).filter(InventoryEntry.user_id == current_user.id).order_by(InventoryEntry.current_value.desc().nullslast()).limit(3).all()
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

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
