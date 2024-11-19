from datetime import datetime


def calculate_predicted_costs(total_cost, estimated_saves):
    """
    Calculate the predicted total cost and estimated savings for the month
    based on the current usage and day of the month.

    Args:
        total_cost (float): The current total cost.
        estimated_saves (float): The estimated savings based on optimizations.

    Returns:
        dict: A dictionary containing 'total_predicted_cost' and 'estimated_saves_projected'.
    """
    days_in_month = 30  # Assuming a 30-day month for simplicity
    today = datetime.now().day
    predicted_multiplier = days_in_month / today if today > 0 else 1

    total_predicted_cost = total_cost * predicted_multiplier
    estimated_saves_projected = estimated_saves * predicted_multiplier

    return {
        "total_predicted_cost": total_predicted_cost,
        "estimated_saves_projected": estimated_saves_projected,
    }
