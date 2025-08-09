import datetime 
import heapq
import json
import os
import click

class Ticket:
    def __init__(self, ticket_id, desc, priority, parent_id=None):
        self.ticket_id = ticket_id
        self.desc = desc
        self.status = 'open'
        self.priority = priority
        self.parent_id = parent_id
        self.created_at = datetime.datetime.now()
        self.closed_at = None
    
    def close(self):
        if self.status == 'open':
            self.status == 'closed'
            self.closed_at = datetime.datetime.datetime.now()
            return True
        return False 
    
    def __repr__(self):
        return f"Ticket {self.ticket_id}: ({self.desc}), ({self.priority}), (self.status)"

    def to_dict(self):
        return {
            'ticket_id': self.ticket_id,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat(),
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }

    @classmethod
    def from_dict(cls, data):
        ticket = cls(data['ticket_id'], data['description'], data['priority'], data['parent_id'])
        ticket.status = data['status']
        ticket.created_at = datetime.datetime.fromisoformat(data['created_at'])
        ticket.closed_at = datetime.datetime.fromisoformat(data['closed_at']) if data['closed_at'] else None
        return ticket
    

class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

