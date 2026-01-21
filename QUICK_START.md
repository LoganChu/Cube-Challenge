# CardVault Quick Start - 1 Day MVP

## Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend dev, optional)
- Python 3.11+ (for local backend dev, optional)

## Fast Setup (Docker - Recommended)

1. **Clone and start services:**
```bash
docker-compose up -d
```

2. **Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- ML Service: http://localhost:8001
- API Docs: http://localhost:8000/docs

3. **Test the API:**
```bash
# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","username":"testuser"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'

# Save the access_token from response
```

## Manual Setup (Without Docker)

### Backend

1. **Navigate to backend:**
```bash
cd backend
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the server:**
```bash
python main.py
```

Backend runs on http://localhost:8000

### ML Service

1. **Navigate to ml-service:**
```bash
cd ml-service
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the service:**
```bash
python app.py
```

ML Service runs on http://localhost:8001

### Frontend

1. **Navigate to frontend:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Run the dev server:**
```bash
npm start
```

Frontend runs on http://localhost:3000

## Key Features (MVP)

✅ User authentication (register/login)  
✅ Single-card scanning (mock ML)  
✅ Multi-card scanning (mock ML)  
✅ Inventory management  
✅ Basic API endpoints  

## What's Mocked

For the 1-day MVP, the following are mocked/simplified:
- **ML Models**: Mock card detection (returns hardcoded cards)
- **Database**: SQLite (easy setup, switch to PostgreSQL for production)
- **Price Data**: Hardcoded values (can add real price feeds later)
- **File Storage**: Local filesystem (switch to S3 for production)

## Next Steps

1. **Replace mock ML with real models:**
   - Install PyTorch/ONNX Runtime
   - Download pre-trained YOLOv8 and EfficientNet models
   - Update `ml-service/app.py` with actual inference

2. **Add real price feeds:**
   - Integrate TCGPlayer API
   - Add eBay scraping/API
   - Implement valuation calculation

3. **Switch to production database:**
   - Update `DATABASE_URL` to PostgreSQL
   - Run migrations

4. **Add missing features:**
   - Marketplace listings
   - Messaging system
   - AI agent alerts
   - Condition grading

## Troubleshooting

**Port already in use:**
- Change ports in `docker-compose.yml`

**Database errors:**
- Delete `cardvault.db` and restart (SQLite)
- Or use PostgreSQL: `DATABASE_URL=postgresql://user:pass@localhost:5432/cardvault`

**Frontend can't connect to API:**
- Check `REACT_APP_API_URL` in frontend environment
- Ensure backend is running on port 8000

## API Testing

Use the interactive docs at http://localhost:8000/docs to test all endpoints.

Or use curl:
```bash
# Get access token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}' \
  | jq -r '.access_token')

# Get inventory
curl -X GET http://localhost:8000/api/v1/inventory \
  -H "Authorization: Bearer $TOKEN"
```
