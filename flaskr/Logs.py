import datetime
import os
import threading
import time

import psutil
import platform

from firebase import firebase

firebase = firebase.FirebaseApplication('https://tfg-en-psi-default-rtdb.europe-west1.firebasedatabase.app/', None)

cpu_usage = []
avg_cpu_usage = 0
logging_cpu_usage = False


def log_activity(activity_code, time, version, id, cpu_usage, peer=False):
    formatted_id = id.replace(".", "-")

    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if peer:
        log = {
            "id": id,
            "timestamp": timestamp,
            "version": version,
            "type": "Desktop (Flask): " + get_system_info(),
            "activity_code": activity_code,
            "peer": peer,
            "time": round(time, 2),
            "RAM": get_ram_usage(),
            "CPU": str(cpu_usage) + "% - " + get_cpu_usage(),
            "Instance_RAM": get_instance_ram_usage(),
        }
    else:
        log = {
            "id": id,
            "timestamp": timestamp,
            "version": version,
            "type": "Desktop (Flask): " + get_system_info(),
            "activity_code": activity_code,
            "time": round(time, 2),
            "RAM": get_ram_usage(),
            "CPU": str(cpu_usage) + "% - " + get_cpu_usage(),
            "Instance_RAM": get_instance_ram_usage(),
        }

    firebase.post(f"/logs/{formatted_id}/activities", log)

    print(f"Activity log sent to Firebase")


def get_ram_usage():
    mem_info = psutil.virtual_memory()
    total_mem = round(mem_info.total / (1024 ** 2), 2)
    available_mem = round(mem_info.available / (1024 ** 2), 2)
    mem_use = round(total_mem - available_mem, 2)
    mem_use_percent = round(mem_info.percent, 2)
    return f"{mem_use} MB / {total_mem} MB - {mem_use_percent}%"


def get_instance_ram_usage():
    pid = os.getpid()
    python_process = psutil.Process(pid)
    memory_info = round(python_process.memory_info().rss / (1024 ** 2), 2)
    return f"{memory_info} MB"


def get_cpu_usage():
    cpu_info = psutil.cpu_freq().current / 1000, psutil.cpu_count()
    return f"{cpu_info[0]} GHz - {cpu_info[1]} cores"


def get_system_info():
    return f"{platform.platform()} - {platform.machine()}"


def get_logs(id):
    formatted_id = id.replace(".", "-")
    return firebase.get(f"/logs/{formatted_id}/activities", None)


def start_logging_cpu_usage():
    global logging_cpu_usage
    logging_cpu_usage = True
    thread = threading.Thread(target=log_cpu_usage)
    thread.start()


def stop_logging_cpu_usage():
    global logging_cpu_usage, avg_cpu_usage, cpu_usage
    logging_cpu_usage = False
    avg_cpu_usage = sum(cpu_usage) / len(cpu_usage)
    result = avg_cpu_usage
    cpu_usage = []
    return round(result, 2)


def log_cpu_usage():
    global cpu_usage
    while logging_cpu_usage:
        cpu_usage.append(psutil.cpu_percent())
        time.sleep(0.1)
