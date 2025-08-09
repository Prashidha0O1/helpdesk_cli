class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node

    def display(self):
        current = self.head
        history = []
        while current:
            history.append(str(current.data))
            current = current.next
        return "\n".join(history) if history else "No history yet."

    def to_list(self):
        current = self.head
        lst = []
        while current:
            # Serialize ticket objects using their to_dict if available
            data = current.data.to_dict() if hasattr(current.data, 'to_dict') else current.data
            lst.append(data)
            current = current.next
        return lst

    @classmethod
    def from_list(cls, lst):
        ll = cls()
        # Defer Ticket import to runtime to avoid circular imports
        try:
            from ticket import Ticket  # type: ignore
        except Exception:
            Ticket = None  # type: ignore
        for data in lst:
            if isinstance(data, dict) and Ticket is not None and 'ticket_id' in data:
                ll.append(Ticket.from_dict(data))
            else:
                ll.append(data)
        return ll
