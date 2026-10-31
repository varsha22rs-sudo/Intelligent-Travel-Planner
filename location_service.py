import requests
import streamlit as st

@st.cache_data(ttl=86400, show_spinner=False)
def find_location(place_name):
    """Find a place in India using OpenStreetMap Nominatim."""
    query = place_name.strip()
    if not query: return None
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "countrycodes": "in", "format": "jsonv2", "limit": 1},
            headers={"User-Agent": "IndiaWideIntelligentTravelPlanner/1.0 (educational project)"},
            timeout=20,
        )
        response.raise_for_status()
        results = response.json()
        if not results: return None
        item = results[0]
        return {"name": item.get("display_name", query), "latitude": float(item["lat"]), "longitude": float(item["lon"])}
    except requests.RequestException as exc:
        raise RuntimeError("Location lookup failed. Check your internet connection and retry.") from exc
