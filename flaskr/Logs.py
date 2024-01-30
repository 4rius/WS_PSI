import datetime
import os
import threading
import time

import psutil
import platform

from firebase import firebase

firebase = firebase.FirebaseApplication('https://tfg-en-psi-default-rtdb.europe-west1.firebasedatabase.app/', None)

cpu_usage = []
ram_usage = []
avg_cpu_usage = 0
avg_ram_usage = 0
peak_cpu_usage = 0
peak_ram_usage = 0
logging_ram_usage = False
logging_cpu_usage = False


def clean_variables():
    global cpu_usage, ram_usage, avg_cpu_usage, avg_ram_usage, peak_cpu_usage, peak_ram_usage
    cpu_usage = []
    ram_usage = []
    avg_cpu_usage = 0
    avg_ram_usage = 0
    peak_cpu_usage = 0
    peak_ram_usage = 0


def log_activity(activity_code, time, version, id, peer=False):
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
            "RAM": get_ram_info(),
            "Peak_RAM": str(peak_ram_usage) + " MB",
            "CPU": str(avg_cpu_usage) + "% - " + get_cpu_info(),
            "Peak_CPU": str(peak_cpu_usage) + "%",
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
            "Avg_RAM": get_ram_info(),
            "Peak_RAM": str(peak_ram_usage) + " MB",
            "Avg_CPU": str(avg_cpu_usage) + "% - " + get_cpu_info(),
            "Peak_CPU": str(peak_cpu_usage) + "%",
            "Instance_RAM": get_instance_ram_usage(),
        }

    firebase.post(f"/logs/{formatted_id}/activities", log)
    print(f"Activity log sent to Firebase")

    clean_variables()


def get_ram_info():
    mem_info = psutil.virtual_memory()
    total_mem = round(mem_info.total / (1024 ** 2), 2)
    mem_use_percent = round(avg_ram_usage / total_mem * 100, 2)
    return f"{avg_ram_usage} MB / {total_mem} MB - {mem_use_percent}%"


def get_instance_ram_usage():
    pid = os.getpid()
    python_process = psutil.Process(pid)
    memory_info = round(python_process.memory_info().rss / (1024 ** 2), 2)
    return f"{memory_info} MB"


def get_cpu_info():
    cpu_info = psutil.cpu_freq().current / 1000, psutil.cpu_count()
    return f"{cpu_info[0]} GHz - {cpu_info[1]} cores"


def get_system_info():
    return f"{platform.platform()} - {platform.machine()}"


def get_logs(id):
    formatted_id = id.replace(".", "-")
    return firebase.get(f"/logs/{formatted_id}/activities", None)


def start_logging():
    global logging_cpu_usage, logging_ram_usage
    logging_cpu_usage = True
    logging_ram_usage = True
    thread = threading.Thread(target=log_cpu_usage)
    thread2 = threading.Thread(target=log_ram_usage)
    thread.start()
    thread2.start()


def stop_logging_cpu_usage():
    global logging_cpu_usage, avg_cpu_usage, cpu_usage, peak_cpu_usage
    logging_cpu_usage = False
    result = sum(cpu_usage) / len(cpu_usage)
    avg_cpu_usage = round(result, 2)
    peak_cpu_usage = round(max(cpu_usage), 2)
    return


def stop_logging_ram_usage():
    global logging_ram_usage, ram_usage, peak_ram_usage, avg_ram_usage
    logging_ram_usage = False
    result = sum(ram_usage) / len(ram_usage)
    avg_ram_usage = round(result, 2)
    peak_ram_usage = round(max(ram_usage), 2)
    return


def log_cpu_usage():
    global cpu_usage
    while logging_cpu_usage:
        cpu_usage.append(psutil.cpu_percent())
        time.sleep(0.1)


def log_ram_usage():
    global ram_usage
    while logging_ram_usage:
        ram_usage.append(psutil.virtual_memory().used / (1024 ** 2))
        time.sleep(0.1)
