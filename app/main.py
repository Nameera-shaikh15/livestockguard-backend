from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LivestockGuard AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://livestockguard-ai.vercel.app",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "LivestockGuard AI backend is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze")
async def analyze(
    temperature: float = Form(...),
    humidity: float = Form(...),
    activity_level: float = Form(...),
    image: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
):
    return {
        "status": "success",
        "message": "Analysis received",
        "temperature": temperature,
        "humidity": humidity,
        "activity_level": activity_level,
        "image_received": image is not None,
        "audio_received": audio is not None,
    }