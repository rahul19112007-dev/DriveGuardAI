import cv2 # type: ignore
import mediapipe as mp # type: ignore
import time

import firebase_logger # type: ignore
from firebase_logger import save_trip_summary
from telegram_alert import send_alert
from firebase_logger import (
    update_status,
    update_location
)
from gps_logger import get_location

cached_location = get_location()

from eye_detector import get_average_ear
from yawn_detector import calculate_mar
from alarm import start_alarm, stop_alarm
from logger import log_event

EAR_THRESHOLD = 0.20
MAR_THRESHOLD = 0.30
DROWSY_TIME = 2

ear_history = []
mar_history = []

closed_start = None
yawn_start = None

drowsy_logged = False
yawn_logged = False

driver_score = 100
drowsy_count = 0
yawn_count = 0
last_recovery_time = time.time()

session_start = time.time()
face_missing_start = None
last_recovery_time = time.time()
last_status_update = time.time()
last_gps_update = time.time()

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (480, 360))

    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    alarm_needed = False
    elapsed_session = int(time.time() - session_start)

    minutes = elapsed_session // 60
    seconds = elapsed_session % 60
    session_text = f"{minutes:02}:{seconds:02}"

   
    cv2.putText(
        frame,
        "DRIVEGUARD AI",
        (20, 35),
        cv2.FONT_HERSHEY_DUPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Time: {session_text}",
        (20, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1
    )

    if results.multi_face_landmarks:
        face_missing_start = None

        for face_landmarks in results.multi_face_landmarks:

            # Face Box
            x_coords = [int(lm.x * w) for lm in face_landmarks.landmark]
            y_coords = [int(lm.y * h) for lm in face_landmarks.landmark]

            x_min = min(x_coords)
            x_max = max(x_coords)
            y_min = min(y_coords)
            y_max = max(y_coords)
            cv2.putText(
                frame,
                "DRIVER",
                (x_min, y_min - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0,255,255),
                1
            )

            corner = 25
            thickness = 2

            # Top Left
            cv2.line(frame, (x_min, y_min), (x_min + corner, y_min), (0,255,255), thickness)
            cv2.line(frame, (x_min, y_min), (x_min, y_min + corner), (0,255,255), thickness)

            # Top Right
            cv2.line(frame, (x_max, y_min), (x_max - corner, y_min), (0,255,255), thickness)
            cv2.line(frame, (x_max, y_min), (x_max, y_min + corner), (0,255,255), thickness)

            # Bottom Left
            cv2.line(frame, (x_min, y_max), (x_min + corner, y_max), (0,255,255), thickness)
            cv2.line(frame, (x_min, y_max), (x_min, y_max - corner), (0,255,255), thickness)

            # Bottom Right
            cv2.line(frame, (x_max, y_max), (x_max - corner, y_max), (0,255,255), thickness)
            cv2.line(frame, (x_max, y_max), (x_max, y_max - corner), (0,255,255), thickness)

            # Eye Detection
            ear, left_eye, right_eye = get_average_ear(
                face_landmarks,
                w,
                h
            )

            ear_history.append(ear)

            if len(ear_history) > 5:
                ear_history.pop(0)

            ear = sum(ear_history) / len(ear_history)

            cv2.putText(
                frame,
                f"EAR: {ear:.2f}",
                (300, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            if ear < EAR_THRESHOLD:
                eye_status = "EYES CLOSED"
                eye_color = (0, 0, 255)
                if closed_start is None:
                    closed_start = time.time()

                elapsed = time.time() - closed_start

                cv2.putText(
                    frame,
                    f"Eye Closure Duration : {elapsed:.1f}s",
                    (20, 240),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 165, 255),
                    2
                )

                if elapsed >= DROWSY_TIME:
                    cv2.putText(
                        frame,
                        "DRIVER FATIGUE ALERT",
                        (20, 270),
                        cv2.FONT_HERSHEY_DUPLEX,
                        0.75,
                        (0, 0, 255),
                        2
                    )

                    if not drowsy_logged:
                        log_event("Driver Fatigue")

                        firebase_logger.log_to_firebase(
                            "Driver Fatigue",
                            driver_score
                        )

                        send_alert(
    "Driver eyes closed",
    driver_score,
    cached_location
)

                        drowsy_count += 1
                        driver_score = max(0, driver_score - 10)

                        drowsy_logged = True

                    alarm_needed = True
            else:
                eye_status = "EYES OPEN"
                eye_color = (0, 255, 0)
                closed_start = None
                drowsy_logged = False

            cv2.putText(
                frame,
                eye_status,
                (300, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                eye_color,
                2
            )

            # Yawn Detection
            mar, mouth_points = calculate_mar(
                face_landmarks,
                w,
                h
            )

            mar_history.append(mar)

            if len(mar_history) > 5:
                mar_history.pop(0)

            mar = sum(mar_history) / len(mar_history)

            cv2.putText(
                frame,
                f"MAR: {mar:.2f}",
                (300, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            if mar > MAR_THRESHOLD:
                if yawn_start is None:
                    yawn_start = time.time()

                yawn_duration = time.time() - yawn_start

                cv2.putText(
                    frame,
                    f"Yawn Duration : {yawn_duration:.1f}s",
                    (20, 320),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 165, 255),
                    2
                )

                if yawn_duration >= 1.2:
                    cv2.putText(
                        frame,
                        "FATIGUE SIGN DETECTED",
                        (20, 290),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (0, 165, 255),
                        2
                    )

                    if not yawn_logged:
                        log_event("Fatigue Indicator")
                        firebase_logger.log_to_firebase(
                            "Excessive Yawning",
                            driver_score
                        )
                        yawn_count += 1
                        driver_score = max(0, driver_score - 2)

                        send_alert(
    "Excessive yawning",
    driver_score,
    cached_location
)

                        yawn_logged = True

                    alarm_needed = True
            else:
                yawn_start = None
                yawn_logged = False
    else:
        cv2.putText(
            frame,
            "NO DRIVER DETECTED",
            (20, 220),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 165, 255),
            2
        )

        if face_missing_start is None:
            face_missing_start = time.time()
        elif time.time() - face_missing_start >= 60:
            session_start = time.time()
            driver_score = 100
            yawn_count = 0
            drowsy_count = 0
            face_missing_start = None
            alarm_needed = False

    # Recovery when driver is present and no alarm
    current_time = time.time()
    if (
        not alarm_needed
        and results.multi_face_landmarks
        and current_time - last_recovery_time >= 60
    ):
        driver_score = min(100, driver_score + 5)
        last_recovery_time = current_time

    if alarm_needed:
        start_alarm()
    else:
        stop_alarm()

    if driver_score >= 80:
        status = "ATTENTIVE"
    elif driver_score >= 50:
        status = "FATIGUED"
    else:
        status = "CRITICAL"

    if time.time() - last_status_update >= 30:
        update_status(
            status,
            driver_score
        )
        last_status_update = time.time()

    if time.time() - last_gps_update >= 30:
        location = get_location()

        if location:
            update_location(
                location["lat"],
                location["lng"]
            )

        last_gps_update = time.time()

    if status == "ATTENTIVE":
        status_color = (0, 255, 0)
    elif status == "FATIGUED":
        status_color = (0, 255, 255)
    else:
        status_color = (0, 0, 255)

    cv2.putText(
        frame,
        f"STATUS : {status}",
        (20, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        status_color,
        2
    )

    cv2.putText(
        frame,
        f"Score: {driver_score}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1
    )

    cv2.putText(
        frame,
        f"Fatigue Alerts: {drowsy_count}",
        (20, 140),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1
    )

    cv2.putText(
        frame,
        f"Fatigue Signs: {yawn_count}",
        (20, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1
    )

    cv2.imshow("DriveGuard AI v1.0", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

trip_time = int(
    (time.time() - session_start) / 60
)

save_trip_summary(
    trip_time,
    drowsy_count,
    yawn_count,
    driver_score
)


cap.release()
cv2.destroyAllWindows()
stop_alarm()