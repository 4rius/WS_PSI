# Wrappear el Future en un PrioritizedItem para que pueda ser ordenado por la cola de prioridad
class PrioritizedItem:
    def __init__(self, priority, item):
        self.priority = priority
        self.item = item

    def __lt__(self, other):
        return self.priority < other.priority