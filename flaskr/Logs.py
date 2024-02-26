import datetime
import os
import threading
import time

import psutil
import platform

from firebase import firebase

firebase = firebase.FirebaseApplication('https://tfg-en-psi-default-rtdb.europe-west1.firebasedatabase.app/', None)


class ThreadData:
    def __init__(self):
        self.cpu_usage = []
        self.ram_usage = []
        self.instance_ram_usage = []
        self.instance_cpu_usage = []
        self.avg_cpu_usage = 0
        self.avg_ram_usage = 0
        self.avg_instance_ram_usage = 0
        self.avg_instance_cpu_usage = 0
        self.peak_cpu_usage = 0
        self.peak_ram_usage = 0
        self.peak_instance_ram_usage = 0
        self.peak_instance_cpu_usage = 0
        self.stop_event = threading.Event()


def log_activity(thread_data, activity_code, time, version, id, peer=False):
    formatted_id = id.replace(".", "-")
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log = {
        "id": id,
        "timestamp": timestamp,
        "version": version,
        "type": "Desktop (Flask): " + get_system_info(),
        "activity_code": activity_code,
        "time": round(time, 2),
        "Avg_RAM": get_ram_info(thread_data),
        "Peak_RAM": str(thread_data.peak_ram_usage) + " MB",
        "Avg_instance_RAM": str(thread_data.avg_instance_ram_usage) + " MB",
        "Peak_instance_RAM": str(thread_data.peak_instance_ram_usage) + " MB",
        "Avg_CPU": str(
            thread_data.avg_cpu_usage) + "% - " + get_cpu_info() if thread_data.avg_cpu_usage != 0 or None else "N/A",
        "Peak_CPU": str(thread_data.peak_cpu_usage) + "%",
        "Avg_instance_CPU": str(thread_data.avg_instance_cpu_usage) + "%",
        "Peak_instance_CPU": str(thread_data.peak_instance_cpu_usage) + "%",
    }
    if peer:
        log["peer"] = peer

    firebase.post(f"/logs/{formatted_id}/activities", log)
    print(f"Activity log sent to Firebase")


def get_ram_info(thread_data):
    mem_info = psutil.virtual_memory()
    total_mem = round(mem_info.total / (1024 ** 2), 2)
    mem_use_percent = round(thread_data.avg_ram_usage / total_mem * 100, 2)
    return f"{thread_data.avg_ram_usage} MB / {total_mem} MB - {mem_use_percent}%"


def get_cpu_info():
    cpu_info = psutil.cpu_freq().current / 1000, psutil.cpu_count()
    return f"{cpu_info[0]} GHz - {cpu_info[1]} cores"


def get_system_info():
    return f"{platform.platform()} - {platform.machine()}"


def get_logs(id):
    formatted_id = id.replace(".", "-")
    return firebase.get(f"/logs/{formatted_id}/activities", None)


def start_logging(thread_data):
    # Iniciar los hilos de registro
    threads = [threading.Thread(target=log_instance_ram_usage, args=(thread_data,)),
               threading.Thread(target=log_instance_cpu_usage, args=(thread_data,)),
               threading.Thread(target=log_cpu_usage, args=(thread_data,)),
               threading.Thread(target=log_ram_usage, args=(thread_data,))]
    for t in threads:
        t.start()


def stop_logging(thread_data):
    thread_data.stop_event.set()
    stop_logging_cpu_usage(thread_data)
    stop_logging_ram_usage(thread_data)


def stop_logging_cpu_usage(thread_data):
    result = sum(thread_data.cpu_usage) / len(thread_data.cpu_usage) if len(thread_data.cpu_usage) != 0 else 0
    thread_data.avg_cpu_usage = round(result, 2) if len(thread_data.cpu_usage) != 0 else 0
    thread_data.peak_cpu_usage = round(max(thread_data.cpu_usage), 2) if len(thread_data.cpu_usage) != 0 else 0
    # If len(instance_cpu_usage) == 0, the result will be Na
    if len(thread_data.instance_cpu_usage) == 0:
        thread_data.avg_instance_cpu_usage = 0
        thread_data.peak_instance_cpu_usage = 0
        return
    result = sum(thread_data.instance_cpu_usage) / len(thread_data.instance_cpu_usage)
    thread_data.avg_instance_cpu_usage = round(result, 2)
    thread_data.peak_instance_cpu_usage = round(max(thread_data.instance_cpu_usage), 2)
    return


def stop_logging_ram_usage(thread_data):
    result = sum(thread_data.ram_usage) / len(thread_data.ram_usage)
    thread_data.avg_ram_usage = round(result, 2)
    thread_data.peak_ram_usage = round(max(thread_data.ram_usage), 2)
    result = sum(thread_data.instance_ram_usage) / len(thread_data.instance_ram_usage)
    thread_data.avg_instance_ram_usage = round(result, 2)
    thread_data.peak_instance_ram_usage = round(max(thread_data.instance_ram_usage), 2)
    return


def log_cpu_usage(thread_data):
    while not thread_data.stop_event.is_set():
        thread_data.cpu_usage.append(psutil.cpu_percent(interval=0.05))
    return


def log_ram_usage(thread_data):
    while not thread_data.stop_event.is_set():
        thread_data.ram_usage.append(psutil.virtual_memory().used / (1024 ** 2))
        time.sleep(0.05)
    return


def log_instance_ram_usage(thread_data):
    pid = os.getpid()
    python_process = psutil.Process(pid)
    while not thread_data.stop_event.is_set():
        memory_info = round(python_process.memory_info().rss / (1024 ** 2), 2)
        thread_data.instance_ram_usage.append(memory_info)
        time.sleep(0.05)
    return


def log_instance_cpu_usage(thread_data):
    pid = os.getpid()
    python_process = psutil.Process(pid)
    while not thread_data.stop_event.is_set():
        percent = python_process.cpu_percent(interval=0.05)
        thread_data.instance_cpu_usage.append(percent)
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
