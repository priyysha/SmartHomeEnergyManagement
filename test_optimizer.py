
from modules.optimizer import optimize_schedule

# Electricity price for each hour
hourly_rates = []

for hour in range(24):
    if 0 <= hour < 6 or 22 <= hour < 24:
        hourly_rates.append(4)
    elif 6 <= hour < 10:
        hourly_rates.append(5)
    elif 10 <= hour < 17:
        hourly_rates.append(7)
    else:
        hourly_rates.append(10)


# Household appliances
appliances = [
    {
        "name": "AC",
        "power": 1500,
        "duration": 3,
        "preferred_start": 18,
        "preferred_end": 23
    },
    {
        "name": "Washing Machine",
        "power": 500,
        "duration": 1,
        "preferred_start": 8,
        "preferred_end": 22
    },
    {
        "name": "Water Heater",
        "power": 2000,
        "duration": 1,
        "preferred_start": 5,
        "preferred_end": 23
    }
]

schedule, demand, cost = optimize_schedule(
    appliances,
    hourly_rates,
    max_demand=4
)

print("\nOPTIMIZED APPLIANCE SCHEDULE")

for appliance, hours in schedule.items():
    print(appliance, ":", hours)

print("\nMaximum Demand:", max(demand), "kW")
print("Total Electricity Cost:", round(sum(cost), 2), "Rs.")
