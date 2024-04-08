import time

from Network import Logs
from Network.Logs import ThreadData
from Network.collections.DbConstants import VERSION


def log_activity(func):
    def wrapper(self, *args, **kwargs):
        start_time = time.time()  # Tiempo de inicio
        thread_data = ThreadData()
        Logs.start_logging(thread_data)
        result = func(self, *args, **kwargs)  # Ejecución de la función
        end_time = time.time()  # Tiempo de finalización
        Logs.stop_logging(thread_data)
        device = args[0] if len(args) > 0 else None
        cs = args[1] if len(args) > 1 else None
        activity_code = func.__name__.upper() + ("_" + cs.imp_name if cs is not None else "")
        Logs.log_activity(thread_data, activity_code, end_time - start_time, VERSION, self.id, device)
        print(f"Activity {activity_code} took {end_time - start_time}s")
        return result

    return wrapper
