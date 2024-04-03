from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue

from Network.PrioritizedItem import PrioritizedItem


class PriorityExecutor:
    def __init__(self, max_workers):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.queue = PriorityQueue()

    def submit(self, priority, func, *args, **kwargs):
        # Prioridad negativa para que el menor sea el mayor porque la cola de prioridad es min-heap
        self.queue.put(PrioritizedItem(-priority, self.executor.submit(func, *args, **kwargs)))

    def done(self):
        return self.queue.empty()
