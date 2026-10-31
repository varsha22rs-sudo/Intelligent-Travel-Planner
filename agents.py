
"""Agents for evaluating and planning trips."""


def calculate_trip_estimate(
    transport_cost,
    hotel_cost,
    food_cost,
    attraction_cost,
):
    transport_cost = float(transport_cost)
    hotel_cost = float(hotel_cost)
    food_cost = float(food_cost)
    attraction_cost = float(attraction_cost)

    total = (
        transport_cost
        + hotel_cost
        + food_cost
        + attraction_cost
    )

    return {
        "transport_cost": transport_cost,
        "hotel_cost": hotel_cost,
        "food_cost": food_cost,
        "attraction_cost": attraction_cost,
        "total_cost": total,
    }


def check_destination_eligibility(
    total_cost,
    budget,
    travel_hours,
    days,
):
    """Check whether a proposed trip satisfies basic constraints."""

    total_cost = float(total_cost)
    budget = float(budget)
    travel_hours = float(travel_hours)
    days = int(days)

    if budget <= 0:
        return {
            "eligible": False,
            "reason": "Budget must be greater than zero.",
        }

    if days <= 0:
        return {
            "eligible": False,
            "reason": "Trip duration must be at least one day.",
        }

    if total_cost < 0 or travel_hours < 0:
        return {
            "eligible": False,
            "reason": "Cost and travel time cannot be negative.",
        }

    if total_cost > budget:
        return {
            "eligible": False,
            "reason": "Estimated trip cost exceeds your budget.",
        }

    if travel_hours > days * 24:
        return {
            "eligible": False,
            "reason": "Estimated travel time exceeds the trip duration.",
        }

    return {
        "eligible": True,
        "reason": "Trip meets the budget and duration constraints.",
    }


def evaluate_plan(
    total_cost,
    budget,
    travel_hours,
    days,
    transport_cost,
    hotel_cost,
    food_cost,
    attraction_cost,
    cost_weight=0.5,
    time_weight=0.3,
    preference_weight=0.2,
    preference_score=100,
):
    """Evaluate a trip using cost, time, and user preferences."""

    total_cost = float(total_cost)
    budget = float(budget)
    travel_hours = float(travel_hours)
    days = int(days)

    if budget <= 0 or days <= 0:
        raise ValueError("Budget and trip duration must be positive.")

    weights = [cost_weight, time_weight, preference_weight]

    if any(weight < 0 for weight in weights):
        raise ValueError("Utility weights cannot be negative.")

    total_weight = sum(weights)

    if total_weight <= 0:
        raise ValueError("At least one utility weight must be positive.")

    cost_weight = float(cost_weight)
    time_weight = float(time_weight)
    preference_weight = float(preference_weight)

    available_hours = days * 24

    preference_available = preference_score is not None

    if preference_available:
        preference_score = float(preference_score)

        if not 0 <= preference_score <= 100:
            raise ValueError(
                "Preference score must be between 0 and 100."
            )
    else:
        preference_score = 0.0

    eligibility = check_destination_eligibility(
        total_cost=total_cost,
        budget=budget,
        travel_hours=travel_hours,
        days=days,
    )

    budget_score = max(
        0.0,
        min(100.0, 100 * (1 - total_cost / budget)),
    )

    time_score = max(
        0.0,
        min(100.0, 100 * (1 - travel_hours / available_hours)),
    )

    active_preference_weight = (
        preference_weight if preference_available else 0.0
    )

    active_total_weight = (
        cost_weight + time_weight + active_preference_weight
    )

    if active_total_weight <= 0:
        raise ValueError(
            "At least one active utility weight must be positive."
        )

    utility = round(
        (
            cost_weight * budget_score
            + time_weight * time_score
            + active_preference_weight * preference_score
        ) / active_total_weight,
        1,
    )

    if not eligibility["eligible"]:
        utility = 0.0

    if preference_available:
        preference_explanation = (
            f"Preference score: {round(preference_score, 1)}/100 "
            f"(weight {preference_weight}). "
        )
    else:
        preference_explanation = (
            "Preference score unavailable because no matching sample "
            "attractions were found; utility was calculated using "
            "cost and time only. "
        )

    return {
        "within_budget": total_cost <= budget,
        "within_time": travel_hours <= available_hours,
        "eligible": eligibility["eligible"],
        "utility": utility,
        "budget_score": round(budget_score, 1),
        "time_score": round(time_score, 1),
        "preference_score": (
            round(preference_score, 1)
            if preference_available
            else None
        ),
        "reason": eligibility["reason"],
        "utility_explanation": (
            f"Budget score: {round(budget_score, 1)}/100 "
            f"(weight {cost_weight}). "
            f"Time score: {round(time_score, 1)}/100 "
            f"(weight {time_weight}). "
            f"{preference_explanation}"
            f"Final weighted utility: {utility}/100."
        ),
        "transport_cost": float(transport_cost),
        "hotel_cost": float(hotel_cost),
        "food_cost": float(food_cost),
        "attraction_cost": float(attraction_cost),
    }



def goal_based_agent(
    current_location,
    destinations,
    route,
    total_cost,
    travel_hours,
    budget,
    days,
):
    """Check whether the planned route reaches all requested destinations
    and satisfies the budget and duration constraints."""

    requested_destinations = [
        str(destination).strip()
        for destination in destinations
    ]

    route_names = [
        str(location).strip()
        for location in route
    ]

    # Check that the route starts at the selected starting location.
    if not route_names or route_names[0] != current_location:
        return {
            "success": False,
            "goal_reached": False,
            "eligible": False,
            "route": route_names,
            "reason": "The route does not start at the selected location.",
        }

    # Check that every requested destination is included.
    missing_destinations = [
        destination
        for destination in requested_destinations
        if destination not in route_names[1:]
    ]

    if missing_destinations:
        return {
            "success": False,
            "goal_reached": False,
            "eligible": False,
            "route": route_names,
            "reason": (
                "The route is missing these destinations: "
                + ", ".join(missing_destinations)
            ),
        }

    # Check the complete trip, not just one transport leg.
    eligibility = check_destination_eligibility(
        total_cost=total_cost,
        budget=budget,
        travel_hours=travel_hours,
        days=days,
    )

    if not eligibility["eligible"]:
        return {
            "success": False,
            "goal_reached": True,
            "eligible": False,
            "route": route_names,
            "reason": eligibility["reason"],
        }

    return {
        "success": True,
        "goal_reached": True,
        "eligible": True,
        "route": route_names,
        "reason": (
            "The route includes all requested destinations and "
            "satisfies the budget and duration constraints."
        ),
    }




   

def compare_transport_options(
    candidates,
    budget,
    days,
    hotel_cost=0,
    food_cost=0,
    attraction_cost=0,
    cost_weight=0.5,
    time_weight=0.3,
    preference_weight=0.2,
):
    """Rank transport choices by feasibility and utility."""

    results = []

    for option in candidates:
        transport_cost = float(option["cost"])

        estimate = calculate_trip_estimate(
            transport_cost=transport_cost,
            hotel_cost=hotel_cost,
            food_cost=food_cost,
            attraction_cost=attraction_cost,
        )

        evaluation = evaluate_plan(
            total_cost=estimate["total_cost"],
            budget=budget,
            travel_hours=option["hours"],
            days=days,
            transport_cost=transport_cost,
            hotel_cost=hotel_cost,
            food_cost=food_cost,
            attraction_cost=attraction_cost,
            cost_weight=cost_weight,
            time_weight=time_weight,
        )

        results.append({
            **option,
            **estimate,
            **evaluation,
        })

    feasible = [
        option for option in results
        if option["eligible"]
    ]

    ranked = sorted(
        feasible if feasible else results,
        key=lambda option: (
            option["eligible"],
            option["utility"],
        ),
        reverse=True,
    )

    recommended = ranked[0] if ranked else None

    return {
        "options": ranked,
        "recommended": recommended,
        "reason": (
            recommended["reason"]
            if recommended
            else "No transport options were supplied."
        ),
    }

def calculate_preference_score(attractions, interests):
    """Score how well the selected attractions match user interests."""

    if not interests:
        return 100.0

    category_mapping = {
        "Nature": "nature",
        "Adventure": "adventure",
        "History": "history",
        "Spirituality": "spiritual",
        "Sightseeing": "sightseeing",
    }

    selected_categories = {
        category_mapping[interest]
        for interest in interests
        if interest in category_mapping
    }

    if not selected_categories:
        return 0.0

    if not attractions:
        return 0.0

    matched = sum(
        1
        for attraction in attractions
        if attraction.get("category", "").lower() in selected_categories
    )

    return round((matched / len(attractions)) * 100, 1)
