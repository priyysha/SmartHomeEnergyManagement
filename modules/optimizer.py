
def get_allowed_hours(start, end):
    """
    Return all allowed operating hours.
    Supports time windows that cross midnight.
    Both start and end hours are inclusive.
    """
    if start <= end:
        return list(range(start, end + 1))

    return list(range(start, 24)) + list(range(0, end + 1))


def get_valid_start_times(appliance):
    """
    Find possible starting hours where the appliance
    can complete its entire operating duration
    within its preferred time window.
    """
    start = appliance["preferred_start"]
    end = appliance["preferred_end"]
    duration = appliance["duration"]

    allowed_hours = get_allowed_hours(start, end)
    valid_starts = []

    for hour in allowed_hours:
        slots = [(hour + i) % 24 for i in range(duration)]

        if all(slot in allowed_hours for slot in slots):
            valid_starts.append(hour)

    return valid_starts


def calculate_comfort_score(appliances, schedule):
    """
    Calculate a comfort score from 0 to 100.

    Starting at the preferred start hour gives
    maximum comfort. Delaying an appliance reduces
    its comfort score.
    """
    if not appliances:
        return 100.0

    total_score = 0.0

    for appliance in appliances:
        name = appliance["name"]
        starts = schedule.get(name, [])

        if not starts:
            return 0.0

        actual_start = starts[0]
        preferred_start = appliance["preferred_start"]

        allowed_starts = get_valid_start_times(appliance)

        if not allowed_starts:
            return 0.0

        max_delay = max(
            (hour - preferred_start) % 24
            for hour in allowed_starts
        )

        actual_delay = (
            actual_start - preferred_start
        ) % 24

        if max_delay == 0:
            appliance_score = 100.0
        else:
            appliance_score = (
                100 * (1 - actual_delay / max_delay)
            )

        total_score += appliance_score

    return total_score / len(appliances)


def optimize_schedule(
    appliances,
    hourly_rates,
    max_demand,
    cost_weight=0.40,
    peak_weight=0.35,
    comfort_weight=0.25
):
    """
    Multi-objective smart home energy optimizer.

    Objectives:
    1. Minimize electricity cost.
    2. Minimize peak electricity demand.
    3. Maximize user comfort.

    Uses exhaustive search to find the best feasible
    combination of appliance starting times.

    Returns:
        schedule
        hourly_demand
        hourly_cost
    """

    # -----------------------------------
    # INPUT VALIDATION
    # -----------------------------------

    if len(hourly_rates) != 24:
        raise ValueError("Exactly 24 hourly rates are required.")

    if max_demand <= 0:
        raise ValueError("Maximum demand must be greater than zero.")

    weights = [cost_weight, peak_weight, comfort_weight]

    if any(weight < 0 for weight in weights):
        raise ValueError("Objective weights cannot be negative.")

    if sum(weights) == 0:
        raise ValueError("At least one objective weight must be positive.")

    weight_total = sum(weights)

    cost_weight /= weight_total
    peak_weight /= weight_total
    comfort_weight /= weight_total

    for appliance in appliances:
        if appliance["power"] <= 0:
            raise ValueError("Appliance power must be positive.")

        if not 1 <= appliance["duration"] <= 24:
            raise ValueError("Appliance duration must be between 1 and 24.")

        if not 0 <= appliance["preferred_start"] <= 23:
            raise ValueError("Preferred start must be between 0 and 23.")

        if not 0 <= appliance["preferred_end"] <= 23:
            raise ValueError("Preferred end must be between 0 and 23.")

    # -----------------------------------
    # FIND POSSIBLE START TIMES
    # -----------------------------------

    appliance_options = []

    for appliance in appliances:
        valid_starts = get_valid_start_times(appliance)

        if not valid_starts:
            raise ValueError(
                f"No valid operating time exists for {appliance['name']}."
            )

        appliance_options.append({
            "appliance": appliance,
            "starts": valid_starts
        })

    # Schedule appliances with fewer options first.
    appliance_options.sort(
        key=lambda item: len(item["starts"])
    )

    # -----------------------------------
    # NORMALIZATION VALUES
    # -----------------------------------

    maximum_possible_cost = sum(
        (item["appliance"]["power"] / 1000)
        * item["appliance"]["duration"]
        * max(hourly_rates)
        for item in appliance_options
    )

    if maximum_possible_cost == 0:
        maximum_possible_cost = 1

    # -----------------------------------
    # SEARCH FOR THE BEST SCHEDULE
    # -----------------------------------

    hourly_demand = [0.0] * 24
    hourly_cost = [0.0] * 24

    current_schedule = {}
    best_schedule = None
    best_demand = None
    best_cost = None
    best_objective = float("inf")

    def search(index):

        nonlocal best_schedule
        nonlocal best_demand
        nonlocal best_cost
        nonlocal best_objective

        # All appliances have been scheduled.
        if index == len(appliance_options):

            total_cost = sum(hourly_cost)
            peak = max(hourly_demand)

            comfort = calculate_comfort_score(
                appliances,
                current_schedule
            )

            normalized_cost = (
                total_cost / maximum_possible_cost
            )

            normalized_peak = peak / max_demand

            comfort_penalty = (
                1 - comfort / 100
            )

            # Combined multi-objective function.
            objective = (
                cost_weight * normalized_cost
                + peak_weight * normalized_peak
                + comfort_weight * comfort_penalty
            )

            if objective < best_objective:
                best_objective = objective

                best_schedule = {
                    name: slots[:]
                    for name, slots in current_schedule.items()
                }

                best_demand = hourly_demand[:]
                best_cost = hourly_cost[:]

            return

        item = appliance_options[index]
        appliance = item["appliance"]

        name = appliance["name"]
        power = appliance["power"] / 1000
        duration = appliance["duration"]

        for start in item["starts"]:

            slots = [
                (start + i) % 24
                for i in range(duration)
            ]

            # Reject schedules that exceed the demand limit.
            if any(
                hourly_demand[hour] + power > max_demand + 1e-9
                for hour in slots
            ):
                continue

            # Apply this appliance's schedule.
            current_schedule[name] = slots

            for hour in slots:
                hourly_demand[hour] += power
                hourly_cost[hour] += power * hourly_rates[hour]

            # Schedule the next appliance.
            search(index + 1)

            # Backtrack and try another starting time.
            for hour in slots:
                hourly_demand[hour] -= power
                hourly_cost[hour] -= power * hourly_rates[hour]

            del current_schedule[name]

    search(0)

    # -----------------------------------
    # CHECK WHETHER A FEASIBLE SCHEDULE EXISTS
    # -----------------------------------

    if best_schedule is None:
        raise ValueError(
            "No feasible schedule found. Increase the maximum "
            "demand limit or adjust appliance preferences."
        )

    return best_schedule, best_demand, best_cost
