"""India-wide dynamic travel planner UI with destination-order optimization."""

import pandas as pd
import streamlit as st
import folium

from streamlit_folium import st_folium
from location_service import find_location
from route_service import get_driving_route, estimate_nonroad_route
from agents import (
    evaluate_plan,
    calculate_preference_score,
    goal_based_agent,
)
from knowledge_base import ATTRACTIONS
from route_optimizer import optimize_visit_order
from ui_theme import (
    inject_css, hero, pills, stat_strip, route_timeline,
    budget_donut, day_cards, short_name,
)


# --------------------------------------------------
# 1. Page setup
# --------------------------------------------------

st.set_page_config(
    page_title="India-Wide Intelligent Travel Planner",
    page_icon="🧭",
    layout="wide",
)

inject_css()

if "saved_itinerary" not in st.session_state:
    st.session_state.saved_itinerary = None

hero(
    "India-Wide Intelligent Travel Planner",
    "Enter a starting city and the places you want to visit. The selected search "
    "algorithm chooses the best order. Costs and times are estimates, not live quotes.",
)


# --------------------------------------------------
# 2. Sidebar: user input
# --------------------------------------------------

with st.sidebar:
    st.header("Trip details")

    start_text = st.text_input(
        "Starting city and state",
        "Dehradun, Uttarakhand",
    )

    destinations_text = st.text_area(
        "Destinations to visit (one per line or separated by semicolons)",
        "Jaipur, Rajasthan",
        help="Enter each destination once. The optimizer chooses the visit order.",
    )

    modes = st.multiselect(
        "Transport modes to compare",
        ["Car", "Taxi", "Train", "Flight"],
        default=["Car", "Taxi", "Train", "Flight"],
    )

    priority = st.selectbox(
        "Main priority",
        [
            "Lowest estimated cost",
            "Shortest estimated travel time",
        ],
    )

    interests = st.multiselect(
        "What do you enjoy while travelling?",
        ["Nature", "Adventure", "History", "Spirituality", "Sightseeing"],
        default=["Nature", "Sightseeing"],
        help="Choose the types of attractions you prefer.",
    )

    algorithm = st.selectbox(
        "Route optimization algorithm",
        ["A*", "UCS", "BFS", "DFS", "Greedy"],
        index=0,
        help="Choose how the planner explores possible destination orders.",
    )

    st.subheader("Travellers and budget")

    travellers = st.number_input(
        "Number of travellers",
        min_value=1,
        max_value=100,
        value=2,
        step=1,
    )

    days = st.number_input(
        "Trip duration (days)",
        min_value=1,
        max_value=90,
        value=3,
        step=1,
    )

    budget = st.number_input(
        "Total budget (₹)",
        min_value=500,
        max_value=10000000,
        value=20000,
        step=500,
    )

    room_option = st.radio(
        "Accommodation arrangement",
        [
            "One shared room for everyone",
            "Separate room for each traveller",
        ],
    )

    hotel_rate = st.number_input(
        "Estimated hotel price per room/night (₹)",
        min_value=0,
        max_value=100000,
        value=1500,
        step=100,
    )

    food_rate = st.number_input(
        "Estimated food per person/day (₹)",
        min_value=0,
        max_value=20000,
        value=500,
        step=50,
    )

    activity_rate = st.number_input(
        "Estimated attractions/activities per person/day (₹)",
        min_value=0,
        max_value=50000,
        value=300,
        step=50,
    )

    car_rate = st.number_input(
        "Estimated car cost per road km (₹)",
        min_value=0.0,
        max_value=500.0,
        value=12.0,
        step=1.0,
    )

    taxi_rate = st.number_input(
        "Estimated taxi fare per road km (₹)",
        min_value=0.0,
        max_value=500.0,
        value=18.0,
        step=1.0,
    )

    train_rate = st.number_input(
        "Estimated train cost per km (₹)",
        min_value=0.0,
        max_value=100.0,
        value=1.8,
        step=0.1,
    )

    flight_rate = st.number_input(
        "Estimated flight cost per km (₹)",
        min_value=0.0,
        max_value=100.0,
        value=5.5,
        step=0.5,
    )

    generate = st.button(
        "Generate itinerary",
        type="primary",
        use_container_width=True,
    )


# --------------------------------------------------
# 3. Helpers for transport-option estimates
# --------------------------------------------------

def get_transport_options(a, b, selected_modes):
    """Estimate available modes from location a to location b."""
    candidates = []
    road_result = None

    # Get the road route once, then use it for Car and Taxi estimates.
    if any(mode in selected_modes for mode in ("Car", "Taxi")):
        try:
            road_result = get_driving_route(a, b)
        except Exception:
            road_result = None

    for mode in selected_modes:
        try:
            if mode in ("Car", "Taxi"):
                if not road_result:
                    continue

                distance = float(road_result["distance_km"])
                hours = float(road_result["duration_minutes"]) / 60.0
                coordinates = road_result.get("coordinates", [])

                if mode == "Car":
                    cost = distance * float(car_rate)
                    note = (
                        "Estimated car running cost; tolls and parking "
                        "may be extra."
                    )
                else:
                    cost = distance * float(taxi_rate)
                    note = "Estimated taxi fare; actual fares may vary."

            else:
                estimate = estimate_nonroad_route(
                    a,
                    b,
                    mode,
                    train_rate=float(train_rate),
                    flight_rate=float(flight_rate),
                )
                distance = float(estimate["distance_km"])
                hours = float(estimate["duration_hours"])
                cost = float(estimate["estimated_cost"])
                note = estimate.get(
                    "note",
                    "Approximate transport estimate; not a live quote.",
                )
                # Train/flight geometry is only a straight-line visual guide.
                coordinates = []

            if (
                distance < 0
                or hours < 0
                or cost < 0
            ):
                continue

            candidates.append(
                {
                    "from": a["name"],
                    "to": b["name"],
                    "mode": mode,
                    "distance_km": distance,
                    "hours": hours,
                    "cost": cost,
                    "note": note,
                    "coordinates": coordinates,
                }
            )
        except Exception:
            # A missing estimate for one mode should not block other modes.
            continue

    return candidates


def reverse_option(option, from_name, to_name):
    """Reverse an option for the opposite direction of the same city pair."""
    reversed_option = dict(option)
    reversed_option["from"] = from_name
    reversed_option["to"] = to_name

    coordinates = option.get("coordinates", [])
    if coordinates:
        reversed_option["coordinates"] = list(reversed(coordinates))

    return reversed_option


# --------------------------------------------------
# 4. Generate the itinerary after the button is clicked
# --------------------------------------------------

if generate:
    st.session_state.saved_itinerary = None

    if not start_text.strip():
        st.error("Enter a starting city and state.")
    elif not destinations_text.strip():
        st.error("Enter at least one destination.")
    elif not modes:
        st.error("Select at least one transport mode.")
    else:
        destination_names = [
            item.strip()
            for line in destinations_text.splitlines()
            for item in line.split(";")
            if item.strip()
        ]

        try:
            with st.spinner(
                "Finding locations and estimating transport between "
                "destination pairs..."
            ):
                start = find_location(start_text)

                if not start:
                    raise ValueError(
                        f"Starting place not found: {start_text}. "
                        "Try including the state name."
                    )

                locations = [start]
                missing_destinations = []
                seen_names = {start["name"].strip().casefold()}

                for name in destination_names:
                    place = find_location(name)

                    if place is None:
                        missing_destinations.append(name)
                        continue

                    normalized_name = place["name"].strip().casefold()

                    # Do not pass duplicate locations to the optimizer.
                    if normalized_name in seen_names:
                        continue

                    seen_names.add(normalized_name)
                    locations.append(place)

                if missing_destinations:
                    st.warning(
                        "These destinations could not be found and were "
                        "skipped: " + ", ".join(missing_destinations)
                    )

                if len(locations) < 2:
                    raise ValueError(
                        "At least one valid destination different from "
                        "the starting city is required."
                    )

                if len(locations) > 9:
                    raise ValueError(
                        "For this version, enter at most 8 destinations "
                        "plus the starting city. Pairwise route estimation "
                        "requires many transport lookups and search states."
                    )

                # --------------------------------------------------
                # 4A. Build transport options for every city pair
                # --------------------------------------------------
                # This is what lets the optimizer change the destination order.
                # The first location remains the fixed starting city.
                leg_options = {}
                all_comparisons = []
                location_by_name = {
                    location["name"]: location for location in locations
                }

                total_pairs = len(locations) * (len(locations) - 1) // 2
                completed_pairs = 0
                progress = st.progress(0, text="Preparing city-to-city options...")

                for i in range(len(locations)):
                    for j in range(i + 1, len(locations)):
                        a = locations[i]
                        b = locations[j]

                        forward_candidates = get_transport_options(a, b, modes)

                        # Use the same pairwise estimates in reverse to avoid
                        # doubling external routing requests. Road coordinates
                        # are reversed for the opposite direction; actual roads
                        # and times can differ slightly by direction.
                        backward_candidates = [
                            reverse_option(option, b["name"], a["name"])
                            for option in forward_candidates
                        ]

                        if forward_candidates:
                            leg_options[(a["name"], b["name"])] = (
                                forward_candidates
                            )
                            all_comparisons.extend(forward_candidates)

                        if backward_candidates:
                            leg_options[(b["name"], a["name"])] = (
                                backward_candidates
                            )
                            all_comparisons.extend(backward_candidates)

                        completed_pairs += 1
                        progress.progress(
                            completed_pairs / max(total_pairs, 1),
                            text=(
                                f"Estimating transport options: "
                                f"{completed_pairs}/{total_pairs} city pairs"
                            ),
                        )

                progress.empty()

                # --------------------------------------------------
                # 4B. Optimize the destination visit order
                # --------------------------------------------------
                # "hours" is accepted by both the earlier and corrected
                # route_optimizer.py versions; it means optimize travel time.
                metric = (
                    "cost"
                    if priority == "Lowest estimated cost"
                    else "hours"
                )

                optimization = optimize_visit_order(
                    locations=locations,
                    leg_options=leg_options,
                    algorithm=algorithm,
                    metric=metric,
                )

                optimized_names = optimization["path"]
                optimized_locations = [
                    location_by_name[name] for name in optimized_names
                ]
                legs = optimization["legs"]

                # Add a safe fallback for older optimizer versions if a field
                # is absent from a selected leg.
                for leg in legs:
                    leg.setdefault("note", "Estimated transport option.")
                    leg.setdefault("coordinates", [])
                    leg.setdefault("distance_km", 0.0)

                # Flag the exact selected mode for each optimized route leg.
                selected_keys = {
                    (leg["from"], leg["to"], leg["mode"])
                    for leg in legs
                }

                # Calculate comparison scores separately for each directed pair.
                comparisons_by_pair = {}
                for option in all_comparisons:
                    pair = (option["from"], option["to"])
                    comparisons_by_pair.setdefault(pair, []).append(option)

                for pair, options in comparisons_by_pair.items():
                    costs = [float(option["cost"]) for option in options]
                    times = [float(option["hours"]) for option in options]
                    min_cost, max_cost = min(costs), max(costs)
                    min_time, max_time = min(times), max(times)

                    for option in options:
                        cost_score = (
                            100.0
                            if max_cost == min_cost
                            else 100.0 * (max_cost - option["cost"])
                            / (max_cost - min_cost)
                        )
                        time_score = (
                            100.0
                            if max_time == min_time
                            else 100.0 * (max_time - option["hours"])
                            / (max_time - min_time)
                        )
                        option["utility"] = round(
                            cost_score if metric == "cost" else time_score,
                            1,
                        )
                        option["leg"] = (
                            f"{option['from']} → {option['to']}"
                        )
                        option["recommended"] = (
                            option["from"],
                            option["to"],
                            option["mode"],
                        ) in selected_keys

                # --------------------------------------------------
                # 4C. Calculate total trip expenses
                # --------------------------------------------------
                travellers_count = int(travellers)
                trip_days = int(days)

                transport_cost = (
                    sum(float(leg["cost"]) for leg in legs)
                    * travellers_count
                )

                nights = max(0, trip_days - 1)

                if room_option == "Separate room for each traveller":
                    rooms = travellers_count
                else:
                    rooms = 1

                hotel_cost = nights * rooms * float(hotel_rate)
                food_cost = (
                    travellers_count * trip_days * float(food_rate)
                )
                activity_cost = (
                    travellers_count * trip_days * float(activity_rate)
                )

                total = (
                    transport_cost
                    + hotel_cost
                    + food_cost
                    + activity_cost
                )

                total_hours = sum(float(leg["hours"]) for leg in legs)
                total_distance = sum(
                    float(leg.get("distance_km", 0)) for leg in legs
                )

                # Match selected interests against sample attractions for the
                # destination cities that appear in the knowledge base.
                destination_city_names = {
                    str(place.get("name", "")).split(",")[0].strip().lower()
                    for place in optimized_locations[1:]
                }
                relevant_attractions = [
                    attraction
                    for attraction in ATTRACTIONS
                    if str(attraction.get("city", "")).strip().lower()
                    in destination_city_names
                ]
                
                if relevant_attractions:
                    preference_score = calculate_preference_score(
                        relevant_attractions,
                        interests,
                    )
                    preference_status = "evaluated"
                else:
                    preference_score = None
                    preference_status = "unavailable"


                evaluation = evaluate_plan(
                    total_cost=total,
                    budget=float(budget),
                    travel_hours=total_hours,
                    days=trip_days,
                    transport_cost=transport_cost,
                    hotel_cost=hotel_cost,
                    food_cost=food_cost,
                    attraction_cost=activity_cost,
                    preference_score=preference_score,
                )
                goal_result = goal_based_agent(
                    current_location=optimized_names[0],
                    destinations=[
                        location["name"]
                        for location in locations[1:]
                    ],
                    route=optimized_names,
                    total_cost=total,
                    travel_hours=total_hours,
                    budget=float(budget),
                    days=trip_days,
                )

                st.session_state.saved_itinerary = {
                    "locations": optimized_locations,
                    "legs": legs,
                    "all_comparisons": all_comparisons,
                    "transport_cost": transport_cost,
                    "hotel_cost": hotel_cost,
                    "food_cost": food_cost,
                    "activity_cost": activity_cost,
                    "total": total,
                    "hours": total_hours,
                    "distance": total_distance,
                    "evaluation": evaluation,
                    "travellers": travellers_count,
                    "days": trip_days,
                    "budget": float(budget),
                    "room_option": room_option,
                    "rooms": rooms,
                    "nights": nights,
                    "priority": priority,
                    "algorithm": algorithm,
                    "interests": interests,
                    "preference_score": preference_score,
                    "optimized_metric": metric,
                    "optimization": optimization,
                    "goal_result": goal_result,
                }

        except Exception as exc:
            st.error(f"Unable to generate the itinerary: {exc}")


# --------------------------------------------------
# 5. Display saved results outside the button block
# --------------------------------------------------

def build_route_map(saved_data):
    """Folium map with numbered stops, road routes and dashed guides."""
    stops = saved_data["locations"]
    route_map = folium.Map(
        location=[float(stops[0]["latitude"]), float(stops[0]["longitude"])],
        zoom_start=5,
    )

    points = []
    for index, place in enumerate(stops):
        lat, lon = float(place["latitude"]), float(place["longitude"])
        points.append([lat, lon])
        folium.Marker(
            [lat, lon],
            tooltip=f"Stop {index + 1}",
            popup=place["name"],
        ).add_to(route_map)

    by_name = {place["name"]: place for place in stops}

    for leg in saved_data["legs"]:
        coordinates = leg.get("coordinates", [])
        if coordinates:
            folium.PolyLine(
                [[float(la), float(lo)] for lo, la in coordinates],
                weight=4,
                tooltip=f"{leg['from']} to {leg['to']} ({leg['mode']})",
            ).add_to(route_map)
        else:
            a, b = by_name.get(leg["from"]), by_name.get(leg["to"])
            if a and b:
                folium.PolyLine(
                    [
                        [float(a["latitude"]), float(a["longitude"])],
                        [float(b["latitude"]), float(b["longitude"])],
                    ],
                    weight=3,
                    dash_array="5,8",
                    tooltip=f"Straight-line guide for {leg['mode']}; not the actual route",
                ).add_to(route_map)

    if len(points) > 1:
        route_map.fit_bounds(points)
    return route_map


saved = st.session_state.saved_itinerary

if saved:
    evaluation = saved["evaluation"]
    goal_result = saved["goal_result"]
    stops = saved["locations"]
    over_budget = saved["total"] > saved["budget"]

    # ---- Title row -------------------------------------------------
    st.markdown("## Your Travel Plan")
    pills(
        [
            f"{saved['days']} days",
            f"{len(stops) - 1} destinations",
            f"{saved['travellers']} travellers",
            f"₹{saved['total']:,.0f} estimated",
        ]
    )

    if goal_result["success"]:
        st.success("Goal check: " + goal_result["reason"])
    else:
        st.warning("Goal check: " + goal_result["reason"])

    # ---- Route timeline + map -------------------------------------
    left, right = st.columns([1, 1.7], gap="medium")

    with left:
        route_timeline(stops, saved["legs"])

    with right:
        st.markdown('<div class="card"><h3>Route map</h3>', unsafe_allow_html=True)
        st_folium(
            build_route_map(saved),
            use_container_width=True,
            height=450,
            key="dynamic_india_map",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Stat strip -----------------------------------------------
    stat_strip(
        [
            (f"{saved['days']} days", "Total duration"),
            (f"{len(stops) - 1} stops", "Destinations"),
            (f"{saved['distance']:,.0f} km", "Total distance"),
            (f"{saved['hours']:.1f} h", "Travel time"),
            (f"₹{saved['total']:,.0f}", "Estimated total"),
            (f"₹{saved['budget'] - saved['total']:,.0f}", "Budget remaining"),
        ]
    )
    st.write("")

    # ---- Budget | Why this plan | Days ----------------------------
    col_a, col_b, col_c = st.columns([1, 1.1, 1.1], gap="medium")

    with col_a:
        budget_donut(
            {
                "Transport": saved["transport_cost"],
                "Hotels": saved["hotel_cost"],
                "Food": saved["food_cost"],
                "Activities": saved["activity_cost"],
            },
            saved["budget"],
        )

    with col_b:
        metric_label = (
            "lowest cost" if saved["optimized_metric"] == "cost" else "shortest travel time"
        )
        status = (
            "Over budget. Try fewer stops, cheaper transport or lower estimates."
            if over_budget
            else "Within your budget."
        )
        preference_line = (
            f"Interest match: {evaluation['preference_score']}/100."
            if evaluation["preference_score"] is not None
            else "Interest match unavailable: no sample attractions for these cities."
        )
        st.markdown(
            f'<div class="card soft-green"><h3>Why this plan</h3>'
            f"<p><b>{saved['algorithm']}</b> ordered the stops for <b>{metric_label}</b>.</p>"
            f"<p>{status}</p>"
            f"<p>Utility score: <b>{evaluation['utility']}/100</b><br>{preference_line}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(evaluation.get("utility_explanation", ""))

    with col_c:
        day_cards(stops, saved["days"], saved["legs"])

    # ---- Accommodation note ---------------------------------------
    st.markdown(
        f'<div class="card"><h3>Accommodation</h3>'
        f"{saved['room_option']}: {saved['rooms']} room(s) per night for "
        f"{saved['nights']} night(s). Estimated hotel total: "
        f"₹{saved['hotel_cost']:,.0f}.</div>",
        unsafe_allow_html=True,
    )

    # ---- Detail tables (collapsed to keep the page clean) ----------
    with st.expander("Selected route legs"):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "From": short_name(leg["from"]),
                        "To": short_name(leg["to"]),
                        "Mode": leg["mode"],
                        "Distance (km)": round(float(leg.get("distance_km", 0)), 1),
                        "Time (hours)": round(float(leg["hours"]), 2),
                        "Cost for all travellers (₹)": round(
                            float(leg["cost"]) * saved["travellers"]
                        ),
                        "Notes": leg.get("note", ""),
                    }
                    for leg in saved["legs"]
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Transport comparison for every city pair"):
        rows = [
            {
                "Route": option["leg"],
                "Mode": option["mode"],
                "Distance (km)": round(float(option["distance_km"]), 1),
                "Time (hours)": round(float(option["hours"]), 2),
                "Cost for all travellers (₹)": round(
                    float(option["cost"]) * saved["travellers"]
                ),
                "Priority score": option.get("utility", 0),
                "Selected": "Yes" if option.get("recommended") else "",
                "Notes": option.get("note", ""),
            }
            for option in saved["all_comparisons"]
        ]
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No transport comparison options were available.")

    st.caption(
        "Costs and travel times are approximate. Road routes depend on "
        "OpenStreetMap/OSRM availability. Train and flight estimates are not "
        "live schedules or ticket prices."
    )

else:
    st.info(
        "Enter a starting city and at least one destination, choose transport "
        "modes, set your budget, and click Generate itinerary."
    )
    st.markdown(
        "Example: start `Dehradun, Uttarakhand`; destinations "
        "`Jaipur, Rajasthan; Agra, Uttar Pradesh; Goa`."
    )