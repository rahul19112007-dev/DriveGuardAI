import importlib
import plotly.express as px
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="DriveGuard AI Dashboard", layout="wide")

st.markdown("""
<style>

.main {
    background-color: #0E1117;
}

div[data-testid="metric-container"] {
    background: linear-gradient(135deg,#1E293B,#111827);
    border: 1px solid #334155;
    padding: 18px;
    border-radius: 18px;
    box-shadow: 0px 4px 18px rgba(0,0,0,0.3);
}

div[data-testid="metric-container"] label {
    color: #94A3B8 !important;
}

div[data-testid="metric-container"] div {
    color: white !important;
}

h1 {
    color: #00E5FF;
    text-align: center;
}

h2,h3 {
    color: white;
}

[data-testid="stDataFrame"] {
    border-radius: 15px;
    overflow: hidden;
}

.stDownloadButton button {
    background: linear-gradient(135deg,#06B6D4,#2563EB);
    color: white;
    border-radius: 12px;
    border: none;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

st_autorefresh(interval=10_000, key="dashboard_autorefresh")

firebase_admin = None
credentials = None
db = None

try:
    firebase_admin = importlib.import_module("firebase_admin")
    credentials = importlib.import_module("firebase_admin.credentials")
    db = importlib.import_module("firebase_admin.db")
except ImportError:
    firebase_admin = None
    credentials = None
    db = None

# Firebase Setup

if firebase_admin is None or credentials is None or db is None:
    st.error("Firebase Admin SDK is unavailable. Install the firebase_admin package.")
    st.stop()

if not firebase_admin._apps:
    cred = credentials.Certificate(
        "firebase_key.json"
    )

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL":
            "https://driveguardai-486d3-default-rtdb.asia-southeast1.firebasedatabase.app/"
        }
    )

st.markdown("""
<h1>
🚗 DriveGuard AI
</h1>
<p style='text-align:center;color:#94A3B8;font-size:18px'>
Real-Time Driver Fatigue Monitoring System
</p>
""", unsafe_allow_html=True)

status_ref = db.reference(
    "live_status"
)

live = status_ref.get()

# Fetch Data

ref = db.reference("events")

data = ref.get()

if live:
    location_ref = db.reference(
        "live_location"
    )

    location = location_ref.get()

    if location:
        st.markdown("## 📍 Driver Location")

        map_df = pd.DataFrame(
            {
                "lat": [location.get("latitude")],
                "lon": [location.get("longitude")]
            }
        )

        st.map(map_df)

        st.markdown("## 🟢 Live Driver Status")

        colA, colB = st.columns(2)

        colA.metric("Current Status", live.get("status", "Unknown"))
        colB.metric("Current Score", live.get("score", "N/A"))

records = []
df = pd.DataFrame(columns=["Time", "Event", "Score"])

if data:
    for key, value in data.items():
        records.append(
            {
                "Time": value.get("time"),
                "Event": value.get("event"),
                "Score": value.get("score")
            }
        )

    df = pd.DataFrame(records)
# Default values in case dataframe is empty
latest_score = "N/A"
fatigue_count = 0
yawn_count = 0

# If we have event rows, compute latest metrics
if not df.empty:
    latest_score = df.iloc[-1]["Score"]
    fatigue_count = len(df[df["Event"] == "Driver Fatigue"])
    yawn_count = len(df[df["Event"] == "Excessive Yawning"])

# Statistics

total_trips = 0
avg_score = 0
total_drive_time = 0
worst_score = 100

trip_ref = db.reference("trip_summary")
trip_data = trip_ref.get()

if trip_data:

    total_trips = len(trip_data)

    scores = []
    durations = []

    for _, trip in trip_data.items():

        scores.append(
            trip.get("score", 100)
        )

        durations.append(
            trip.get("trip_time", 0)
        )

    avg_score = round(
        sum(scores) / len(scores),
        1
    )

    total_drive_time = sum(
        durations
    )

    worst_score = min(
        scores
    )

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Safety Score",
    latest_score
)

col2.metric(
    "Fatigue Alerts",
    fatigue_count
)

col3.metric(
    "Fatigue Signs",
    yawn_count
)

col4.metric(
    "Total Trips",
    total_trips
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Average Score",
    avg_score
)

col2.metric(
    "Driving Time (min)",
    total_drive_time
)

col3.metric(
    "Worst Score",
    worst_score
)

fatigue_df = df[
    df["Event"] == "Driver Fatigue"
]

if not fatigue_df.empty:
    chart = px.line(
        fatigue_df,
        x="Time",
        y="Score",
        title="Fatigue Trend"
    )

    chart.update_layout(
    paper_bgcolor="#111827",
    plot_bgcolor="#111827",
    font_color="white",
    title_font_size=24,
    height=450
)

st.plotly_chart(
    chart,
    width="stretch"
)

csv = df.to_csv(
    index=False
)

st.download_button(
    label="📥 Download Report CSV",
    data=csv,
    file_name="driveguard_report.csv",
    mime="text/csv"
)

st.markdown("## 📋 Event History")
st.dataframe(df[::-1], use_container_width=True)

st.markdown("## 📊 Trip Analytics")

trip_ref = db.reference("trip_summary")
trip_data = trip_ref.get()

if trip_data:

    latest_trip = list(
        trip_data.values()
    )[-1]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Driving Time",
        f"{latest_trip['trip_time']} min"
    )

    col2.metric(
        "Fatigue Alerts",
        latest_trip['fatigue_alerts']
    )

    col3.metric(
        "Yawns",
        latest_trip['yawns']
    )

    col4.metric(
        "Final Score",
        latest_trip['score']
    )

else:

    st.warning(
        "No Firebase Data Found"
    )