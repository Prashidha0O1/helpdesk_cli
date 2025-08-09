class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if self.items:
            return self.items.pop()
        return None

    def is_empty(self):
        return len(self.items) == 0

    def to_list(self):
        return self.items[:]  # Copy

    @classmethod
    def from_list(cls, lst):
        stack = cls()
        stack.items = lst[:]
        return stack

class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if self.items:
            return self.items.pop(0)
        return None

    def is_empty(self):
        return len(self.items) == 0

    def to_list(self):
        return [t.to_dict() for t in self.items]

    @classmethod
    def from_list(cls, lst):
        q = cls()
        for data in lst:
            q.enqueue(Ticket.from_dict(data))
        return q

priority_map = {'high': 0, 'medium': 1, 'low': 2}

class PriorityQueue:
    def __init__(self):
        self.heap = []

    def enqueue(self, ticket):
        heapq.heappush(self.heap, (priority_map[ticket.priority], ticket.created_at.timestamp(), ticket.ticket_id, ticket))

    def dequeue(self):
        if self.heap:
            return heapq.heappop(self.heap)[3]
        return None

    def is_empty(self):
        return len(self.heap) == 0

    def to_list(self):
        # Sort to serialize, but heap is not ordered, so extract all
        temp_heap = self.heap[:]
        lst = []
        while temp_heap:
            _, _, _, ticket = heapq.heappop(temp_heap)
            lst.append(ticket.to_dict())
        return lst

    @classmethod
    def from_list(cls, lst):
        pq = cls()
        for data in lst:
            pq.enqueue(Ticket.from_dict(data))
        return pq
