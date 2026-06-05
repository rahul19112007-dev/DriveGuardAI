import winsound

alarm_running = False

def start_alarm():
    global alarm_running

    if not alarm_running:
        winsound.PlaySound(
            "assets/alarm.wav",
            winsound.SND_FILENAME |
            winsound.SND_ASYNC |
            winsound.SND_LOOP
        )
        alarm_running = True

def stop_alarm():
    global alarm_running

    winsound.PlaySound(None, winsound.SND_PURGE)
    alarm_running = False