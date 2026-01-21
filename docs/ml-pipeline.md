# CardVault ML Pipeline Design

## Overview

CardVault's ML pipeline consists of 5 main components:
1. Multi-card detection & cropping
2. Card classification (set & name)
3. Condition grading
4. OCR for identifiers
5. Valuation model (optional, post-MVP)

---

## Component 1: Multi-Card Detection & Cropping

### Purpose
Detect all card bounding boxes in a single image containing multiple cards.

### Model Choice: YOLOv8
**Rationale**: State-of-the-art object detection, fast inference (<200ms on GPU), good balance of accuracy/speed.

**Alternatives Considered**:
- **Faster R-CNN**: More accurate but slower (500-1000ms)
- **RetinaNet**: Good accuracy, slower than YOLOv8
- **Custom CNN**: Requires extensive training data

**Tradeoff**: YOLOv8 chosen for latency (sub-second inference) despite slightly lower accuracy than Faster R-CNN.

### Input/Output
**Input**:
- Image (JPEG/PNG, max 10MB)
- Resolution: Variable (resized to 640x640 for inference)

**Output**:
```json
{
  "detections": [
    {
      "bounding_box": { "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4 },
      "confidence": 0.95,
      "class": "card"
    }
  ],
  "total_cards": 5
}
```

### Training Data Suggestions
- **Source**: Collect images from users, annotate with bounding boxes
- **Target**: 10,000+ annotated images (2-20 cards per image)
- **Diversity**: Different card arrangements (grid, scattered, overlapping), lighting conditions, backgrounds
- **Annotation Tool**: LabelImg, CVAT, or custom tool
- **Augmentation**: Rotation (±15°), brightness (±20%), blur, noise

### Evaluation Metrics
- **mAP@0.5** (mean Average Precision): Target ≥0.90
- **Recall**: Target ≥0.90 (minimize missed cards)
- **Precision**: Target ≥0.85 (minimize false positives)
- **Inference Latency**: Target <200ms per image (p95, GPU)

### Implementation Notes
- **Preprocessing**: Resize to 640x640, normalize [0,1]
- **Postprocessing**: Non-maximum suppression (NMS), filter by confidence ≥0.5
- **Cropping**: Extract card regions, pad by 10% margin for context
- **Batch Processing**: Process up to 10 images in parallel (GPU memory permitting)

---

## Component 2: Card Classification (Set & Name)

### Purpose
Identify card set and name from cropped card image.

### Model Choice: Vision Transformer (ViT-B/16) or EfficientNet-B3
**Rationale**: 
- **ViT-B/16**: Excellent accuracy on fine-grained classification, good transfer learning
- **EfficientNet-B3**: Faster inference, smaller model size, competitive accuracy

**Recommendation**: Start with **EfficientNet-B3** (faster, smaller), upgrade to **ViT** if accuracy insufficient.

**Tradeoff**: EfficientNet-B3 is 2-3x faster but ViT may achieve 2-5% better accuracy on complex cards.

### Input/Output
**Input**:
- Cropped card image (224x224 or 384x384)
- Normalized RGB [0,1]

**Output**:
```json
{
  "set": {
    "id": "uuid",
    "name": "Core Set 2021",
    "code": "M21",
    "confidence": 0.92
  },
  "card_name": {
    "name": "Lightning Bolt",
    "confidence": 0.88
  },
  "top_k_predictions": [
    { "set_code": "M21", "card_name": "Lightning Bolt", "confidence": 0.88 },
    { "set_code": "M21", "card_name": "Lightning Strike", "confidence": 0.10 }
  ]
}
```

### Architecture Options

#### Option A: Two-Stage Model
- Stage 1: Set classifier (predict set from image)
- Stage 2: Card classifier (predict card name within set)
- **Pros**: Smaller card classifiers per set, faster inference
- **Cons**: Error propagation (wrong set → wrong card)

#### Option B: Single Joint Model
- Single model: Set + Card Name (multitask learning)
- **Pros**: End-to-end optimization, better accuracy
- **Cons**: Larger model, slower inference

**Recommendation**: Start with **Option B** (simpler), consider Option A if sets have >500 cards each.

### Training Data Suggestions
- **Source**: 
  - Public card databases (Scryfall API, Pokémon API)
  - User-uploaded images (with manual corrections)
  - Synthetic data generation (rotation, brightness, shadows)
- **Target**: 
  - 50,000+ labeled images minimum
  - At least 100 images per card (for common cards)
  - At least 10 images per card (for rare cards)
- **Labeling**: Use existing card databases (Scryfall ID, TCGPlayer ID) for automated labeling
- **Data Balancing**: Oversample rare cards, undersample common cards

### Evaluation Metrics
- **Top-1 Accuracy**: Target ≥85% overall
- **Top-3 Accuracy**: Target ≥95% overall
- **Per-Set Accuracy**: Target ≥80% for sets with >50 cards
- **Inference Latency**: Target <300ms per card (p95, GPU)

### Fine-Tuning Strategy
1. **Base Model**: Pre-trained on ImageNet (EfficientNet) or JFT (ViT)
2. **Domain Adaptation**: Fine-tune on card images (general card dataset)
3. **Task-Specific**: Fine-tune on labeled set+name pairs
4. **Continuous Learning**: Retrain monthly with new user corrections

---

## Component 3: Condition Grading

### Purpose
Estimate card condition (1-10 scale or categorical) from image.

### Model Choice: Regression Model (EfficientNet-B2) or Classification Model
**Approach**: Regression (1-10 scale) preferred for granularity.

**Architecture**:
- Backbone: EfficientNet-B2 (or ResNet-50)
- Head: 1 linear layer → scalar output (1-10)
- Loss: Huber loss (robust to outliers)

**Alternative**: Classification (10 classes) - simpler but less granular.

### Input/Output
**Input**:
- Cropped card image (224x224)
- Focused regions: edges, corners, surface (optional preprocessing)

**Output**:
```json
{
  "condition_grade": 9.5,
  "confidence": 0.82,
  "condition_category": "Near Mint",
  "breakdown": {
    "edges": 9.0,
    "corners": 9.5,
    "surface": 9.8,
    "centering": 9.2
  }
}
```

### Training Data Suggestions
- **Source**: 
  - Professional grading services (PSA, BGS) - if data available
  - User-labeled images with manual condition assessment
  - Synthetic degradation (scratches, wear simulation)
- **Target**: 
  - 20,000+ labeled images
  - Balanced distribution across conditions (avoid over-representing NM)
  - Expert annotations (at least 2 graders per image, consensus)
- **Labeling**: Use categorical labels (NM, LP, MP, HP, D) and map to 1-10 scale:
  - Near Mint: 9.0-10.0
  - Lightly Played: 7.0-8.9
  - Moderately Played: 5.0-6.9
  - Heavily Played: 3.0-4.9
  - Damaged: 1.0-2.9

### Evaluation Metrics
- **MAE** (Mean Absolute Error): Target <1.0 grade
- **Within 1 Grade Accuracy**: Target ≥75% (within ±1 grade of expert)
- **Per-Condition Accuracy**: Target ≥70% correct category

### Implementation Notes
- **Preprocessing**: Enhance edges/corners (Canny edge detection), normalize lighting
- **Augmentation**: Rotate, flip, adjust brightness (realistic wear patterns)
- **Confidence Thresholds**: Only show estimate if confidence ≥0.70

---

## Component 4: OCR for Card Identifiers

### Purpose
Extract card numbers (e.g., "001/150"), serial numbers, foil stamps from images.

### Model Choice: Tesseract OCR (Open Source) or Google Cloud Vision API
**Recommendation**: Start with **Tesseract** (free), use **Google Cloud Vision** if accuracy insufficient.

**Tradeoff**: Tesseract is free but may struggle with small text. Google Cloud Vision is paid but more accurate.

### Input/Output
**Input**:
- Cropped card image (full card or focused region)
- Region of interest: Card number area (bottom-right typically)

**Output**:
```json
{
  "card_number": "001/150",
  "confidence": 0.95,
  "serial_number": null, // if present
  "foil_stamp": true,
  "raw_text": "001/150"
}
```

### Training Data Suggestions
- **Source**: Card images with known identifiers
- **Target**: 5,000+ images with labeled card numbers
- **Preprocessing**: Crop to card number region, enhance contrast, binarize

### Evaluation Metrics
- **Character Accuracy**: Target ≥90% for clear images
- **Exact Match Accuracy**: Target ≥85% for card numbers
- **Latency**: Target <500ms per card (Tesseract) or <200ms (Cloud Vision)

### Implementation Notes
- **Region Detection**: Use template matching or ML to locate card number region
- **Text Cleanup**: Post-process OCR output (regex patterns, common corrections)
- **Fallback**: If OCR fails, rely on classification model

---

## Component 5: Valuation Model (Post-MVP)

### Purpose
Predict future card prices using historical data (optional, post-MVP).

### Model Choice: Time Series Model (LSTM/Transformer) or Regression
**Approach**: Time series forecasting (predict price 30/60/90 days ahead).

**Architecture**: 
- Input: Historical prices (last 180 days), card features (set, rarity, popularity)
- Model: LSTM or Transformer (Time Series Transformer)
- Output: Price forecast with confidence intervals

### Evaluation Metrics
- **MAE**: Target <15% of actual price (30-day forecast)
- **Direction Accuracy**: Target ≥60% (predict price up/down correctly)

---

## ML Pipeline Architecture

### Inference Flow

```
User uploads image
    ↓
[Preprocessor] Resize, normalize
    ↓
[Card Detector] YOLOv8 → bounding boxes
    ↓
[Card Cropper] Extract card regions
    ↓
For each card:
    ├─ [Classifier] EfficientNet → set + name
    ├─ [Condition Grader] EfficientNet → condition score
    └─ [OCR] Tesseract → card number
    ↓
[Postprocessor] Confidence filtering, deduplication
    ↓
Return results to API
```

### Deployment

**Containerization**: Docker container with GPU support
- **Base Image**: `nvidia/cuda:11.8.0-runtime-ubuntu22.04`
- **Framework**: PyTorch 2.0+ or TensorFlow 2.x
- **Model Serving**: FastAPI + Uvicorn or TorchServe

**Optimization**:
- **Model Quantization**: INT8 quantization for faster inference
- **ONNX Runtime**: Convert models to ONNX for cross-platform optimization
- **TensorRT**: NVIDIA GPU optimization (2-5x speedup)
- **Batch Processing**: Process multiple cards in parallel

**Scaling**:
- **Horizontal Scaling**: Kubernetes with GPU nodes (GKE, EKS)
- **Auto-scaling**: Scale based on queue length
- **Caching**: Cache classification results for identical images (hash-based)

### Model Monitoring

- **Drift Detection**: Monitor accuracy over time (user corrections as ground truth)
- **A/B Testing**: Test new models against production (shadow mode)
- **Performance Metrics**: Track latency, GPU utilization, throughput
- **Error Logging**: Log misclassifications for retraining

---

## Recommended External APIs/Vendors

### Price Data
- **TCGPlayer API**: Official pricing (MTG, Pokémon, Yu-Gi-Oh!)
- **eBay API**: Historical sales data
- **CardMarket**: European pricing
- **Scryfall API**: MTG card database (free)

### ML/OCR Services
- **Google Cloud Vision API**: OCR (paid, high accuracy)
- **AWS Rekognition**: Card detection/classification (paid)
- **Azure Computer Vision**: OCR alternative

### Open Source Models
- **YOLOv8**: Ultralytics (GitHub: ultralytics/ultralytics)
- **EfficientNet**: TensorFlow Hub or PyTorch Hub
- **Vision Transformer**: Hugging Face Transformers
- **Tesseract OCR**: GitHub: tesseract-ocr/tesseract

---

## Training Pipeline

### Data Collection
1. **User Uploads**: Collect user-uploaded images with manual corrections
2. **External Sources**: Scrape card databases (with permission) or use APIs
3. **Data Labeling**: Use active learning (prioritize uncertain predictions)

### Training Workflow
1. **Data Pipeline**: Extract, transform, label images
2. **Model Training**: Train on GPU cluster (single GPU sufficient for EfficientNet)
3. **Validation**: Evaluate on held-out test set
4. **Model Registry**: Version models (MLflow, DVC, or S3)
5. **Deployment**: Deploy new model to staging, run shadow mode, promote to production

### Continuous Improvement
- **Feedback Loop**: User corrections → retrain model monthly
- **Active Learning**: Prioritize uncertain predictions for labeling
- **A/B Testing**: Compare model versions in production

---

## Cost Estimates (AWS/GCP)

### Training (One-time)
- **GPU Instance** (p3.2xlarge): ~$3/hour × 24 hours = $72 per training run
- **Storage**: S3/GS ~$0.023/GB/month

### Inference (Ongoing)
- **GPU Instance** (g4dn.xlarge): ~$0.50/hour × 730 hours = $365/month (always-on)
- **Serverless** (Lambda/Cloud Functions): ~$0.00001667/GB-second (pay-per-use, may be cheaper for low volume)

**Recommendation**: Start with serverless, move to dedicated GPU if volume >1000 scans/day.
