"""Hotel-room estimate helpers."""
def estimate_rooms(travellers, room_option):
    return int(travellers) if room_option == "Separate room for each traveller" else 1

def estimate_accommodation(days, travellers, room_option, price_per_room_night):
    nights = max(0, int(days)-1)
    rooms = estimate_rooms(travellers, room_option)
    return {"nights": nights, "rooms": rooms, "cost": nights*rooms*float(price_per_room_night)}
