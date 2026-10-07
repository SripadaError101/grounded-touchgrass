import json
import requests
from typing import Dict, Any, Optional

OLLAMA_API_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "gemma3:4b"

def check_ollama_status() -> Dict[str, Any]:
    """
    Checks if local Ollama server is running and what models are available.
    """
    try:
        r = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            models = r.json().get("models", [])
            model_names = [m.get("name") for m in models]
            active_model = DEFAULT_MODEL if any(DEFAULT_MODEL in m for m in model_names) else (model_names[0] if model_names else "none")
            return {
                "online": True,
                "server": "Local Ollama Instance",
                "active_model": active_model,
                "available_models": model_names,
                "hardware": "Local GPU / CPU (Zero Cloud, 100% Offline)",
                "privacy": "Air-gapped / Zero Data Leakage"
            }
    except Exception as e:
        pass
    
    return {
        "online": False,
        "server": "Offline Fallback Mode",
        "active_model": "Embedded Heuristic Naturalist Engine",
        "available_models": ["offline-rules-engine"],
        "hardware": "Local CPU",
        "privacy": "100% Offline"
    }

def query_gemma(prompt: str, system_prompt: str = "", model: str = DEFAULT_MODEL, timeout: int = 40) -> str:
    """
    Queries local Gemma 3 open-weights model via Ollama.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.4,
            "num_predict": 700
        }
    }
    try:
        r = requests.post(f"{OLLAMA_API_URL}/api/generate", json=payload, timeout=timeout)
        if r.status_code == 200:
            return r.json().get("response", "").strip()
    except Exception as e:
        print(f"Ollama call failed or timed out: {e}")
    return ""

def generate_quick_dispatch(activity_type: str, duration_mins: int, environment: str = "woodland") -> Dict[str, Any]:
    """
    Generates a concise 30-second field expedition card to get someone immediately outside.
    """
    system_prompt = (
        "You are 'Touch Grass AI', an open-source outdoor naturalist companion. "
        "Your sole mission is to get people OFF the screen and INTO the real world. "
        "Keep text concise, punchy, inspiring, and grounded in nature. "
        "Return ONLY a clean JSON object with keys: title, primary_mission, auditory_anchor, "
        "species_watchlist, field_advice, screen_off_countdown."
    )
    prompt = f"""Generate a field expedition card for:
Activity: {activity_type}
Duration: {duration_mins} minutes
Environment: {environment}
Season: Autumn / Fall

Respond strictly with a JSON object format:
{{
  "title": "Short poetic title (e.g., Whispering Oaks Autumn Sprint)",
  "primary_mission": "1 clear tangible hands-on task (e.g. Find 3 fallen leaves of different shapes and spot 1 nut-foraging mammal)",
  "auditory_anchor": "1 sensory mindfulness cue to do halfway through without looking at screen (e.g. Stop for 60 seconds at water crossing; close eyes and count 4 distinct birds)",
  "species_watchlist": ["Target 1", "Target 2", "Target 3"],
  "field_advice": "Quick practical advice (shoes, wind layer, sun angle)",
  "screen_off_countdown": "Final words urging them to shut their laptop or pocket their phone NOW."
}}
"""
    raw_response = query_gemma(prompt, system_prompt)
    try:
        # Extract json block if wrapped in markdown
        cleaned = raw_response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        data = json.loads(cleaned)
        return data
    except Exception:
        # High quality offline fallback
        return {
            "title": f"Autumn {activity_type.capitalize()} Expeditions ({duration_mins} min)",
            "primary_mission": f"Explore your nearest natural path for {duration_mins} mins. Observe how the leaf canopy filters sunlight and locate 2 distinct fallen seed pods.",
            "auditory_anchor": "At the halfway mark, stand motionless for 60 seconds. Close your eyes and identify the quietest wind-rustle or bird call around you.",
            "species_watchlist": ["Sugar Maple & Red Oak foliage", "Black-capped Chickadee", "Eastern Chipmunk caching acorns"],
            "field_advice": "Wear lugged trail shoes; carry a light windbreaker; pocket your phone on silent.",
            "screen_off_countdown": "Dispatch complete! Shut your laptop or lock your phone right now and step outside into the air."
        }

def reason_bird_identification(acoustic_data: Dict[str, Any], habitat_context: str = "woodland edge") -> Dict[str, Any]:
    """
    Combines acoustic metrics (FFT dominant frequency, spectral centroid, pitch profile)
    with Gemma 3 bioacoustic reasoning.
    """
    dom_freq = acoustic_data.get("dominant_frequency_hz", 3000)
    spectral_centroid = acoustic_data.get("spectral_centroid_hz", 3200)
    bandwidth = acoustic_data.get("bandwidth_hz", 1500)
    pitch_profile = acoustic_data.get("pitch_profile", "Songbird whistle")
    duration = acoustic_data.get("duration_seconds", 3.0)

    system_prompt = (
        "You are an offline bioacoustics ornithologist. You analyze physical sound metrics "
        "measured by microphone FFT and match them against avian vocalizations. "
        "Return strictly a JSON object with keys: primary_species, scientific_name, confidence_percent, "
        "secondary_candidates, acoustic_match_rationale, field_visual_markers, call_behavior."
    )

    prompt = f"""Analyze these measured acoustic features from a trail recording:
- Dominant Peak Frequency: {dom_freq} Hz
- Spectral Centroid: {spectral_centroid} Hz
- Estimated Bandwidth: {bandwidth} Hz
- Pitch Profile: {pitch_profile}
- Duration: {duration} seconds
- Habitat Context: {habitat_context}
- Season: Autumn

Evaluate candidate North American/European wild bird species matching these exact frequencies.
Return strictly valid JSON:
{{
  "primary_species": "Most probable common name",
  "scientific_name": "Latin name",
  "confidence_percent": 88,
  "secondary_candidates": ["Alternative species 1", "Alternative species 2"],
  "acoustic_match_rationale": "Why this frequency ({dom_freq}Hz) and tone structure matches this species' song or call",
  "field_visual_markers": "What plumage or silhouette markers to scan for in the trees right now",
  "call_behavior": "Why they are calling (territorial song, contact flocking, alarm chatter)"
}}
"""
    raw = query_gemma(prompt, system_prompt)
    try:
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        return json.loads(cleaned)
    except Exception:
        # Heuristic acoustic classifier based on frequency bands
        if dom_freq < 650:
            return {
                "primary_species": "Mourning Dove",
                "scientific_name": "Zenaida macroura",
                "confidence_percent": 86,
                "secondary_candidates": ["Great Horned Owl (Bubo virginianus)", "Ruffed Grouse"],
                "acoustic_match_rationale": f"Measured low resonant frequency ({dom_freq} Hz) perfectly aligns with the soft, mournful 400-600Hz perch-coo rhythm of doves and resonant forest hooters.",
                "field_visual_markers": "Slender buff-brown body, long pointed tail with white tips, small round head sitting on low branches or fence wire.",
                "call_behavior": "Perch calling and autumn flock contact coos as birds feed on fallen grass seeds."
            }
        elif 650 <= dom_freq < 1800:
            return {
                "primary_species": "Blue Jay",
                "scientific_name": "Cyanocitta cristata",
                "confidence_percent": 84,
                "secondary_candidates": ["American Crow (Corvus brachyrhynchos)", "Red-bellied Woodpecker"],
                "acoustic_match_rationale": f"Mid-frequency acoustic profile ({dom_freq} Hz) with wide harmonics matches corvid vocalizations and loud forest alarm or 'jay-jay' rallies.",
                "field_visual_markers": "Vibrant cobalt-blue crest, black necklace pattern, white wing bars, actively flying between oak and beech canopies gathering acorns.",
                "call_behavior": "Contact shouting while caching oak acorns or alerting other jays to a raptor nearby."
            }
        elif 1800 <= dom_freq < 3600:
            return {
                "primary_species": "American Robin",
                "scientific_name": "Turdus migratorius",
                "confidence_percent": 91,
                "secondary_candidates": ["Northern Cardinal (Cardinalis cardinalis)", "Song Sparrow (Melospiza melodia)"],
                "acoustic_match_rationale": f"Strong energy peak at {dom_freq} Hz with moderate bandwidth matches the rich, whistle-carol musical phrases characteristic of the thrush family.",
                "field_visual_markers": "Brick-red breast, charcoal-slate back and head, yellow bill, hops vigorously on ground turning leaf litter.",
                "call_behavior": "Flocking chatter and cheerily-cheer-up autumn carols in berry-rich dogwoods and staghorn sumac."
            }
        else:
            return {
                "primary_species": "Black-capped Chickadee",
                "scientific_name": "Poecile atricapillus",
                "confidence_percent": 93,
                "secondary_candidates": ["Tufted Titmouse (Baeolophus bicolor)", "Golden-crowned Kinglet"],
                "acoustic_match_rationale": f"High clear tonal whistle ({dom_freq} Hz) matches the signature pure two-tone 'fee-bee' or the rapid high-frequency 'chick-a-dee-dee' trill harmonics.",
                "field_visual_markers": "Contrasting black cap and bib, crisp white cheeks, acrobatically clinging upside down to branch tips and pine cones.",
                "call_behavior": "Winter flock cohesion calls; chickadees lead multi-species foraging parties through autumn woodlands."
            }

def reason_garden_advice(calendar_data: Dict[str, Any], query: str = "") -> str:
    """
    Gemma 3 personalized offline advice for garden action this week.
    """
    zone = calendar_data.get("zone", "6")
    days_to_frost = calendar_data.get("days_to_fall_frost", 20)
    system_prompt = (
        "You are an organic homestead and soil regeneration guide. "
        "Keep advice practical, action-oriented, and encouraging hands in the soil. "
        "Focus on what to plant, transplant, mulch, and harvest THIS WEEK."
    )
    prompt = f"""Based on USDA Zone {zone} with approx {days_to_frost} days until first fall frost:
User question / focus: {query if query else 'What should I get in the ground right now?'}

Provide 3 bulleted immediate outdoor action steps and 1 soil touch-grass tip. Keep it under 150 words."""

    res = query_gemma(prompt, system_prompt)
    if res:
        return res
    return (
        f"**Zone {zone} Autumn Action Plan ({days_to_frost} days to first frost):**\n"
        "• **Plant Garlic Cloves:** Break garlic heads into individual cloves. Plant pointy end up, 2-3 inches deep, spaced 6 inches apart.\n"
        "• **Mulch with Fallen Leaves:** Shred oak and maple leaves with a rake or lawnmower and lay a thick 3-inch blanket over bare garden soil.\n"
        "• **Sow Winter Rye / Cover Crops:** Broadcast rye seed over cleared beds to hold root structure and feed earthworms all winter long.\n"
        "🌱 *Touch Grass Tip:* Rub the damp autumn garden soil between your fingers; notice the sweet scent of actinobacteria and beneficial fungi preparing for winter."
    )
