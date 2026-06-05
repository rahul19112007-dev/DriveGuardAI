import firebase_admin
import threading

from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime

cred = credentials.Certificate("firebase_key.json")

firebase_admin.initialize_app(
    cred,
    {
        "databaseURL":
        "https://driveguardai-486d3-default-rtdb.asia-southeast1.firebasedatabase.app/"
    }
)


def _save_event(event, score):

    ref = db.reference("events")

    ref.push({
        "event": event,
        "score": score,
        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    })


def log_to_firebase(event, score):

    threading.Thread(
        target=_save_event,
        args=(event, score),
        daemon=True
    ).start()


def update_status(status, score):

    ref = db.reference("live_status")

    ref.set({
        "status": status,
        "score": score,
        "updated_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    })


def _save_trip(
    trip_time,
    fatigue_alerts,
    yawns,
    score
):

    ref = db.reference("trip_summary")

    ref.push({
        "trip_time": trip_time,
        "fatigue_alerts": fatigue_alerts,
        "yawns": yawns,
        "score": score,
        "date": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    })


def save_trip_summary(
    trip_time,
    fatigue_alerts,
    yawns,
    score
):
    _save_trip(
        trip_time,
        fatigue_alerts,
        yawns,
        score
    )

def update_location(lat, lng):

    ref = db.reference(
        "live_location"
    )

    ref.set({
        "latitude": lat,
        "longitude": lng
    })