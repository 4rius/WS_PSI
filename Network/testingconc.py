import threading
import time
from queue import PriorityQueue
from concurrent.futures import ThreadPoolExecutor

class PrioritizedItem:
    def __init__(self, priority, item):
        self.priority = priority
        self.item = item

    def __lt__(self, other):
        return self.priority < other.priority

class PriorityExecutor:
    def __init__(self, max_workers):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.queue = PriorityQueue()
        self._stop_event = threading.Event()  # Evento para señalar que se debe detener el hilo
        self._start_thread()

    def _start_thread(self):
        def function():
            while not self._stop_event.is_set():
                if not self.queue.empty():
                    prioritized_item = self.queue.get()
                    if prioritized_item is not None:
                        func, args, kwargs = prioritized_item.item
                        self.executor.submit(func, *args, **kwargs)
                        self.queue.task_done()
                else:
                    time.sleep(0.1)

        threading.Thread(target=function).start()

    def submit(self, priority, func, *args, **kwargs):
        self.queue.put(PrioritizedItem(priority, (func, args, kwargs)))

    def shutdown(self):
        self._stop_event.set()  # Señaliza al hilo que debe detenerse
        self.executor.shutdown()


def test_function(name):
    print("PriorityExecutor test function - name: ", name)

executor = PriorityExecutor(2)
executor.submit(2, test_function, "2")
executor.submit(3, test_function , "3")
executor.submit(0, test_function , "0")
executor.submit(1, test_function , "1")
time.sleep(1)
executor.shutdown()