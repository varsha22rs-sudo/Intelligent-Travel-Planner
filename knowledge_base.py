"""Sample knowledge base for the Uttarakhand travel planning agent.

All fares, times, distances, hotel prices and fees are illustrative demo values,
not live travel data. Route costs are per person, per one-way journey.
Hotel prices are per room per night.
"""

CITIES = {
    "Dehradun": {"state": "Uttarakhand", "type": "city", "lat": 30.3165, "lon": 78.0322},
    "Mussoorie": {"state": "Uttarakhand", "type": "hill station", "lat": 30.4598, "lon": 78.0644},
    "Rishikesh": {"state": "Uttarakhand", "type": "adventure and spiritual destination", "lat": 30.0869, "lon": 78.2676},
    "Haridwar": {"state": "Uttarakhand", "type": "spiritual destination", "lat": 29.9457, "lon": 78.1642},
    "Haldwani": {"state": "Uttarakhand", "type": "city", "lat": 29.2183, "lon": 79.5130},
    "Nainital": {"state": "Uttarakhand", "type": "hill station", "lat": 29.3919, "lon": 79.4542},
    "Almora": {"state": "Uttarakhand", "type": "hill town", "lat": 29.5971, "lon": 79.6591},
}

# Routes are treated as bidirectional in this demonstration.
ROUTES = [
    {"from": "Dehradun", "to": "Mussoorie", "transport": "Bus", "cost": 100, "time": 1.5, "distance": 35},
    {"from": "Dehradun", "to": "Rishikesh", "transport": "Bus", "cost": 100, "time": 1.5, "distance": 45},
    {"from": "Dehradun", "to": "Haridwar", "transport": "Bus", "cost": 120, "time": 1.5, "distance": 55},
    {"from": "Rishikesh", "to": "Haridwar", "transport": "Bus", "cost": 60, "time": 0.75, "distance": 25},
    {"from": "Haridwar", "to": "Haldwani", "transport": "Bus", "cost": 400, "time": 6, "distance": 200},
    {"from": "Haldwani", "to": "Nainital", "transport": "Bus", "cost": 80, "time": 1, "distance": 35},
    {"from": "Mussoorie", "to": "Rishikesh", "transport": "Taxi", "cost": 800, "time": 3, "distance": 75},
    {"from": "Nainital", "to": "Almora", "transport": "Bus", "cost": 150, "time": 2, "distance": 65},
    {"from": "Haldwani", "to": "Almora", "transport": "Bus", "cost": 180, "time": 3, "distance": 90},
]

ATTRACTIONS = [
    {"name": "Kempty Falls", "city": "Mussoorie", "category": "nature", "entry_fee": 0, "visit_time": 2},
    {"name": "Mall Road", "city": "Mussoorie", "category": "sightseeing", "entry_fee": 0, "visit_time": 1.5},
    {"name": "Triveni Ghat", "city": "Rishikesh", "category": "spiritual", "entry_fee": 0, "visit_time": 1},
    {"name": "Lakshman Jhula area", "city": "Rishikesh", "category": "sightseeing", "entry_fee": 0, "visit_time": 1.5},
    {"name": "Har Ki Pauri", "city": "Haridwar", "category": "spiritual", "entry_fee": 0, "visit_time": 1.5},
    {"name": "Naini Lake", "city": "Nainital", "category": "nature", "entry_fee": 0, "visit_time": 2},
    {"name": "Bright End Corner", "city": "Almora", "category": "nature", "entry_fee": 0, "visit_time": 1},
]

HOTELS = [
    {"name": "Budget Stay A", "city": "Mussoorie", "category": "budget", "price_per_night": 1200},
    {"name": "Budget Stay B", "city": "Rishikesh", "category": "budget", "price_per_night": 1000},
    {"name": "Budget Stay C", "city": "Haridwar", "category": "budget", "price_per_night": 900},
    {"name": "Budget Stay D", "city": "Nainital", "category": "budget", "price_per_night": 1500},
    {"name": "Budget Stay E", "city": "Haldwani", "category": "budget", "price_per_night": 1000},
    {"name": "Budget Stay F", "city": "Almora", "category": "budget", "price_per_night": 1100},
]

MEAL_COST_PER_PERSON_PER_DAY = 400
DEFAULT_PREFERENCE_CATEGORIES = ["nature", "sightseeing"]
