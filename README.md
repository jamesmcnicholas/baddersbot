# Baddersbot Admin Prototype

A FastAPI-based prototype that explores the organiser-facing workflows for the Badminton Club allocation tool. The goal is to let the admin review monthly allocations, tweak sessions, and communicate the confirmed plan without diving into spreadsheets.

## Project Layout

- `src/baddersbot/app.py` – FastAPI application factory and health endpoint.
- `src/baddersbot/routes/` – HTTP routes for the dashboard, availability planner, allocation workspace, and WhatsApp exports.
- `src/baddersbot/services/` – Shared data helpers (SQLite repository, JSON fixture loader).
- `src/baddersbot/templates/` – Jinja templates for the HTML experiences.
- `tests/` – Smoke tests that verify each page renders successfully (requires local dependency install).
- `requirements.md` – Product requirements and scope notes.
- `AGENTS.md` – Contributor guidelines for future agents.

## Stack

- Python 3.12+
- FastAPI & Starlette for HTTP routing
- SQLModel on SQLite for lightweight persistence (auto-seeded from fixtures)
- Jinja2 for server-rendered templates
- Uvicorn for development server

## Getting Started

1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Launch the development server (run from the project root):
   ```bash
   PYTHONPATH=src uvicorn baddersbot.app:app --reload
   ```
   > Note: The CLI environment used by this agent times out when starting long-lived servers. Please run the server locally on your machine.
3. On first launch the app creates `src/baddersbot/data/baddersbot.db` and seeds players from the JSON fixtures automatically.

## Key Screens

- `/admin/dashboard` – Cycle overview with KPIs, venue-aware weekly fill snapshot, and alerts.
- `/admin/availability` – Player availability planner with multi-select calendar backed by SQLite.
- `/admin/allocation` – Mock allocation workspace with session rosters, waitlists, and manual controls.
- `/admin/users` – Player directory with search, grade selectors, and payment status summary.
- `/admin/allocation/messages` – Generates session-level WhatsApp copy for broadcasting confirmed line-ups.

## Testing

Run smoke tests once dependencies are installed:
```bash
PYTHONPATH=src pytest
```
*(The automated agent cannot complete this command inside the harness due to runtime limits; please execute locally.)*

## Next Steps

- Expand persistence layer from SQLite prototype to Postgres (production target) and model allocations end-to-end.
- Implement authentication for the admin routes.
- Hook allocation actions (swap, waitlist, publish) into API endpoints and persistence.
- Consider a React front end with the Python backend as an API layer when the prototype hardens.
