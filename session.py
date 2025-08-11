import json
import os
from typing import Optional, Dict, Any


SESSION_FILE = "helpdesk_session.json"


def _read_file(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_file(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def get_current_user() -> Optional[Dict[str, Any]]:
    return _read_file(SESSION_FILE)


def login(user_id: str, name: str, role: str = "user", email: Optional[str] = None) -> Dict[str, Any]:
    role = role.lower()
    if role not in {"user", "admin"}:
        role = "user"
    session = {"user_id": user_id, "name": name, "role": role, "email": email}
    _write_file(SESSION_FILE, session)
    return session


def logout() -> bool:
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
            return True
        except Exception:
            return False
    return False


