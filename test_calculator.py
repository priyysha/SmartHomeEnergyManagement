
from modules.energy_calculator import (
    calculate_energy,
    calculate_cost,
    calculate_peak_demand,
    calculate_total_cost
)

# Test energy calculation
energy = calculate_energy(1500, 2)

# Test cost calculation
cost = calculate_cost(energy, 5)

# Test peak demand
peak = calculate_peak_demand([1.5, 2.0, 3.0, 1.0])

# Test total cost
total_cost = calculate_total_cost(
    [1, 2, 3],
    [4, 5, 6]
)

print("Energy Consumption:", energy, "kWh")
print("Electricity Cost: Rs.", cost)
print("Peak Demand:", peak, "kW")
print("Total Electricity Bill: Rs.", total_cost)
