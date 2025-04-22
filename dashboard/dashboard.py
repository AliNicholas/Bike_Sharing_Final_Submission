import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data & mempersiapkan data
df = pd.read_csv("dashboard/main_data.csv")
df["hour"] = df["hour"].astype(str).str.zfill(2) + ":00"
df["datetime"] = pd.to_datetime(df["year"].astype(str) + "-" + df["month"] + "-01 " + df["hour"])
df["date"] = df["datetime"].dt.date

# konfigurasi
st.set_page_config(page_title="🚲 Bike Sharing Dashboard", layout="wide")

# title
st.title("🚲 Bike Sharing Dashboard")

# interatif plot
filter_col, visual_col = st.columns([1, 3])

with filter_col:
    st.header("🔧 Filter")

    # Checkbox - Weather Condition
    weather_types = df["weather_condition"].unique().tolist()
    st.subheader("🌦️ Weather Condition")
    weather_selected = [w for w in weather_types if st.checkbox(w, value=True, key=f"w_{w}")]
    if not weather_selected:
        st.error("atleast choose one weather condition!")

    # Checkbox - User Type
    st.subheader("🧑‍🧑 User Type")
    casual = st.checkbox("Casual", value=True)
    registered = st.checkbox("Registered", value=True)
    user_cols = []
    if casual:
        user_cols.append("casual")
    if registered:
        user_cols.append("registered")
    if not user_cols:
        st.error("atleast choose one user type!")

    # Slider - Time range
    st.subheader("⏱️ Time Range (Hour)")
    hour_range = st.select_slider("Choose with slider:", options=[f"{h:02d}:00" for h in range(24)], value=("00:00", "23:00"))
    st.markdown(f"Choosen Time: **{hour_range[0]}** hingga **{hour_range[1]}**")

with visual_col:
    st.title("🌏 Interactive Dashboard")

    # Filter data
    filtered_df = df[(df["weather_condition"].isin(weather_selected)) & (df["hour"] >= hour_range[0]) & (df["hour"] <= hour_range[1])]

    if filtered_df.empty:
        st.warning("Tidak ada data yang sesuai dengan filter.")
    else:
        filtered_df["hour_int"] = filtered_df["hour"].str[:2].astype(int)
        hour_group = filtered_df.groupby("hour_int")[user_cols].sum().reset_index()
        melted_hour = hour_group.melt(id_vars="hour_int", var_name="User Type", value_name="RentCount")

        fig1, ax1 = plt.subplots(figsize=(10, 5))
        sns.lineplot(
            data=melted_hour,
            x="hour_int",
            y="RentCount",
            hue="User Type",
            marker="o",
            palette="Set2",
            ax=ax1,
        )

        ax1.set_title("Rent Bike Trend (Filtered)", fontsize=13)
        ax1.set_xlabel("Hour")
        ax1.set_ylabel("Total Rent")
        ax1.set_xticks(range(24))
        ax1.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=45)
        ax1.grid(True)
        weather_str = ", ".join(weather_selected)
        ax1.text(
            0.01,
            0.98,
            f"Weather: {weather_str}",
            fontsize=7,
            transform=ax1.transAxes,
            ha="left",
            va="top",
            bbox=dict(facecolor="white", alpha=0.6, edgecolor="gray"),
        )

        st.pyplot(fig1)

# overview plot
st.header("📊 Exploratory Overview")

# overview row 1
overview1_col, overview2_col = st.columns(2)
with overview1_col:
    st.subheader("🕒 Rent per Hour: Workday vs Holiday")
    avg_hour = df.groupby(["hour", "is_workingday"])["total_rent_count"].mean().unstack()
    fig, ax = plt.subplots(figsize=(7, 4))
    avg_hour.plot(ax=ax, marker="o")
    ax.set_title("Average Rent per Hour\n(Workday vs Holiday)", fontsize=11)
    ax.set_xlabel("Hour")
    ax.set_ylabel("Rental Count")
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=45)
    ax.legend(title="Day Type")
    ax.grid(True)
    st.pyplot(fig)

with overview2_col:
    st.subheader("📈 Monthly Rental Trend: Casual vs Registered")
    monthly = df.resample("M", on="datetime")[["casual", "registered"]].mean()
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    monthly.plot(ax=ax3, marker="o")
    ax3.set_title("Average Rental per Hour per Month", fontsize=11)
    ax3.set_xlabel("Month")
    ax3.set_ylabel("Rental Count")
    ax3.grid(True)
    st.pyplot(fig3)


# overview row 2
overview3_col, overview4_col = st.columns(2)
with overview3_col:
    st.subheader("🌧️ Weather Condition Impact")
    avg_weather = df.groupby("weather_condition")["total_rent_count"].mean().sort_values(ascending=False)

    fig2, ax2 = plt.subplots(figsize=(6, 4))
    avg_weather.plot(kind="bar", ax=ax2, color="cornflowerblue", edgecolor="black")

    ax2.set_title("Average Rent per Weather Category (2011–2012)", fontsize=11)
    ax2.set_xlabel("Weather Condition")
    ax2.set_ylabel("Total Rent")
    ax2.set_xticklabels(avg_weather.index, rotation=45, ha="right")
    ax2.grid(axis="y")
    st.pyplot(fig2)


with overview4_col:
    st.subheader("🌡️ Rental Based on Temperature Zones")
    df["temp_c"] = df["temp"] * 41
    bins = [-1, 10, 20, 30, 50]
    labels = ["Dingin", "Sejuk", "Hangat", "Panas"]
    df["temp_zone"] = pd.cut(df["temp_c"], bins=bins, labels=labels)
    temp_rental = df.groupby(["date", "temp_zone"])["total_rent_count"].sum().reset_index()
    avg_temp = temp_rental.groupby("temp_zone")["total_rent_count"].mean()
    fig4, ax4 = plt.subplots(figsize=(5.5, 4))
    avg_temp.plot(kind="bar", color="coral", ax=ax4)
    ax4.set_title("Avg Daily Rental by Temperature Zone")
    ax4.set_xlabel("Temp Zone")
    ax4.set_ylabel("Average Rental")
    ax4.grid(axis="y")
    st.pyplot(fig4)
