import json
import os
import click

from ticket import Ticket
from LinkedList import LinkedList
from Stack import Stack, Queue, PriorityQueue

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


def _render_table(rows):
    # Determine column widths
    col_count = max(len(r) for r in rows)
    widths = [0] * col_count
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(str(cell)))

    def sep_line():
        parts = ["+" + "-" * (w + 2) for w in widths]
        return "".join(parts) + "+"

    def format_row(row):
        cells = []
        for i, w in enumerate(widths):
            text = str(row[i]) if i < len(row) else ""
            if i == 0:
                cells.append(f"| {text.ljust(w)} ")
            else:
                cells.append(f"| {text.rjust(w)} ")
        return "".join(cells) + "|"

    lines = [sep_line(), format_row(rows[0]), sep_line()]
    for r in rows[1:-1]:
        lines.append(format_row(r))
    if len(rows) > 1:
        lines.append(sep_line())
        lines.append(format_row(rows[-1]))
    lines.append(sep_line())
    return "\n".join(lines)

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

    headers = ["Priority", "Open", "Closed", "Resolved %"]
    data_rows = []
    total_open = 0
    total_closed = 0
    for row in dashboard[1:]:
        priority_label = row[0]
        open_count = int(row[1])
        closed_count = int(row[2])
        total = open_count + closed_count
        resolved_pct = f"{(closed_count / total * 100):.0f}%" if total > 0 else "0%"
        data_rows.append([priority_label, str(open_count), str(closed_count), resolved_pct])
        total_open += open_count
        total_closed += closed_count

    total_all = total_open + total_closed
    total_pct = f"{(total_closed / total_all * 100):.0f}%" if total_all > 0 else "0%"
    total_row = ["Total", str(total_open), str(total_closed), total_pct]

    table = _render_table([headers] + data_rows + [total_row])
    click.echo(table)

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


if __name__ == '__main__':
    cli()
