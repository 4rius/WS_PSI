import firebase_admin
import datetime
import psutil
import platform

from firebase import firebase

firebase = firebase.FirebaseApplication('https://tfg-en-psi-default-rtdb.europe-west1.firebasedatabase.app/', None)


def log_activity(activity_code, time, version, id):
    formatted_id = id.replace(".", "-")

    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    log = {
        "id": id,
        "timestamp": timestamp,
        "version": version,
        "type": "Desktop (Flask): " + get_system_info(),
        "activity_code": activity_code,
        "time": round(time, 2),
        "RAM": get_ram_usage()
    }

    firebase.post(f"/logs/{formatted_id}/activities", log)

    print(f"Activity log sent to Firebase")


def get_ram_usage():
    mem_info = psutil.virtual_memory()
    total_mem = round(mem_info.total / (1024 ** 2), 2)
    available_mem = round(mem_info.available / (1024 ** 2), 2)
    mem_use = total_mem - available_mem
    mem_use_percent = round(mem_info.percent, 2)
    return f"{mem_use} MB / {total_mem} MB - {mem_use_percent}%"


def get_system_info():
    return f"{platform.platform()} - {platform.machine()}"


def get_stats(id):
    formatted_id = id.replace(".", "-")
    return firebase.get(f"/logs/{formatted_id}/activities", None)
