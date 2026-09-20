# LivestockGuard AI — Backend MVP

**LivestockGuard AI** is a clean, modular Python FastAPI backend for an AI-assisted multimodal livestock health early-warning system. Designed for cattle, buffalo, goats, sheep, poultry, and other farm animals, it analyzes available farm evidence (images, short videos, animal audio, behavior/activity signals, ambient temperature, and humidity) to flag potential health risks, stress indicators, and environmental hazards.

---

## ⚠️ Non-Diagnostic System Notice

> **IMPORTANT DISCLAIMER**
> - The goal of LivestockGuard AI is **NOT** to diagnose diseases or prescribe veterinary medication.
> - OpenCV image analysis and audio spectral feature extraction are used for **measurable visual and temporal feature heuristics**.
> - The risk engine weights (**Visual: 25%**, **Behaviour: 30%**, **Audio: 20%**, **Environment: 25%**) and THI thresholds are **configurable prototype parameters** and are **NOT clinically or scientifically validated**.
> - All recommendation outputs strictly adhere to:
>   > *"Inspect the animal's movement, feeding behaviour, and physical condition. Review the farm's temperature, humidity, shade and ventilation conditions. If concerning signs persist, seek veterinary assessment."*

---

## Architecture Diagram

```
                              ┌───────────────────────────────────┐
                              │     Frontend / API Consumer       │
                              └─────────────────┬─────────────────┘
                                                │ REST (HTTP/JSON/Multipart)
                                                ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FastAPI Application                                    │
│                                                                                        │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────────────────┐ │
│  │   routes_analysis     │  │    routes_animals     │  │        routes_alerts        │ │
│  └───────────┬───────────┘  └───────────┬───────────┘  └──────────────┬──────────────┘ │
│              │                          │                             │                │
│              ▼                          ▼                             ▼                │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                 Services Layer                                   │  │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │  │
│  │  │ vision_service  │ │  video_service  │ │  audio_service  │ │ env_service     │  │  │
│  │  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘ └────────┬────────┘  │  │
│  │           │                   │                   │                   │         │  │
│  │           └───────────┬───────┴─────────┬─────────┴───────────────────┘         │  │
│  │                       ▼                 ▼                                       │  │
│  │               ┌───────────────┐ ┌───────────────┐                               │  │
│  │               │  risk_engine  │ │ explanation   │                               │  │
│  │               └───────┬───────┘ └───────┬───────┘                               │  │
│  └───────────────────────┼─────────────────┼───────────────────────────────────────┘  │
│                          │                 │                                          │
│                          ▼                 ▼                                          │
│               ┌───────────────────────────────────────────┐                           │
│               │     Database Access Layer (SQLite CRUD)    │                           │
│               └─────────────────────┬─────────────────────┘                           │
└─────────────────────────────────────┼──────────────────────────────────────────────────┘
                                      ▼
                           ┌─────────────────────┐
                           │   SQLite Database   │
                           └─────────────────────┘
```

---

## Dataset and Model Transparency

The hackathon problem statement requests guidance on connecting suitable public livestock datasets:

1. **Visual & Behavior Datasets**:
   - *Public Options*: Open-source cattle posture/lameness vision datasets, USDA livestock video repositories.
   - *Current Implementation*: OpenCV frame preprocessing, contour aspect ratio, and mean frame differencing for optical activity signals.

2. **Audio Vocalization Datasets**:
   - *Public Options*: AudioSet animal vocalization subset, bioacoustic livestock distress call collections.
   - *Current Implementation*: `librosa` / `scipy` extraction of RMS energy, Zero-Crossing Rate (ZCR), Spectral Centroid, and MFCCs to compute acoustic anomaly scores.

3. **Environmental Stress Datasets**:
   - *Public Options*: NOAA historical agricultural weather data, Temperature Humidity Index (THI) heat stress models for livestock.
   - *Current Implementation*: Dynamic THI calculation based on configurable environmental thresholds.

*Note*: Unless external model API keys (`VISION_API_KEY` or `LLM_API_KEY`) are set in `.env`, the system executes 100% locally using feature-extraction heuristics.

---

## API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root service health check |
| `GET` | `/health` | Detailed health & non-diagnostic status |
| `POST` | `/animals` | Register or update an animal profile |
| `GET` | `/animals` | List all registered animals |
| `GET` | `/animals/{animal_id}` | Get animal information |
| `GET` | `/animals/{animal_id}/history` | Chronological analysis history for an animal |
| `POST` | `/analyze/image` | Single-modality image feature analysis |
| `POST` | `/analyze/video` | Single-modality video frame differencing analysis |
| `POST` | `/analyze/audio` | Single-modality audio spectral feature analysis |
| `POST` | `/analyze/environment` | Environmental THI heat stress risk assessment |
| `POST` | `/analyze` | Main multimodal analysis pipeline (accepts any combination) |
| `GET` | `/alerts` | Get all alerts |
| `GET` | `/alerts/active` | Get active alerts only |
| `GET` | `/alerts/resolved` | Get resolved alerts only |
| `POST` | `/alerts/{alert_id}/resolve` | Resolve an active alert (updates status to NORMAL) |
| `GET` | `/dashboard/summary` | Get aggregated dashboard metrics and counts |
| `POST` | `/assistant` | Contextual AI assistant endpoint for animal history QA |
| `GET` | `/demo/analysis/{animal_id}` | Pre-populated demo analysis for frontend presentation |

---

## Quickstart & Local Setup

### 1. Requirements & Virtual Environment
- Python 3.11+

```bash
# Clone or navigate to the directory
cd livestockguard-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Tests
```bash
pytest
```

### 4. Start the Application Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

---

## Standardized `/analyze` Response Example

```json
{
  "analysis_id": "anls_a1b2c3d4",
  "animal": {
    "animal_id": "Cow-17",
    "species": "cattle",
    "age": 4.5,
    "farm_id": "GreenValley"
  },
  "risk": {
    "score": 78,
    "level": "HIGH_RISK"
  },
  "modalities_analyzed": ["image", "video", "environment"],
  "indicators": [
    {
      "modality": "video",
      "name": "reduced_activity",
      "confidence": 0.85,
      "description": "Significantly reduced inter-frame movement detected over 12 analyzed frames."
    },
    {
      "modality": "image",
      "name": "unusual_posture_signal",
      "confidence": 0.82,
      "description": "Prototype visual analysis detected abnormal standing posture alignment."
    },
    {
      "modality": "environment",
      "name": "potential_heat_stress_environment",
      "confidence": 0.90,
      "description": "Temperature of 34°C with 72% humidity indicates heat stress risk conditions."
    }
  ],
  "explanation": "Cow-17 was flagged with risk level HIGH_RISK because potential health risk indicators were observed: reduced activity, unusual posture signal, potential heat stress environment.",
  "recommendation": "Inspect the animal's movement, feeding behaviour, and physical condition. Review the farm's temperature, humidity, shade and ventilation conditions. If concerning signs persist, seek veterinary assessment.",
  "alert_created": true,
  "alert": {
    "alert_id": "alt_e5f6g7h8",
    "status": "ACTIVE",
    "created_at": "2026-09-20T12:00:00Z"
  },
  "created_at": "2026-09-20T12:00:00Z"
}
```

---

## Frontend Integration Guide

1. **Dashboard Overview**: Fetch `GET /dashboard/summary` to populate dashboard cards (Total Animals, Normal, Attention, High Risk, Resolved Alerts).
2. **Demo Mode for Live Presentations**: Fetch `GET /demo/analysis/Cow-17` or `GET /demo/analysis/Goat-08` to instantly load realistic risk data into the UI without requiring actual file uploads.
3. **Multimodal Analysis Form**: Send `multipart/form-data` to `POST /analyze`. Any modality (image, video, audio, temperature, humidity) can be omitted without breaking the analysis or incurring artificial zero scores.
4. **Alert Resolution**: Call `POST /alerts/{alert_id}/resolve` when a farmer marks a risk alert as handled. The UI can filter active and resolved alerts using `GET /alerts/active` and `GET /alerts/resolved`.
