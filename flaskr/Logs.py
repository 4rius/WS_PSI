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
instance_ram_usage = []
instance_cpu_usage = []
avg_cpu_usage = 0
avg_ram_usage = 0
avg_instance_ram_usage = 0
avg_instance_cpu_usage = 0
peak_cpu_usage = 0
peak_ram_usage = 0
peak_instance_ram_usage = 0
peak_instance_cpu_usage = 0
logging_ram_usage = False
logging_cpu_usage = False
lock = threading.Lock()
active_threads = 0


def clean_variables():
    if active_threads == 1:
        global cpu_usage, ram_usage, avg_cpu_usage, avg_ram_usage, peak_cpu_usage, peak_ram_usage
        cpu_usage = []
        ram_usage = []
        avg_cpu_usage = 0
        avg_ram_usage = 0
        peak_cpu_usage = 0
        peak_ram_usage = 0


def log_activity(activity_code, time, version, id, peer=False):
    global active_threads
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
            "Avg_RAM": get_ram_info(),
            "Peak_RAM": str(peak_ram_usage) + " MB",
            "Avg_instance_RAM": str(avg_instance_ram_usage) + " MB",
            "Peak_instance_RAM": str(peak_instance_ram_usage) + " MB",
            "Avg_CPU": str(avg_cpu_usage) + "% - " + get_cpu_info() if avg_cpu_usage != 0 or None else "N/A",
            "Peak_CPU": str(peak_cpu_usage) + "%",
            "Avg_instance_CPU": str(avg_instance_cpu_usage) + "%",
            "Peak_instance_CPU": str(peak_instance_cpu_usage) + "%"
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
            "Avg_instance_RAM": str(avg_instance_ram_usage) + " MB",
            "Peak_instance_RAM": str(peak_instance_ram_usage) + " MB",
            "Avg_CPU": str(avg_cpu_usage) + "% - " + get_cpu_info() if avg_cpu_usage != 0 or None else "N/A",
            "Peak_CPU": str(peak_cpu_usage) + "%",
            "Avg_instance_CPU": str(avg_instance_cpu_usage) + "%",
            "Peak_instance_CPU": str(peak_instance_cpu_usage) + "%"
        }

    firebase.post(f"/logs/{formatted_id}/activities", log)
    print(f"Activity log sent to Firebase")

    clean_variables()
    active_threads -= 1
    print(f"Active threads: {active_threads}")


def get_ram_info():
    mem_info = psutil.virtual_memory()
    total_mem = round(mem_info.total / (1024 ** 2), 2)
    mem_use_percent = round(avg_ram_usage / total_mem * 100, 2)
    return f"{avg_ram_usage} MB / {total_mem} MB - {mem_use_percent}%"


def get_instance_ram_usage():
    pid = os.getpid()
    python_process = psutil.Process(pid)
    memory_info = round(python_process.memory_info().rss / (1024 ** 2), 2)
    return memory_info


def get_instance_cpu_usage():
    pid = os.getpid()
    python_process = psutil.Process(pid)
    return python_process.cpu_percent(interval=1)


def get_cpu_info():
    cpu_info = psutil.cpu_freq().current / 1000, psutil.cpu_count()
    return f"{cpu_info[0]} GHz - {cpu_info[1]} cores"


def get_system_info():
    return f"{platform.platform()} - {platform.machine()}"


def get_logs(id):
    formatted_id = id.replace(".", "-")
    return firebase.get(f"/logs/{formatted_id}/activities", None)


def start_logging():
    global logging_cpu_usage, logging_ram_usage, active_threads
    logging_cpu_usage = True
    logging_ram_usage = True
    threads = [threading.Thread(target=log_cpu_usage), threading.Thread(target=log_ram_usage), threading.Thread(target=log_instance_ram_usage), threading.Thread(target=log_instance_cpu_usage)]
    for t in threads:
        t.start()
    with lock:
        active_threads += 1


def stop_logging_cpu_usage():
    global logging_cpu_usage, avg_cpu_usage, cpu_usage, peak_cpu_usage, avg_instance_cpu_usage, peak_instance_cpu_usage, instance_cpu_usage
    logging_cpu_usage = False
    result = sum(cpu_usage) / len(cpu_usage)
    avg_cpu_usage = round(result, 2)
    peak_cpu_usage = round(max(cpu_usage), 2)
    # If len(instance_cpu_usage) == 0, the result will be Na
    if len(instance_cpu_usage) == 0:
        avg_instance_cpu_usage = 0
        peak_instance_cpu_usage = 0
        return
    result = sum(instance_cpu_usage) / len(instance_cpu_usage)
    avg_instance_cpu_usage = round(result, 2)
    peak_instance_cpu_usage = round(max(instance_cpu_usage), 2)
    return


def stop_logging_ram_usage():
    global logging_ram_usage, ram_usage, peak_ram_usage, avg_ram_usage, instance_ram_usage, avg_instance_ram_usage, peak_instance_ram_usage
    logging_ram_usage = False
    result = sum(ram_usage) / len(ram_usage)
    avg_ram_usage = round(result, 2)
    peak_ram_usage = round(max(ram_usage), 2)
    result = sum(instance_ram_usage) / len(instance_ram_usage)
    avg_instance_ram_usage = round(result, 2)
    peak_instance_ram_usage = round(max(instance_ram_usage), 2)
    return


def log_cpu_usage():
    global cpu_usage
    while logging_cpu_usage:
        cpu_usage.append(psutil.cpu_percent())
        time.sleep(0.1)
    return


def log_ram_usage():
    global ram_usage
    while logging_ram_usage:
        ram_usage.append(psutil.virtual_memory().used / (1024 ** 2))
        time.sleep(0.1)
    return


def log_instance_ram_usage():
    global instance_ram_usage
    while logging_ram_usage:
        instance_ram_usage.append(get_instance_ram_usage())
        time.sleep(0.1)
    return


def log_instance_cpu_usage():
    global instance_cpu_usage
    while logging_cpu_usage:
        instance_cpu_usage.append(get_instance_cpu_usage())
        time.sleep(0.1)
    return


def setup_logs(id, set_size, domain):
    formatted_id = id.replace(".", "-")
    log = {
        "id": id,
        "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "set_size": set_size,
        "domain": domain,
        "type": "Desktop (Flask): " + get_system_info()
    }
    firebase.post(f"/logs/{formatted_id}/setup", log)
    print(f"Log setup sent to Firebase")


def log_result(implementation, result, version, id, device):
    formatted_id = id.replace(".", "-")
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log = {
        "id": id,
        "timestamp": timestamp,
        "implementation": implementation,
        "result": result,
        "device": device,
        "version": version,
        "type": "Desktop (Flask): " + get_system_info()
    }
    firebase.post(f"/logs/{formatted_id}/results", log)
    print(f"Result log sent to Firebase")
    return