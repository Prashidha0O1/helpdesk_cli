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
    

class HelpDeskSystem:
    STATE_FILE = 'helpdesk_state.json'

    def __init__(self):
        self.tickets = {}  # ticket_id -> Ticket
        self.next_id = 1
        self.history = LinkedList()
        self.standard_queue = Queue()
        self.high_priority_queue = PriorityQueue()
        self.undo_stack = Stack()
        self.load_state()  # Load on init

    # Week 2: Recursion for checking dependencies
    def is_resolvable(self, ticket_id):
        if ticket_id not in self.tickets:
            return False
        ticket = self.tickets[ticket_id]
        if not ticket.parent_id:
            return True  # Assuming open is resolvable if no parent; but for close, we check status separately
        parent = self.tickets.get(ticket.parent_id)
        if not parent or parent.status != 'closed':
            return False
        return self.is_resolvable(parent.ticket_id)

    def create_ticket(self, description, priority='medium', parent_id=None):
        ticket = Ticket(self.next_id, description, priority, parent_id)
        self.tickets[self.next_id] = ticket
        self.history.append(ticket)
        if priority == 'high':
            self.high_priority_queue.enqueue(ticket)
        else:
            self.standard_queue.enqueue(ticket)
        self.undo_stack.push({'action': 'create', 'ticket_id': self.next_id})
        self.next_id += 1
        self.save_state()
        return ticket

    def close_ticket(self, ticket_id):
        if ticket_id in self.tickets:
            ticket = self.tickets[ticket_id]
            if self.is_resolvable(ticket_id) and ticket.close():
                self.undo_stack.push({'action': 'close', 'ticket_id': ticket_id, 'prev_status': 'open'})
                self.save_state()
                return True
        return False

    def process_next_ticket(self):
        if not self.high_priority_queue.is_empty():
            ticket = self.high_priority_queue.dequeue()
            self.save_state()
            return ticket
        elif not self.standard_queue.is_empty():
            ticket = self.standard_queue.dequeue()
            self.save_state()
            return ticket
        return None

    # Week 1: Analytics dashboard using 2D list
    def analytics_dashboard(self):
        stats = [
            ['Priority', 'Open', 'Closed'],
            ['High', 0, 0],
            ['Medium', 0, 0],
            ['Low', 0, 0]
        ]
        for ticket in self.tickets.values():
            row = {'high': 1, 'medium': 2, 'low': 3}[ticket.priority.lower()]
            col = 1 if ticket.status == 'open' else 2
            stats[row][col] += 1
        return stats

    def undo_last_action(self):
        action = self.undo_stack.pop()
        if not action:
            return False
        if action['action'] == 'create':
            ticket_id = action['ticket_id']
            if ticket_id in self.tickets:
                del self.tickets[ticket_id]
        elif action['action'] == 'close':
            ticket_id = action['ticket_id']
            if ticket_id in self.tickets:
                self.tickets[ticket_id].status = action['prev_status']
                self.tickets[ticket_id].closed_at = None
                ticket = self.tickets[ticket_id]
                if ticket.priority == 'high':
                    self.high_priority_queue.enqueue(ticket)
                else:
                    self.standard_queue.enqueue(ticket)
        self.save_state()
        return True

    def save_state(self):
        state = {
            'next_id': self.next_id,
            'tickets': {str(k): v.to_dict() for k, v in self.tickets.items()},
            'history': self.history.to_list(),
            'standard_queue': self.standard_queue.to_list(),
            'high_priority_queue': self.high_priority_queue.to_list(),
            'undo_stack': self.undo_stack.to_list()
        }
        with open(self.STATE_FILE, 'w') as f:
            json.dump(state, f, indent=4)

    def load_state(self):
        if os.path.exists(self.STATE_FILE):
            with open(self.STATE_FILE, 'r') as f:
                state = json.load(f)
            self.next_id = state['next_id']
            self.tickets = {int(k): Ticket.from_dict(v) for k, v in state['tickets'].items()}
            self.history = LinkedList.from_list(state['history'])
            self.standard_queue = Queue.from_list(state['standard_queue'])
            self.high_priority_queue = PriorityQueue.from_list(state['high_priority_queue'])
            self.undo_stack = Stack.from_list(state['undo_stack'])

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
    else:
        pass  # Subcommands will handle

@cli.command(help='Create a new ticket')
@click.option('--description', required=True, help='Ticket description')
@click.option('--priority', default='medium', type=click.Choice(['low', 'medium', 'high'], case_sensitive=False), help='Priority level')
@click.option('--parent', default=None, type=int, help='Parent ticket ID (optional)')
def create(description, priority, parent):
    system = HelpDeskSystem()
    ticket = system.create_ticket(description, priority, parent)
    click.echo(f"Created: {ticket}")

@cli.command(help='Close a ticket')
@click.argument('ticket_id', type=int)
def close(ticket_id):
    system = HelpDeskSystem()
    if system.close_ticket(ticket_id):
        click.echo("Ticket closed.")
    else:
        click.echo("Cannot close ticket.")

@cli.command(help='Process the next ticket')
def process():
    system = HelpDeskSystem()
    ticket = system.process_next_ticket()
    if ticket:
        click.echo(f"Processed: {ticket}")
    else:
        click.echo("No tickets to process.")

@cli.command(help='Check if a ticket is resolvable')
@click.argument('ticket_id', type=int)
def check(ticket_id):
    system = HelpDeskSystem()
    if system.is_resolvable(ticket_id):
        click.echo("Ticket is resolvable.")
    else:
        click.echo("Ticket has unresolved dependencies.")

@cli.command(help='View analytics dashboard')
def analytics():
    system = HelpDeskSystem()
    dashboard = system.analytics_dashboard()
    for row in dashboard:
        click.echo(" | ".join(map(str, row)))

@cli.command(help='View ticket history')
def history():
    system = HelpDeskSystem()
    click.echo("Ticket History:")
    click.echo(system.history.display())

@cli.command(help='Undo last action')
def undo():
    system = HelpDeskSystem()
    if system.undo_last_action():
        click.echo("Last action undone.")
    else:
        click.echo("No actions to undo.")
