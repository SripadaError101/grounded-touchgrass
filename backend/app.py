import os
import io
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .database import (
    init_db, add_observation, get_observations, delete_observation,
    add_expedition, get_expeditions, complete_expedition
)
from .acoustic_analyzer import analyze_audio_bytes
from .garden_engine import calculate_garden_calendar, HARDINESS_ZONES
from .trail_generator import generate_trail_route
from .ai_engine import (
    check_ollama_status, generate_quick_dispatch,
    reason_bird_identification, reason_garden_advice
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")

app = FastAPI(title="Grounded TouchGrass AI", version="1.0.0")

# Initialize SQLite database
init_db()

# Request schemas
class DispatchRequest(BaseModel):
    activity_type: str = "walk"
    duration_mins: int = 30
    environment: str = "woodland"

class GardenQueryRequest(BaseModel):
    zone: str = "6"
    query: str = ""

class TrailRouteRequest(BaseModel):
    center_lat: float = 40.7829
    center_lng: float = -73.9654
    distance_km: float = 5.0
    route_type: str = "run"
    foliage_focus: str = "high"

class ObservationRequest(BaseModel):
    category: str
    species_name: str
    scientific_name: str = ""
    confidence: float = 0.0
    location_name: str = "Trailside"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: str = ""
    acoustic_data: str = ""

class CompleteExpeditionRequest(BaseModel):
    notes: str = ""

@app.get("/api/status")
def get_system_status():
    """System and local model status."""
    return check_ollama_status()

@app.post("/api/dispatch")
def create_field_dispatch(req: DispatchRequest):
    """Generates a 30-second expedition card to push users outside immediately."""
    dispatch = generate_quick_dispatch(req.activity_type, req.duration_mins, req.environment)
    exp_id = add_expedition(
        activity_type=req.activity_type,
        title=dispatch.get("title", "Outdoor Expedition"),
        objective=dispatch.get("primary_mission", ""),
        sensory_prompt=dispatch.get("auditory_anchor", ""),
        duration_mins=req.duration_mins
    )
    dispatch["expedition_id"] = exp_id
    return dispatch

@app.get("/api/samples")
def list_sample_audio():
    """Returns available local bioacoustic audio samples."""
    samples = [
        {"id": "chickadee_call.wav", "name": "Black-capped Chickadee (Whistle & Dee)", "expected": "Poecile atricapillus", "pitch": "High clear whistle (3.2 - 3.8 kHz)"},
        {"id": "american_robin.wav", "name": "American Robin (Spring/Fall Carol)", "expected": "Turdus migratorius", "pitch": "Musical carols (2.2 - 2.8 kHz)"},
        {"id": "northern_cardinal.wav", "name": "Northern Cardinal (Cheer-Cheer Sweeps)", "expected": "Cardinalis cardinalis", "pitch": "Rapid frequency sweeps (2.1 - 4.2 kHz)"},
        {"id": "mourning_dove.wav", "name": "Mourning Dove (Perch Coo)", "expected": "Zenaida macroura", "pitch": "Low resonant coos (440 - 560 Hz)"},
        {"id": "barred_owl.wav", "name": "Barred Owl (Forest Hoot Series)", "expected": "Strix varia", "pitch": "Deep nocturnal hoots (290 - 340 Hz)"}
    ]
    return samples

@app.get("/api/samples/audio/{filename}")
def serve_sample_audio(filename: str):
    """Serves sample audio WAV for HTML5 audio playback."""
    path = os.path.join(SAMPLES_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Sample audio file not found")
    return FileResponse(path, media_type="audio/wav")

@app.post("/api/identify/audio")
async def identify_audio(
    file: Optional[UploadFile] = File(None),
    sample_id: Optional[str] = Form(None),
    habitat: Optional[str] = Form("temperate woodland / park")
):
    """
    Receives trail audio, computes FFT & spectrogram, and applies Gemma 3 bioacoustic reasoning.
    """
    audio_bytes = b""
    if file and file.filename:
        audio_bytes = await file.read()
    elif sample_id:
        sample_path = os.path.join(SAMPLES_DIR, sample_id)
        if os.path.exists(sample_path):
            with open(sample_path, "rb") as f:
                audio_bytes = f.read()
        else:
            raise HTTPException(status_code=400, detail="Invalid sample_id specified")
    else:
        raise HTTPException(status_code=400, detail="No audio file or sample specified")

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio data received")

    # Perform NumPy/SciPy acoustic feature extraction & spectrogram generation
    try:
        acoustic_metrics = analyze_audio_bytes(audio_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Audio analysis error: {str(e)}")

    # Apply Gemma 3 bioacoustic reasoning
    reasoning = reason_bird_identification(acoustic_metrics, habitat or "woodland")

    return {
        "acoustics": acoustic_metrics,
        "identification": reasoning,
        "habitat": habitat
    }

@app.get("/api/garden/calendar")
def get_garden_calendar(zone: str = "6"):
    """Returns calculated frost dates, days remaining, and crop calendar."""
    return calculate_garden_calendar(zone)

@app.post("/api/garden/advice")
def get_garden_advice(req: GardenQueryRequest):
    """Provides Gemma 3 organic soil and planting advice for this week."""
    calendar_data = calculate_garden_calendar(req.zone)
    advice_text = reason_garden_advice(calendar_data, req.query)
    return {
        "calendar": calendar_data,
        "advice": advice_text
    }

@app.post("/api/trail/generate")
def create_trail_route(req: TrailRouteRequest):
    """Generates a foliage loop route with waypoints and GPX export data."""
    route_data = generate_trail_route(
        center_lat=req.center_lat,
        center_lng=req.center_lng,
        distance_km=req.distance_km,
        route_type=req.route_type,
        foliage_focus=req.foliage_focus
    )
    return route_data

@app.post("/api/journal/observation")
def record_observation(req: ObservationRequest):
    """Logs an offline field observation to local SQLite."""
    obs_id = add_observation(
        category=req.category,
        species_name=req.species_name,
        scientific_name=req.scientific_name,
        confidence=req.confidence,
        location_name=req.location_name,
        latitude=req.latitude,
        longitude=req.longitude,
        notes=req.notes,
        acoustic_data=req.acoustic_data
    )
    return {"status": "success", "id": obs_id}

@app.get("/api/journal/observations")
def list_observations():
    """Lists recent offline field observations."""
    return get_observations(limit=50)

@app.delete("/api/journal/observation/{obs_id}")
def remove_observation(obs_id: int):
    """Deletes an observation entry."""
    success = delete_observation(obs_id)
    return {"success": success}

@app.get("/api/journal/expeditions")
def list_expeditions():
    """Lists recent dispatched expeditions."""
    return get_expeditions(limit=20)

@app.post("/api/journal/expedition/{exp_id}/complete")
def finish_expedition(exp_id: int, req: CompleteExpeditionRequest):
    """Marks an expedition completed with field notes."""
    success = complete_expedition(exp_id, req.notes)
    return {"success": success}

# Mount static frontend
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
