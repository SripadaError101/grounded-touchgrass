import math
import random
from typing import Dict, Any, List

def generate_trail_route(
    center_lat: float = 40.7829,  # Default Central Park / Autumn Woodland baseline
    center_lng: float = -73.9654,
    distance_km: float = 5.0,
    route_type: str = "run",      # "run", "hike", "birding_walk"
    foliage_focus: str = "high"   # "high", "moderate", "waterfront"
) -> Dict[str, Any]:
    """
    Generates a realistic scenic loop trail around center coordinates,
    with fall foliage canopy waypoints, elevation profile, and exportable GPX.
    """
    # Calculate approximate loop radius in degrees (~111km per degree latitude)
    # circumference = 2 * pi * radius -> radius = distance / (2 * pi)
    radius_km = distance_km / (2 * math.pi)
    radius_deg_lat = radius_km / 111.0
    radius_deg_lng = radius_deg_lat / math.cos(math.radians(center_lat))

    num_waypoints = max(8, int(distance_km * 2.5))
    waypoints = []
    foliage_species_pool = [
        ("Sugar Maple Canopy", "Brilliant Scarlet & Electric Orange", 95),
        ("Golden Birch & Beech Grove", "Vibrant Golden Yellow & Bronze", 88),
        ("Red Oak Ridge", "Deep Russet & Burgundy", 82),
        ("Sassafras & Sweetgum Hollow", "Multi-colored Purple, Red & Amber", 91),
        ("Creek Crossing & Hemlock Shade", "Evergreen Contrast with Floating Golden Leaves", 85),
        ("Summit Overlook", "Panoramic Valley Canopy View", 98)
    ]

    base_elevation = 45.0
    total_elevation_gain = 0.0
    elevations = []

    # Generate slightly wobbled circular loop with realistic terrain
    angle_step = (2 * math.pi) / num_waypoints
    current_elev = base_elevation

    for i in range(num_waypoints):
        angle = i * angle_step
        # Add natural organic noise to route
        wobble_r = 1.0 + 0.25 * math.sin(3 * angle) + 0.15 * math.cos(2 * angle)
        lat = center_lat + (radius_deg_lat * wobble_r) * math.cos(angle)
        lng = center_lng + (radius_deg_lng * wobble_r) * math.sin(angle)

        # Elevation variation
        elev_delta = (math.sin(angle * 2) * 15.0) + (math.cos(angle * 3) * 8.0)
        elev = max(10.0, base_elevation + elev_delta)
        if i > 0:
            diff = elev - elevations[-1]
            if diff > 0:
                total_elevation_gain += diff
        elevations.append(round(elev, 1))

        foliage_pick = foliage_species_pool[i % len(foliage_species_pool)]

        waypoints.append({
            "step": i + 1,
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "elevation_m": round(elev, 1),
            "foliage_feature": foliage_pick[0],
            "foliage_palette": foliage_pick[1],
            "foliage_intensity_percent": foliage_pick[2],
            "landmark": f"Waypoint {i+1}: {foliage_pick[0]}"
        })

    # Close the loop
    waypoints.append({
        "step": num_waypoints + 1,
        "lat": waypoints[0]["lat"],
        "lng": waypoints[0]["lng"],
        "elevation_m": waypoints[0]["elevation_m"],
        "foliage_feature": "Trailhead / Finish Loop",
        "foliage_palette": "Cool Down Under Autumn Canopy",
        "foliage_intensity_percent": 90,
        "landmark": "Trailhead & Meetup Hub"
    })

    # Average foliage index
    avg_foliage = round(sum(w["foliage_intensity_percent"] for w in waypoints) / len(waypoints), 1)

    # Pace & duration
    if route_type == "run":
        est_pace_min_per_km = 5.5  # 5:30/km
        surface = "Packed Dirt & Woodchip Trailways"
        gear_tip = "Trail running shoes with lugged grip for wet fallen leaves."
    elif route_type == "hike":
        est_pace_min_per_km = 12.0 # 12 min/km
        surface = "Single-track Trail with Rock/Root Crossings"
        gear_tip = "Lightweight trail runners or day hiking boots."
    else: # birding_walk
        est_pace_min_per_km = 22.0 # Slow mindful pace
        surface = "Soft Forest Path & Boardwalks"
        gear_tip = "Binoculars (8x42 recommended), notebook, quiet jacket."

    duration_mins = int(distance_km * est_pace_min_per_km)

    # Generate GPX format
    gpx_content = build_gpx_xml(waypoints, f"Foliage Loop {distance_km}km")

    return {
        "title": f"Autumn Foliage {distance_km}km {route_type.capitalize()} Loop",
        "distance_km": round(distance_km, 1),
        "distance_miles": round(distance_km * 0.621371, 2),
        "estimated_duration_minutes": duration_mins,
        "elevation_gain_meters": round(total_elevation_gain, 1),
        "foliage_canopy_index": f"{avg_foliage}% Peak Color",
        "surface_type": surface,
        "gear_tip": gear_tip,
        "waypoints": waypoints,
        "gpx_data": gpx_content,
        "run_club_prompt": (
            f"Set up a group meetup! Warm up for 5 mins under the Sugar Maples, "
            f"run at conversational pace through the Beech Grove, and gather at the finish for post-run cider."
        )
    }

def build_gpx_xml(waypoints: List[Dict[str, Any]], track_name: str) -> str:
    """
    Constructs a standard GPX 1.1 XML string compatible with Garmin, Apple Watch, Strava, OsmAnd.
    """
    trkpts = []
    for pt in waypoints:
        trkpts.append(
            f'      <trkpt lat="{pt["lat"]}" lon="{pt["lng"]}">'
            f'\n        <ele>{pt["elevation_m"]}</ele>'
            f'\n        <name>{pt["foliage_feature"]}</name>'
            f'\n      </trkpt>'
        )
    trkpts_str = "\n".join(trkpts)

    gpx = f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Grounded TouchGrass AI - Open Source" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata>
    <name>{track_name}</name>
    <desc>Offline-generated scenic route for screen-free outdoor exploration</desc>
  </metadata>
  <trk>
    <name>{track_name}</name>
    <trkseg>
{trkpts_str}
    </trkseg>
  </trk>
</gpx>"""
    return gpx
