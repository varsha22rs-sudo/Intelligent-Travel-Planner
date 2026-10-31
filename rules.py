"""Hard constraints for travel plans."""


def check_inputs(start, destinations, budget, days, allowed_transport, cities):
    errors = []
    if start not in cities:
        errors.append("Please select a valid starting city.")
    if not destinations:
        errors.append("Choose at least one destination.")
    if start in destinations:
        errors.append("The starting city cannot also be a required destination.")
    if any(city not in cities for city in destinations):
        errors.append("One or more selected destinations are not in the knowledge base.")
    if budget <= 0:
        errors.append("Budget must be greater than zero.")
    if days <= 0:
        errors.append("Trip duration must be greater than zero.")
    if not allowed_transport:
        errors.append("Choose at least one transport type.")
    return errors


def budget_rule(total_cost, budget):
    return total_cost <= budget


def time_rule(total_hours, available_hours):
    return total_hours <= available_hours
