import firebase_admin
from firebase_admin import db
from datetime import datetime

def save_trip_summary(
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
        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    })