import json
import os
import datetime
from typing import List, Dict, Any, Optional
import click

from ticket import Ticket
from LinkedList import LinkedList
from Stack import Stack, Queue, PriorityQueue
try:
    from session import get_current_user, login as session_login, logout as session_logout
except Exception:  # Fallbacks if session module missing
    def get_current_user():
        return None
    def session_login(*args, **kwargs):
        return None
    def session_logout():
        return False

try:
    # Optional UI enhancements with Rich
    from ui import render_user_dashboard, render_admin_dashboard
    _HAS_UI = True
except Exception:
    _HAS_UI = False

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
        current_user = get_current_user()
        owner_id = current_user.get('user_id') if current_user else None
        ticket = Ticket(
            self.next_id,
            description,
            priority,
            parent_id,
            owner_user_id=owner_id,
            assigned_to_user_id=None,
            tags=[],
        )
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

    # Assignment and tagging
    def assign_ticket(self, ticket_id: int, user_id: str) -> bool:
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return False
        previous_assignee = ticket.assigned_to_user_id
        ticket.assigned_to_user_id = user_id
        self.undo_stack.push({'action': 'assign', 'ticket_id': ticket_id, 'prev_assigned': previous_assignee})
        self.save_state()
        return True

    def tag_ticket(self, ticket_id: int, tags: List[str]) -> bool:
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return False
        previous_tags = list(ticket.tags)
        for t in tags:
            if t not in ticket.tags:
                ticket.tags.append(t)
        self.undo_stack.push({'action': 'tag', 'ticket_id': ticket_id, 'prev_tags': previous_tags})
        self.save_state()
        return True

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

    def analytics_extended(self) -> Dict[str, Any]:
        # SLA targets in hours by priority
        sla_hours = {'high': 4, 'medium': 24, 'low': 72}
        now = datetime.datetime.now()

        def ticket_age_hours(t: Ticket) -> float:
            ref = t.closed_at or now
            return max(0.0, (ref - t.created_at).total_seconds() / 3600)

        def bucket(age_h: float) -> str:
            if age_h < 24:
                return '0-24h'
            if age_h < 72:
                return '1-3d'
            if age_h < 168:
                return '3-7d'
            return '7d+'

        open_count = 0
        closed_count = 0
        breaches = 0
        by_priority = {'high': {'open': 0, 'closed': 0}, 'medium': {'open': 0, 'closed': 0}, 'low': {'open': 0, 'closed': 0}}
        aging_buckets = {'0-24h': 0, '1-3d': 0, '3-7d': 0, '7d+': 0}

        for t in self.tickets.values():
            pr = t.priority.lower()
            if t.status == 'open':
                open_count += 1
                by_priority[pr]['open'] += 1
                age_h = ticket_age_hours(t)
                aging_buckets[bucket(age_h)] += 1
                if age_h > sla_hours.get(pr, 24):
                    breaches += 1
            else:
                closed_count += 1
                by_priority[pr]['closed'] += 1

        total = open_count + closed_count
        sla_pct = 0 if (open_count == 0 and closed_count == 0) else int(round(100 * (1 - (breaches / (open_count or 1))), 0))
        return {
            'totals': {'open': open_count, 'closed': closed_count},
            'by_priority': by_priority,
            'aging_buckets': aging_buckets,
            'sla': {'targets_h': sla_hours, 'open_breaches': breaches, 'sla_pct_estimate': sla_pct},
        }

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
        elif action['action'] == 'assign':
            ticket_id = action['ticket_id']
            if ticket_id in self.tickets:
                self.tickets[ticket_id].assigned_to_user_id = action.get('prev_assigned')
        elif action['action'] == 'tag':
            ticket_id = action['ticket_id']
            if ticket_id in self.tickets:
                self.tickets[ticket_id].tags = action.get('prev_tags', [])
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

def _format_ticket_row(t: Ticket) -> List[str]:
    age_h = int((datetime.datetime.now() - t.created_at).total_seconds() // 3600)
    owner = t.owner_user_id or '-'
    assignee = t.assigned_to_user_id or '-'
    tags = ",".join(t.tags) if t.tags else '-'
    return [
        f"#{t.ticket_id}",
        t.priority.capitalize(),
        t.status.capitalize(),
        f"{age_h}h",
        owner,
        assignee,
        (t.description[:40] + '…') if len(t.description) > 40 else t.description,
        tags,
    ]

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

    ext = system.analytics_extended()
    click.echo("\nAging buckets:")
    ab_rows = [["Bucket", "Count"]] + [[k, str(v)] for k, v in ext['aging_buckets'].items()]
    click.echo(_render_table(ab_rows))
    click.echo("\nSLA:")
    click.echo(_render_table([["Metric", "Value"], ["Open breaches", str(ext['sla']['open_breaches'])], ["SLA % (est)", f"{ext['sla']['sla_pct_estimate']}%"]]))

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


@cli.command(help='Login to create a local session')
@click.option('--user-id', required=True, help='Unique user id')
@click.option('--name', required=True, help='Display name')
@click.option('--role', type=click.Choice(['user', 'admin'], case_sensitive=False), default='user')
@click.option('--email', required=False)
def login(user_id, name, role, email):
    session = session_login(user_id=user_id, name=name, role=role, email=email)
    if session:
        click.echo(f"Logged in as {session['name']} ({session['role']})")
    else:
        click.echo("Login unavailable.")


@cli.command(help='Logout current session')
def logout():
    if session_logout():
        click.echo("Logged out.")
    else:
        click.echo("No active session.")


@cli.command(help='Show current user')
def whoami():
    user = get_current_user()
    if user:
        click.echo(f"{user['name']} ({user['user_id']}) role={user['role']}")
    else:
        click.echo("Not logged in.")


@cli.command(help='Assign a ticket to a user id')
@click.argument('ticket_id', type=int)
@click.option('--to', 'to_user', required=True, help='User id to assign to')
def assign(ticket_id, to_user):
    system = HelpDeskSystem()
    if system.assign_ticket(ticket_id, to_user):
        click.echo(f"Assigned #{ticket_id} to {to_user}.")
    else:
        click.echo("Ticket not found.")


@cli.command(help='Add tags to a ticket')
@click.argument('ticket_id', type=int)
@click.option('--add', 'tags', multiple=True, help='Tag to add (repeatable)')
def tag(ticket_id, tags):
    if not tags:
        click.echo("Provide at least one --add tag.")
        return
    system = HelpDeskSystem()
    if system.tag_ticket(ticket_id, list(tags)):
        click.echo(f"Tagged #{ticket_id}: {', '.join(tags)}")
    else:
        click.echo("Ticket not found.")


@cli.command(help='Show your tickets and analytics')
def my():
    user = get_current_user()
    if not user:
        click.echo("Not logged in. Use 'helpdesk login' first.")
        return
    system = HelpDeskSystem()
    mine = [t for t in system.tickets.values() if t.owner_user_id == user['user_id'] or t.assigned_to_user_id == user['user_id']]
    headers = ["ID", "Priority", "Status", "Age", "Owner", "Assignee", "Description", "Tags"]
    rows = [headers] + [_format_ticket_row(t) for t in sorted(mine, key=lambda x: (x.status, x.priority, x.created_at))]
    click.echo(_render_table(rows))
    ext = system.analytics_extended()
    click.echo("\nAt-a-glance:")
    click.echo(_render_table([["Open", str(ext['totals']['open'])], ["Closed", str(ext['totals']['closed'])]]))


@cli.command(help='Admin dashboard (analytics and queue health)')
def admin():
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        click.echo("Admin only. Login with role=admin.")
        return
    system = HelpDeskSystem()
    if _HAS_UI:
        render_admin_dashboard(system)
    else:
        ext = system.analytics_extended()
        click.echo("Queue Health:")
        click.echo(_render_table([["Open", str(ext['totals']['open'])], ["Closed", str(ext['totals']['closed'])], ["Open Breaches", str(ext['sla']['open_breaches'])], ["SLA % (est)", f"{ext['sla']['sla_pct_estimate']}%"]]))
        click.echo("\nAging buckets:")
        ab_rows = [["Bucket", "Count"]] + [[k, str(v)] for k, v in ext['aging_buckets'].items()]
        click.echo(_render_table(ab_rows))


@cli.command(help='Interactive UI (requires rich)')
def tui():
    system = HelpDeskSystem()
    user = get_current_user()
    if _HAS_UI:
        if user and user.get('role') == 'admin':
            render_admin_dashboard(system)
        else:
            render_user_dashboard(system, user)
    else:
        click.echo("Rich UI not available. Install extras: pip install interactive-helpdesk-cli[ui]")


if __name__ == '__main__':
    cli()
