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
        result = []
        for t in self.items:
            result.append(t.to_dict() if hasattr(t, 'to_dict') else t)
        return result

    @classmethod
    def from_list(cls, lst):
        q = cls()
        try:
            from ticket import Ticket  # type: ignore
        except Exception:
            Ticket = None  # type: ignore
        for data in lst:
            if isinstance(data, dict) and Ticket is not None and 'ticket_id' in data:
                q.enqueue(Ticket.from_dict(data))
            else:
                q.enqueue(data)
        return q

priority_map = {'high': 0, 'medium': 1, 'low': 2}

class PriorityQueue:
    def __init__(self):
        self.heap = []

    def enqueue(self, ticket):
        import heapq as _heapq
        _heapq.heappush(self.heap, (priority_map[ticket.priority], ticket.created_at.timestamp(), ticket.ticket_id, ticket))

    def dequeue(self):
        if self.heap:
            import heapq as _heapq
            return _heapq.heappop(self.heap)[3]
        return None

    def is_empty(self):
        return len(self.heap) == 0

    def to_list(self):
        # Sort to serialize, but heap is not ordered, so extract all
        import heapq as _heapq
        temp_heap = self.heap[:]
        lst = []
        while temp_heap:
            _, _, _, ticket = _heapq.heappop(temp_heap)
            lst.append(ticket.to_dict())
        return lst

    @classmethod
    def from_list(cls, lst):
        pq = cls()
        try:
            from ticket import Ticket  # type: ignore
        except Exception:
            Ticket = None  # type: ignore
        for data in lst:
            if isinstance(data, dict) and Ticket is not None and 'ticket_id' in data:
                pq.enqueue(Ticket.from_dict(data))
            else:
                pq.enqueue(data)
        return pq
