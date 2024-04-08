import threading
import time
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue

from Network.PrioritizedItem import PrioritizedItem


class PriorityExecutor:
    def __init__(self, max_workers):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.queue = PriorityQueue()
        self._start_thread()  # Iniciamos el hilo que coge tareas de la cola de prioridad y las ejecuta

    def _start_thread(self):
        def function():
            while True:
                if not self.queue.empty():
                    prioritized_item = self.queue.get()  # Obtiene el elemento de mayor prioridad de la cola
                    if prioritized_item is not None:
                        # Ejecuta la tarea
                        func, args, kwargs = prioritized_item.item
                        self.executor.submit(func, *args, **kwargs)
                        self.queue.task_done()
                else:
                    # Si la cola está vacía, esperamos un tiempo para no consumir CPU
                    time.sleep(0.1)

        threading.Thread(target=function).start()

    # Para enviar las tareas al ejecutor
    def submit(self, priority, func, *args, **kwargs):
        # Se añade la tarea a la cola de prioridad
        self.queue.put(PrioritizedItem(priority, (func, args, kwargs)))
