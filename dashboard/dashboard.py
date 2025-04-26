# import library
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load dataset & Preprocessing dataset (main_data.csv)
df = pd.read_csv("main_data.csv")
df["date"] = pd.to_datetime(df["date"])
df["hour_int"] = df["hour"].str.slice(0, 2).astype(int)
df.set_index("date", inplace=True)
df["temp_c"] = df["temp"] * 41
bins = [-1, 10, 20, 30, 50]
labels = ["Cold", "Cool", "Warm", "Hot"]
df["zona_suhu"] = pd.cut(df["temp_c"], bins=bins, labels=labels)

# configurasi for streamlit web
st.set_page_config(page_title="🚲 Bike Sharing Dashboard", layout="wide")
st.title("🚲 Bike Sharing Dashboard")

# sidebar filter
st.sidebar.header("🔧 Filter")

## filter 1 - Day of Week
st.sidebar.subheader("📅 Day of Week")
all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
selected_days = [d for d in all_days if st.sidebar.checkbox(d, True, key=f"day_{d}")]
if not selected_days:
    st.sidebar.error("At least choose one Day!")

## filter 2 - Season
st.sidebar.subheader("🍂 Season")
seasons = ["Spring", "Summer", "Autumn", "Winter"]
selected_seasons = [s for s in seasons if st.sidebar.checkbox(s, True, key=f"season_{s}")]
if not selected_seasons:
    st.sidebar.error("At least choose one Season!")

## filter 3 - User Type
st.sidebar.subheader("🧑‍🧑 User Type")
user_cols = []
if st.sidebar.checkbox("Casual", True, key="user_casual"):
    user_cols.append("casual")
if st.sidebar.checkbox("Registered", True, key="user_registered"):
    user_cols.append("registered")
if not user_cols:
    st.sidebar.error("At least choose one Type!")

# feature engineering
## day & season
df["day_of_week"] = df.index.day_name()
map_season = lambda m: ("Spring" if m in [3, 4, 5] else "Summer" if m in [6, 7, 8] else "Autumn" if m in [9, 10, 11] else "Winter")
df["Season"] = df.index.month.map(map_season)
df_filtered = df[df["day_of_week"].isin(selected_days) & df["Season"].isin(selected_seasons)]

## filtering
if not df_filtered.empty and user_cols:
    df_filtered = df_filtered.assign(rental_selected=df_filtered[user_cols].sum(axis=1))
else:
    df_filtered = df_filtered.copy()
    df_filtered["rental_selected"] = np.nan


## check data availability
def has_data(df_obj):
    return not df_obj.empty and df_filtered["rental_selected"].notna().any()


# eda1
if has_data(df_filtered):
    eda1 = (
        df_filtered.pivot_table(values="rental_selected", index="hour_int", columns="is_workingday", aggfunc="mean")
        .rename(columns={"Yes": "Workday", "No": "Holiday"})
        .reindex(range(24))
    )
else:
    eda1 = pd.DataFrame()

# eda2
if has_data(df_filtered):
    daily = df_filtered.reset_index().groupby("date")["rental_selected"].sum().to_frame("daily_rental")
    weather_daily = df_filtered.reset_index().groupby("date")["weather_condition"].agg(lambda x: x.mode().iloc[0]).to_frame("weather_condition")
    daily = daily.join(weather_daily)
    daily["weather_group"] = daily["weather_condition"].apply(lambda w: "Bad" if w in ["Light Snow/Rain", "Heavy Rain/Snow"] else "Normal")
    eda2 = daily.groupby("weather_group")["daily_rental"].mean().reset_index()
else:
    eda2 = pd.DataFrame()

# eda3
if has_data(df_filtered):
    eda3 = df_filtered.resample("MS")[user_cols].mean().reset_index().rename(columns={c: f"rental_{c}" for c in user_cols})
else:
    eda3 = pd.DataFrame()

# eda4
if has_data(df_filtered):
    temp_daily = df_filtered.reset_index().groupby("date").agg({"rental_selected": "sum", "zona_suhu": lambda x: x.mode().iloc[0]})
    eda4 = temp_daily.groupby("zona_suhu")["rental_selected"].mean().reset_index().rename(columns={"rental_selected": "total_rent_count"})
else:
    eda4 = pd.DataFrame()

# visualization
## define columns
plot_col1, plot_col2 = st.columns(2)
plot_col3, plot_col4 = st.columns(2)

## chart 1
with plot_col1:
    st.subheader("🕒 Rent per Hour: Workday vs Holiday")
    if eda1.empty:
        st.warning("No data available with current filters.")
    else:
        fig, ax = plt.subplots(figsize=(12, 5))
        hrs = eda1.index.tolist()
        lbl = [f"{h:02d}:00" for h in hrs]
        for col in ["Workday", "Holiday"]:
            if col in eda1:
                ax.plot(hrs, eda1[col], marker="o", label=col)
        ax.set_xticks(hrs)
        ax.set_xticklabels(lbl, rotation=45)
        ax.set_title("Average Rent per Hour on Workdays vs Holidays (2011–2012)")
        ax.set_xlabel("Hour")
        ax.set_ylabel("AVG Rental Count")
        ax.grid(ls="--", alpha=0.4)
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)

## chart 2
with plot_col2:
    st.subheader("📈 Monthly Rental Trend: Casual vs Registered")
    if eda3.empty:
        st.warning("No data available with current filters.")
    else:
        fig, ax = plt.subplots(figsize=(12, 5))
        for col, lbl in [("rental_registered", "Registered"), ("rental_casual", "Casual")]:
            if col in eda3:
                ax.plot(eda3["date"], eda3[col], marker="o", label=lbl)
        ax.set_title("Monthly Average Rental Count per Hour (2011–2012)")
        ax.set_xlabel("Month")
        ax.set_ylabel("Average Rental Count")
        ax.grid(ls="--", alpha=0.4)
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

## chart 3
with plot_col3:
    st.subheader("🌧️ Weather Condition Impact")
    if eda2.empty:
        st.warning("No data available with current filters.")
    else:
        fig, ax = plt.subplots(figsize=(6, 4))
        groups = eda2["weather_group"].tolist()
        ax.bar(groups, eda2["daily_rental"], color=["tab:red" if g == "Bad" else "tab:blue" for g in groups])
        ax.set_xticks(range(len(groups)))
        labels = ["Bad Weather" if g == "Bad" else "Normal Weather" for g in groups]
        ax.set_xticklabels(labels)
        for i, v in enumerate(eda2["daily_rental"]):
            ax.text(i, v + 50, f"{v:.0f}", ha="center")
        ax.set_title("Average Daily Rental Count: Normal vs Bad Weather")
        ax.set_ylabel("Rentals per Day")
        ax.grid(axis="y", ls="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)

## chart 4
with plot_col4:
    st.subheader("🌡️ Rental Based on Temperature Zones")
    if eda4.empty:
        st.warning("No data available with current filters.")
    else:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(eda4["zona_suhu"], eda4["total_rent_count"])
        ax.set_title("Average Daily Rental by Temperature Zone")
        ax.set_xlabel("Temp Zone")
        ax.set_ylabel("Average Rental Count")
        plt.tight_layout()
        st.pyplot(fig)
