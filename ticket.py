import datetime
from typing import Optional


class Ticket:
    def __init__(
        self,
        ticket_id: int,
        description: str,
        priority: str,
        parent_id: Optional[int] = None,
        owner_user_id: Optional[str] = None,
        assigned_to_user_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ):
        self.ticket_id = ticket_id
        self.description = description
        self.status = "open"
        self.priority = priority
        self.parent_id = parent_id
        self.owner_user_id = owner_user_id
        self.assigned_to_user_id = assigned_to_user_id
        self.tags: list[str] = tags or []
        self.created_at = datetime.datetime.now()
        self.closed_at: Optional[datetime.datetime] = None

    def close(self) -> bool:
        if self.status == "open":
            self.status = "closed"
            self.closed_at = datetime.datetime.now()
            return True
        return False

    def __repr__(self) -> str:
        return f"Ticket {self.ticket_id}: ({self.description}), ({self.priority}), ({self.status})"

    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "parent_id": self.parent_id,
            "owner_user_id": self.owner_user_id,
            "assigned_to_user_id": self.assigned_to_user_id,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ticket":
        ticket = cls(
            data["ticket_id"],
            data["description"],
            data["priority"],
            data.get("parent_id"),
            data.get("owner_user_id"),
            data.get("assigned_to_user_id"),
            data.get("tags") or [],
        )
        ticket.status = data["status"]
        ticket.created_at = datetime.datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.datetime.now()
        ticket.closed_at = (
            datetime.datetime.fromisoformat(data["closed_at"]) if data.get("closed_at") else None
        )
        return ticket

