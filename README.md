Interactive Help Desk CLI
==========================

A simple, educational command-line interface (CLI) for managing help desk tickets using classic data structures (LinkedList, Stack, Queue, PriorityQueue).

Installation
------------

```
pip install interactive-helpdesk-cli
```

Download on PyPI: [interactive-helpdesk-cli 0.1.0](https://pypi.org/project/interactive-helpdesk-cli/0.1.0/)

Or from source:

```
python -m pip install --upgrade pip
python -m pip install .
```

Usage
-----

After installation, the `helpdesk` command will be available in your shell.

```
helpdesk --help
```

Example workflow:

```
helpdesk create --description "Parent ticket" --priority high
helpdesk create --description "Child ticket" --priority medium --parent 1
helpdesk analytics
helpdesk process
helpdesk close 1
helpdesk check 2
helpdesk close 2
helpdesk history
helpdesk undo
```

Roles, Sessions, and TUI
------------------------

Local session (no external auth required):

```
helpdesk login --user-id you --name "Your Name" --role user
helpdesk whoami
```

Create and manage tickets (owner is set from your session):

```
helpdesk create --description "Payment failing" --priority high
helpdesk assign 1 --to agent_alex
helpdesk tag 1 --add payments --add urgent
helpdesk my
```

Admin dashboard (login with role=admin):

```
helpdesk login --user-id admin01 --name "Admin" --role admin
helpdesk admin
```

Rich TUI (optional):

```
pip install "interactive-helpdesk-cli[ui]"
helpdesk tui
```

Development
-----------

- Run locally without installing:
  - `python helpdesk.py --help`
- Build a distribution:
  - `python -m pip install build twine`
  - `python -m build`
  - `twine check dist/*`
  - `twine upload dist/*` (requires PyPI credentials)

License
-------

MIT

---------

Todo: 
- Google Oauth Auth Register / Signin
- User Dashboard with Analytics
- Admin Dashboard with Analytics
- Ticket Raise Notification 