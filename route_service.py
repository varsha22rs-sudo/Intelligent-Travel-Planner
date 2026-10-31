import math
import requests

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

def get_driving_route(start, destination):
    """Return road distance, estimated driving duration and route coordinates."""
    coords = f"{start['longitude']},{start['latitude']};{destination['longitude']},{destination['latitude']}"
    try:
        response = requests.get(f"{OSRM_URL}/{coords}", params={"overview":"full", "geometries":"geojson"}, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get("code") != "Ok" or not data.get("routes"): return None
        route = data["routes"][0]
        return {"distance_km": round(route["distance"]/1000, 2), "duration_minutes": round(route["duration"]/60, 1), "coordinates": route["geometry"]["coordinates"]}
    except requests.RequestException as exc:
        raise RuntimeError("Driving route lookup failed. The public demo service may be busy; retry later.") from exc


def estimate_nonroad_route(
    start,
    destination,
    mode,
    train_rate=1.8,
    flight_rate=5.5,
):
    """Return illustrative train/flight estimates, not live fares."""
    lat1 = math.radians(start["latitude"])
    lon1 = math.radians(start["longitude"])
    lat2 = math.radians(destination["latitude"])
    lon2 = math.radians(destination["longitude"])

    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin((lon2 - lon1) / 2) ** 2
    )

    straight = 6371 * 2 * math.asin(min(1, math.sqrt(h)))

    if mode == "Train":
        distance = straight * 1.20
        hours = max(1, distance / 55 + 1)
        rate = float(train_rate)
        note = (
            "Illustrative rail estimate only; not a live route, fare or schedule."
        )

    elif mode == "Flight":
        distance = straight
        hours = max(1, distance / 650 + 2.5)
        rate = float(flight_rate)
        note = (
            "Illustrative flight estimate only; not a live airline fare or schedule."
        )

    else:
        raise ValueError("Unsupported mode: " + mode)

    return {
        "distance_km": round(distance, 1),
        "duration_hours": round(hours, 2),
        "estimated_cost": round(distance * rate, 2),
        "note": note,
    }
