from datetime import datetime
import csv
import os

def log_event(event):

    os.makedirs("logs", exist_ok=True)

    file_path = "logs/driver_log.csv"

    file_exists = os.path.isfile(file_path)

    with open(file_path, "a", newline="") as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["Time", "Event"])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event
        ])