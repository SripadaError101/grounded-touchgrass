from datetime import datetime, date
from typing import Dict, Any, List

HARDINESS_ZONES = {
    "3": {"name": "Zone 3 (Sub-arctic / Northern Plains)", "last_spring": "05-20", "first_fall": "09-15", "min_temp": "-40°F"},
    "4": {"name": "Zone 4 (Upper Midwest / Northern Rockies)", "last_spring": "05-15", "first_fall": "09-25", "min_temp": "-30°F"},
    "5": {"name": "Zone 5 (Midwest / New England / Central)", "last_spring": "05-01", "first_fall": "10-15", "min_temp": "-20°F"},
    "6": {"name": "Zone 6 (Mid-Atlantic / Ohio Valley / Pacific NW)", "last_spring": "04-20", "first_fall": "10-25", "min_temp": "-10°F"},
    "7": {"name": "Zone 7 (Upper South / Mid-Atlantic / Coastal NW)", "last_spring": "04-05", "first_fall": "11-05", "min_temp": "0°F"},
    "8": {"name": "Zone 8 (Deep South / Pacific NW Coast / Texas)", "last_spring": "03-15", "first_fall": "11-20", "min_temp": "10°F"},
    "9": {"name": "Zone 9 (Gulf Coast / Central Florida / SW Deserts)", "last_spring": "02-15", "first_fall": "12-15", "min_temp": "20°F"},
    "10": {"name": "Zone 10 (South Florida / SoCal / Hawaii / Tropics)", "last_spring": "01-15", "first_fall": "12-31", "min_temp": "30°F"},
}

CROPS_CATALOG = [
    {
        "name": "Hardneck & Softneck Garlic",
        "category": "Alliums",
        "ideal_window": "Fall (4-6 weeks before ground freezes)",
        "hardiness": "Extremely Cold Hardy (requires cold vernalization)",
        "instructions": "Plant individual cloves pointy end up, 2-3 inches deep, 6 inches apart. Mulch heavily with 4-6 inches of clean straw or shredded leaves.",
        "frost_strategy": "Overwinters under soil; sprouts in early spring."
    },
    {
        "name": "Winter Spinach (Bloomsdale / Giant Winter)",
        "category": "Greens",
        "ideal_window": "Late Summer to Mid Autumn",
        "hardiness": "Hardy down to 15°F (-9°C)",
        "instructions": "Direct sow seeds 1/2 inch deep. Keep moist. Thin to 4 inches. Sugars concentrate with frost, making fall spinach intensely sweet.",
        "frost_strategy": "Survives heavy frosts under simple row cover or low tunnel."
    },
    {
        "name": "Winter Rye & Hairy Vetch (Cover Crop)",
        "category": "Soil Regeneration",
        "ideal_window": "Early to Mid Autumn",
        "hardiness": "Winter Hardy",
        "instructions": "Broadcast seed over cleared garden beds, rake into top 1 inch of soil, and tamp down. Protects soil from winter compaction and erosion.",
        "frost_strategy": "Suppresses weeds all winter; turn into green manure in spring."
    },
    {
        "name": "Overwintering Kale (Lacinato / Winterbor)",
        "category": "Brassicas",
        "ideal_window": "Transplant established starts in Autumn",
        "hardiness": "Extremely Hardy (sweetens below 28°F)",
        "instructions": "Pick lower leaves progressively. Protect root crowns with thick leaf mulch.",
        "frost_strategy": "Can produce harvestable greens throughout winter in Zones 6-9."
    },
    {
        "name": "Spring Flowering Bulbs (Daffodils, Tulips, Alliums)",
        "category": "Perennials / Pollinator Habitat",
        "ideal_window": "Mid to Late Autumn",
        "hardiness": "Bulb Perennial",
        "instructions": "Plant at depth equal to 3x bulb height in well-drained soil. Top with compost and mulch.",
        "frost_strategy": "Requires winter cold chill to break dormancy for spring blooming."
    },
    {
        "name": "Mache / Corn Salad & Claytona (Miner's Lettuce)",
        "category": "Salad Greens",
        "ideal_window": "Autumn sowing",
        "hardiness": "Ultra-hardy (grows at near-freezing temps)",
        "instructions": "Sow in cold frame or sheltered bed. Germinates readily in cool soil.",
        "frost_strategy": "Harvest fresh crisp winter salads through snow."
    }
]

def calculate_garden_calendar(zone_key: str = "6", custom_frost_date: str = None) -> Dict[str, Any]:
    """
    Calculates frost status, days remaining, seasonal phase, and recommended actions.
    """
    zone_info = HARDINESS_ZONES.get(zone_key, HARDINESS_ZONES["6"])
    today = date.today()
    current_year = today.year

    if custom_frost_date:
        try:
            fall_frost = datetime.strptime(f"{current_year}-{custom_frost_date}", "%Y-%m-%d").date()
        except ValueError:
            fall_frost = datetime.strptime(f"{current_year}-{zone_info['first_fall']}", "%Y-%m-%d").date()
    else:
        fall_frost = datetime.strptime(f"{current_year}-{zone_info['first_fall']}", "%Y-%m-%d").date()

    spring_frost = datetime.strptime(f"{current_year}-{zone_info['last_spring']}", "%Y-%m-%d").date()

    days_to_frost = (fall_frost - today).days

    if days_to_frost > 45:
        season_status = "Late Summer / Early Autumn Transition"
        urgency = "Moderate: Time to establish autumn root crops and leafy brassicas."
    elif 15 <= days_to_frost <= 45:
        season_status = "Prime Fall Planting & Overwintering Window"
        urgency = "High Action: Plant garlic, spring bulbs, cover crops, and mulch exposed beds now."
    elif 0 <= days_to_frost < 15:
        season_status = "Imminent Frost Warning"
        urgency = "Critical: Harvest remaining summer tender crops (tomatoes, peppers, basil). Cover sensitive greens."
    else:
        season_status = "Frost Season Active (Ground Transition to Winter)"
        urgency = "Winter Maintenance: Overwintering crops in ground, mulch replenishment, seed catalog planning."

    return {
        "zone": zone_key,
        "zone_name": zone_info["name"],
        "minimum_temp": zone_info["min_temp"],
        "today_date": today.isoformat(),
        "today_week": today.isocalendar()[1],
        "first_fall_frost": fall_frost.isoformat(),
        "days_to_fall_frost": days_to_frost,
        "season_status": season_status,
        "urgency": urgency,
        "recommended_crops": CROPS_CATALOG,
        "soil_touch_grass_tasks": [
            "Dig trenches and tuck in garlic cloves 3 inches deep beneath fallen leaves.",
            "Gather crunchy autumn oak and maple leaves to shred as carbon-rich protective bed mulch.",
            "Harvest remaining green tomatoes to ripen on newspaper indoors; harvest frost-sweetened kale.",
            "Take a soil sample in a mason jar with water to observe your sand/silt/clay stratification."
        ]
    }
