from typing import Optional, TYPE_CHECKING
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box

from ticket import Ticket
if TYPE_CHECKING:  # avoid runtime import cycle
    from helpdesk import HelpDeskSystem  # pragma: no cover


console = Console()


def _ticket_table(tickets):
    table = Table(title="Tickets", box=box.SIMPLE_HEAVY)
    table.add_column("ID", justify="right")
    table.add_column("Priority")
    table.add_column("Status")
    table.add_column("Age")
    table.add_column("Owner")
    table.add_column("Assignee")
    table.add_column("Description")
    table.add_column("Tags")
    for t in tickets:
        age_h = int((__import__("datetime").datetime.now() - t.created_at).total_seconds() // 3600)
        table.add_row(
            f"#{t.ticket_id}",
            t.priority.capitalize(),
            t.status.capitalize(),
            f"{age_h}h",
            t.owner_user_id or "-",
            t.assigned_to_user_id or "-",
            (t.description[:60] + "…") if len(t.description) > 60 else t.description,
            ",".join(t.tags) if t.tags else "-",
        )
    return table


def _analytics_panels(system: 'HelpDeskSystem'):
    ext = system.analytics_extended()
    totals = Table(title="Totals", box=box.MINIMAL_DOUBLE_HEAD)
    totals.add_column("Metric")
    totals.add_column("Value", justify="right")
    totals.add_row("Open", str(ext['totals']['open']))
    totals.add_row("Closed", str(ext['totals']['closed']))

    sla = Table(title="SLA", box=box.MINIMAL_DOUBLE_HEAD)
    sla.add_column("Metric")
    sla.add_column("Value", justify="right")
    sla.add_row("Open breaches", str(ext['sla']['open_breaches']))
    sla.add_row("SLA % (est)", f"{ext['sla']['sla_pct_estimate']}%")

    aging = Table(title="Aging", box=box.MINIMAL_DOUBLE_HEAD)
    aging.add_column("Bucket")
    aging.add_column("Count", justify="right")
    for k, v in ext['aging_buckets'].items():
        aging.add_row(k, str(v))

    return Columns([Panel(totals, title=""), Panel(sla, title=""), Panel(aging, title="")])


def render_user_dashboard(system: 'HelpDeskSystem', user: Optional[dict]):
    console.rule("HelpDesk — User Dashboard")
    current_user_id = user['user_id'] if user else None
    mine = [t for t in system.tickets.values() if (t.owner_user_id == current_user_id) or (t.assigned_to_user_id == current_user_id)]
    mine_sorted = sorted(mine, key=lambda x: (x.status, x.priority, x.created_at))
    console.print(_ticket_table(mine_sorted))
    console.print(_analytics_panels(system))
    console.print(Panel("Commands: helpdesk create | assign | tag | close | analytics | history", title="Hints"))


def render_admin_dashboard(system: 'HelpDeskSystem'):
    console.rule("HelpDesk — Admin Dashboard")
    all_sorted = sorted(system.tickets.values(), key=lambda x: (x.status, x.priority, x.created_at))
    console.print(_ticket_table(all_sorted))
    console.print(_analytics_panels(system))
    console.print(Panel("Commands: helpdesk admin | analytics | process | assign | tag | undo", title="Hints"))


