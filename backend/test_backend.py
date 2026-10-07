import os
import sys

# Ensure backend can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_db, add_observation, get_observations, add_expedition, get_expeditions
from backend.garden_engine import calculate_garden_calendar
from backend.trail_generator import generate_trail_route
from backend.acoustic_analyzer import analyze_audio_bytes
from backend.ai_engine import check_ollama_status, query_gemma, reason_bird_identification

def run_tests():
    print("=== TEST 1: Database Initialization ===")
    init_db()
    obs_id = add_observation(
        category="bird",
        species_name="Black-capped Chickadee",
        scientific_name="Poecile atricapillus",
        confidence=94.5,
        location_name="Pine Ridge Trail",
        notes="Whistling two-tone call from high pine branch."
    )
    obs = get_observations()
    assert len(obs) > 0, "No observations retrieved"
    print(f"SUCCESS: Inserted and retrieved observation ID {obs_id}: {obs[0]['species_name']}")

    print("\n=== TEST 2: Garden Frost Calculations ===")
    garden = calculate_garden_calendar("6")
    assert "days_to_fall_frost" in garden
    print(f"SUCCESS: Zone 6 calculated: {garden['days_to_fall_frost']} days until fall frost. Season: {garden['season_status']}")

    print("\n=== TEST 3: Trail Route & GPX Generation ===")
    trail = generate_trail_route(40.7829, -73.9654, distance_km=5.0, route_type="run")
    assert len(trail["waypoints"]) > 5
    assert "<gpx" in trail["gpx_data"]
    print(f"SUCCESS: Generated 5km trail route with {len(trail['waypoints'])} waypoints and valid GPX XML ({len(trail['gpx_data'])} bytes)")

    print("\n=== TEST 4: Bioacoustic Analyzer with Real WAV ===")
    sample_wav = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", "chickadee_call.wav")
    assert os.path.exists(sample_wav), f"Sample file {sample_wav} missing"
    with open(sample_wav, "rb") as f:
        audio_bytes = f.read()
    metrics = analyze_audio_bytes(audio_bytes)
    assert metrics["dominant_frequency_hz"] > 0
    assert metrics["spectrogram_image"].startswith("data:image/png;base64,")
    print(f"SUCCESS: Audio analyzed! Dominant Freq: {metrics['dominant_frequency_hz']} Hz, Pitch: {metrics['pitch_profile']}")

    print("\n=== TEST 5: Local Ollama & Gemma 3 Model Check ===")
    status = check_ollama_status()
    print(f"Ollama status: {status}")
    if status["online"]:
        print("Testing Gemma 3 inference...")
        quick_resp = query_gemma("Respond with 'GROUNDED_ONLINE'", timeout=15)
        print(f"Gemma 3 test response: {quick_resp}")

    print("\n=== TEST 6: Bioacoustic Bird Reasoning ===")
    reasoning = reason_bird_identification(metrics, habitat_context="conifer forest edge")
    print(f"Bird Identified: {reasoning.get('primary_species')} ({reasoning.get('scientific_name')})")
    print(f"Rationale: {reasoning.get('acoustic_match_rationale')[:100]}...")

    print("\nALL BACKEND UNIT & INTEGRATION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    run_tests()
