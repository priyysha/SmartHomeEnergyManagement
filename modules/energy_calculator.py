
def calculate_energy(power, hours):
    """
    Calculate electricity consumption in kWh.
    """
    return (power * hours) / 1000


def calculate_cost(energy, rate):
    """
    Calculate electricity cost in rupees.
    """
    return energy * rate


def calculate_peak_demand(hourly_demand):
    """
    Calculate maximum simultaneous power demand in kW.
    """
    if not hourly_demand:
        return 0

    return max(hourly_demand)


def calculate_total_cost(hourly_energy, hourly_rates):
    """
    Calculate total electricity cost across time slots.
    """
    return sum(
        energy * rate
        for energy, rate in zip(hourly_energy, hourly_rates)
    )
