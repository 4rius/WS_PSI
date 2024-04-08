import threading
import time
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue

from Network.PrioritizedItem import PrioritizedItem


# Solo funciona cuando se mandan tareas de distintas prioridades a la vez, si entran 1000 iguales seguidas,
# estas quedarán en la cola del ThreadPoolExecutor real
class PriorityExecutor:
    def __init__(self, max_workers):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.queue = PriorityQueue()
        self.max_tasks_in_queue = 10
        self.tasks_in_progress = 0  # Max should be max_workers + max_tasks_in_queue
        self._start_thread()  # Iniciamos el hilo que coge tareas de la cola de prioridad y las ejecuta

    def _start_thread(self):
        def function():
            while True:
                # De esta forma podemos evitar que la cola se llene de tareas de la misma prioridad
                # Dejamos 10 tareas en la cola para mejorar la eficiencia
                if not self.queue.empty() and self.tasks_in_progress < self.max_tasks_in_queue + self.max_workers:
                    prioritized_item = self.queue.get()  # Obtiene el elemento de mayor prioridad de la cola
                    if prioritized_item is not None:
                        # Ejecuta la tarea
                        func, args, kwargs = prioritized_item.item
                        future = self.executor.submit(func, *args, **kwargs)
                        self.tasks_in_progress += 1
                        # Marcar la tarea como completada y liberar espacio en la cola
                        future.add_done_callback(lambda x: self.task_done())
                        self.queue.task_done()
                else:
                    # Si la cola está vacía, esperamos un tiempo para no consumir CPU
                    time.sleep(0.1)

        threading.Thread(target=function).start()

    # Para enviar las tareas al ejecutor
    def submit(self, priority, func, *args, **kwargs):
        # Se añade la tarea a la cola de prioridad
        self.queue.put(PrioritizedItem(priority, (func, args, kwargs)))

    def task_done(self):
        self.tasks_in_progress -= 1
