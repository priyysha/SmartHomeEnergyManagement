
import streamlit as st
import pandas as pd
import plotly.express as px

from modules.optimizer import (
    optimize_schedule,
    calculate_comfort_score
)


# -----------------------------------
# PAGE CONFIGURATION
# -----------------------------------

st.set_page_config(
    page_title="Smart Home Energy Manager",
    page_icon="🏠",
    layout="wide"
)

st.title("Smart Home Energy Management System")

st.markdown(
    "Intelligent energy scheduling to reduce electricity "
    "cost and peak demand while respecting user preferences."
)

st.divider()


# -----------------------------------
# ELECTRICITY TARIFF
# -----------------------------------

st.sidebar.header("Electricity Tariff")

night_rate = st.sidebar.number_input(
    "Night rate (₹/kWh)",
    min_value=0.0,
    value=4.0
)

morning_rate = st.sidebar.number_input(
    "Morning rate (₹/kWh)",
    min_value=0.0,
    value=5.0
)

day_rate = st.sidebar.number_input(
    "Day rate (₹/kWh)",
    min_value=0.0,
    value=7.0
)

evening_rate = st.sidebar.number_input(
    "Evening rate (₹/kWh)",
    min_value=0.0,
    value=10.0
)


hourly_rates = []

for hour in range(24):

    if 0 <= hour < 6 or 22 <= hour < 24:
        hourly_rates.append(night_rate)

    elif 6 <= hour < 10:
        hourly_rates.append(morning_rate)

    elif 10 <= hour < 17:
        hourly_rates.append(day_rate)

    else:
        hourly_rates.append(evening_rate)


# -----------------------------------
# APPLIANCE INPUTS
# -----------------------------------

st.header("Household Appliance Configuration")

st.write(
    "Enter appliance details and preferred operating hours."
)

appliances = []

default_appliances = [
    ("AC", 1500, 3, 18, 23),
    ("Washing Machine", 500, 1, 8, 22),
    ("Water Heater", 2000, 1, 5, 23)
]

for index, item in enumerate(default_appliances):

    name, power, duration, start, end = item

    with st.expander(f"{name}", expanded=True):

        col1, col2 = st.columns(2)

        with col1:

            appliance_power = st.number_input(
                "Power (Watts)",
                min_value=1,
                value=power,
                key=f"power_{index}"
            )

            operating_duration = st.number_input(
                "Required hours",
                min_value=1,
                max_value=24,
                value=duration,
                key=f"duration_{index}"
            )

        with col2:

            preferred_start = st.selectbox(
                "Preferred start hour",
                range(24),
                index=start,
                format_func=lambda x: f"{x:02d}:00",
                key=f"start_{index}"
            )

            preferred_end = st.selectbox(
                "Preferred end hour",
                range(24),
                index=end,
                format_func=lambda x: f"{x:02d}:00",
                key=f"end_{index}"
            )

        appliances.append({
            "name": name,
            "power": appliance_power,
            "duration": operating_duration,
            "preferred_start": preferred_start,
            "preferred_end": preferred_end
        })


# -----------------------------------
# PEAK DEMAND LIMIT
# -----------------------------------

st.header("Energy Management Settings")

max_demand = st.number_input(
    "Maximum allowed household demand (kW)",
    min_value=0.5,
    max_value=20.0,
    value=4.0,
    step=0.5
)


# -----------------------------------
# OPTIMIZATION
# -----------------------------------

if st.button("Optimize Energy Schedule", type="primary"):

    try:

        # -----------------------------------
        # OPTIMIZED SCHEDULE
        # -----------------------------------

        schedule, demand, hourly_cost = optimize_schedule(
            appliances,
            hourly_rates,
            max_demand
        )

        total_cost = sum(hourly_cost)
        total_energy = sum(demand)
        peak_demand = max(demand)

        comfort_score = calculate_comfort_score(
            appliances,
            schedule
        )

        # -----------------------------------
        # NORMAL (BASELINE) SCHEDULE
        # -----------------------------------

        baseline_demand = [0.0] * 24
        baseline_cost = [0.0] * 24

        baseline_schedule = {}

        for appliance in appliances:

            name = appliance["name"]
            power = appliance["power"] / 1000
            duration = appliance["duration"]

            start = appliance["preferred_start"]

            slots = [
                (start + i) % 24
                for i in range(duration)
            ]

            baseline_schedule[name] = slots

            for hour in slots:

                baseline_demand[hour] += power

                baseline_cost[hour] += (
                    power * hourly_rates[hour]
                )

        baseline_total_cost = sum(baseline_cost)
        baseline_peak = max(baseline_demand)

        # -----------------------------------
        # COMPARISON METRICS
        # -----------------------------------

        cost_savings = (
            (baseline_total_cost - total_cost)
            / baseline_total_cost * 100
            if baseline_total_cost > 0 else 0
        )

        peak_reduction = (
            (baseline_peak - peak_demand)
            / baseline_peak * 100
            if baseline_peak > 0 else 0
        )

        # -----------------------------------
        # OPTIMIZATION RESULTS
        # -----------------------------------

        st.divider()

        st.header("Optimization Results")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Electricity Cost",
            f"₹{total_cost:.2f}"
        )

        col2.metric(
            "Peak Demand",
            f"{peak_demand:.2f} kW"
        )

        col3.metric(
            "Energy Consumption",
            f"{total_energy:.2f} kWh"
        )

        col4.metric(
            "User Comfort Score",
            f"{comfort_score:.1f}%"
        )

        # -----------------------------------
        # BASELINE VS OPTIMIZED COMPARISON
        # -----------------------------------

        st.divider()

        st.header("Normal vs Optimized Performance")

        col1, col2 = st.columns(2)

        col1.metric(
            "Electricity Cost Savings",
            f"{cost_savings:.2f}%",
            delta=f"₹{baseline_total_cost - total_cost:.2f}"
        )

        col2.metric(
            "Peak Demand Reduction",
            f"{peak_reduction:.2f}%",
            delta=f"{baseline_peak - peak_demand:.2f} kW"
        )

        comparison_df = pd.DataFrame({
            "Metric": [
                "Electricity Cost (₹)",
                "Peak Demand (kW)"
            ],
            "Normal Schedule": [
                baseline_total_cost,
                baseline_peak
            ],
            "Optimized Schedule": [
                total_cost,
                peak_demand
            ]
        })

        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True
        )

        # -----------------------------------
        # APPLIANCE SCHEDULE
        # -----------------------------------

        st.subheader("Optimized Appliance Schedule")

        schedule_data = []

        for appliance in appliances:

            name = appliance["name"]
            hours = schedule[name]

            if hours:

                schedule_data.append({
                    "Appliance": name,
                    "Scheduled Hours": ", ".join(
                        f"{hour:02d}:00" for hour in hours
                    ),
                    "Power": f"{appliance['power']} W",
                    "Status": "Scheduled"
                })

            else:

                schedule_data.append({
                    "Appliance": name,
                    "Scheduled Hours": "Not available",
                    "Power": f"{appliance['power']} W",
                    "Status": "Could not schedule"
                })

        st.dataframe(
            pd.DataFrame(schedule_data),
            use_container_width=True,
            hide_index=True
        )

        # -----------------------------------
        # DEMAND COMPARISON GRAPH
        # -----------------------------------

        st.subheader("Normal vs Optimized Electricity Demand")

        demand_df = pd.DataFrame({
            "Hour": [f"{h:02d}:00" for h in range(24)],
            "Normal Schedule": baseline_demand,
            "Optimized Schedule": demand
        })

        fig1 = px.line(
            demand_df,
            x="Hour",
            y=["Normal Schedule", "Optimized Schedule"],
            markers=True,
            title="Hourly Household Electricity Demand"
        )

        fig1.add_hline(
            y=max_demand,
            line_dash="dash",
            annotation_text="Maximum demand limit"
        )

        fig1.update_layout(
            xaxis_title="Hour",
            yaxis_title="Demand (kW)"
        )


        st.plotly_chart(
            fig1,
            use_container_width=True
        )

        # -----------------------------------
        # ELECTRICITY COST GRAPH
        # -----------------------------------

        st.subheader("Hourly Electricity Cost")

        cost_df = pd.DataFrame({
            "Hour": [f"{h:02d}:00" for h in range(24)],
            "Cost (₹)": hourly_cost
        })

        fig2 = px.bar(
            cost_df,
            x="Hour",
            y="Cost (₹)",
            title="Electricity Cost Per Hour"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

        # -----------------------------------
        # FINAL SUMMARY
        # -----------------------------------

        st.success("Energy optimization completed successfully!")

        st.write(
            f"Normal electricity cost: ₹{baseline_total_cost:.2f}"
        )

        st.write(
            f"Optimized electricity cost: ₹{total_cost:.2f}"
        )

        st.write(
            f"Normal peak demand: {baseline_peak:.2f} kW"
        )

        st.write(
            f"Optimized peak demand: {peak_demand:.2f} kW"
        )

        st.write(
            f"User comfort score: {comfort_score:.1f}%"
        )

    except ValueError as error:

        st.error(str(error))
