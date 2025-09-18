from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..services.data_store import get_document, iter_collection
from .navigation import build_nav_context

router = APIRouter(prefix="/admin", tags=["admin"])

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@dataclass
class PlayerSummary:
    name: str
    grade: str
    sessions_allocated: int
    payment_status: str
    notes: str = ""


@dataclass
class SessionSummary:
    date: date
    label: str
    grade: str
    venue: str
    capacity: int
    allocated: int

    @property
    def remaining_slots(self) -> int:
        return max(self.capacity - self.allocated, 0)

    @property
    def fill_percentage(self) -> int:
        if not self.capacity:
            return 0
        return int((self.allocated / self.capacity) * 100)


@dataclass
class AllocationAlert:
    category: str
    message: str


@dataclass
class WeeklyBlockEntry:
    section: str
    note: str | None = None
    allocation_anchor: str | None = None


@dataclass
class WeeklyBlock:
    weekday: str
    time_label: str
    entries: dict[str, list[WeeklyBlockEntry]]


WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request) -> HTMLResponse:
    """Render the administrator dashboard with placeholder information."""
    context = build_dashboard_context()
    context.update({"request": request})
    context.update(build_nav_context("dashboard"))
    return templates.TemplateResponse("admin_dashboard.html", context)


def build_dashboard_context() -> dict[str, object]:
    players = _load_player_summaries()
    sessions = _load_session_summaries()
    alerts = _build_alerts(players, sessions)

    metrics = {
        "total_players": len(players),
        "sessions_this_month": len(sessions),
        "pending_payments": sum(1 for player in players if player.payment_status != "Paid"),
        "unfilled_sessions": sum(1 for session in sessions if session.remaining_slots > 0),
    }

    upcoming_sessions = _select_upcoming_sessions(sessions)
    week_window_label = _format_week_window()

    weekly_schedule = _load_weekly_schedule()
    weekly_colors = _section_color_map()
    weekly_default_color = {"bg": "#e5e7eb", "fg": "#1f2937"}

    weekly_blocks = weekly_schedule["blocks"]
    weekly_day_blocks = _group_blocks_by_weekday(weekly_blocks)

    return {
        "metrics": metrics,
        "sessions": sessions,
        "alerts": alerts,
        "upcoming_sessions": upcoming_sessions,
        "week_window_label": week_window_label,
        "weekly_blocks": weekly_blocks,
        "weekly_day_blocks": weekly_day_blocks,
        "weekly_venues": weekly_schedule["venues"],
        "weekly_colors": weekly_colors,
        "weekly_color_default": weekly_default_color,
    }


def _select_upcoming_sessions(sessions: Iterable[SessionSummary], window_days: int = 7) -> list[SessionSummary]:
    today = date.today()
    window_end = today + timedelta(days=window_days)
    sessions = sorted(sessions, key=lambda session: session.date)

    upcoming = [session for session in sessions if today <= session.date <= window_end]
    if not upcoming:
        upcoming = sessions[: min(len(sessions), 6)]

    return upcoming


def _format_week_window(window_days: int = 7) -> str:
    today = date.today()
    end = today + timedelta(days=window_days - 1)
    return f"{today.strftime('%d %b')} – {end.strftime('%d %b')}"


def _section_color_map() -> dict[str, dict[str, str]]:
    palette = {
        "A Section": {"bg": "#dcb6ff", "fg": "#43186b"},
        "B1 Section": {"bg": "#ffe08a", "fg": "#5b4300"},
        "B2 Section": {"bg": "#cde5ff", "fg": "#123d73"},
        "B3 Section": {"bg": "#bde8c3", "fg": "#0e5133"},
        "B Sections": {"bg": "#8ad0a4", "fg": "#053822"},
        "Coaching": {"bg": "#a7d4ff", "fg": "#0b3c63"},
        "Singles": {"bg": "#ffcc80", "fg": "#6b3a00"},
        "Match Practice": {"bg": "#ffd4e6", "fg": "#742144"},
    }
    return palette


def _load_weekly_schedule() -> dict[str, object]:
    schedule = get_document("weekly_schedule")
    venues = [str(venue) for venue in schedule.get("venues", [])]

    blocks: list[WeeklyBlock] = []
    for raw_block in schedule.get("blocks", []):
        weekday = str(raw_block.get("weekday", ""))
        time_label = str(raw_block.get("time_label", ""))
        raw_entries = raw_block.get("entries", {})
        entries: dict[str, list[WeeklyBlockEntry]] = {}
        for venue, items in raw_entries.items():
            venue_key = str(venue)
            entry_list: list[WeeklyBlockEntry] = []
            for item in items or []:
                entry_list.append(
                    WeeklyBlockEntry(
                        section=str(item.get("section", "")),
                        note=item.get("note"),
                    )
                )
            entries[venue_key] = entry_list
        blocks.append(WeeklyBlock(weekday=weekday, time_label=time_label, entries=entries))

    blocks.sort(key=lambda block: (WEEKDAY_ORDER.index(block.weekday), block.time_label))
    _assign_allocation_anchors(blocks)
    return {"venues": venues, "blocks": blocks}


def _assign_allocation_anchors(blocks: Iterable[WeeklyBlock]) -> None:
    for block in blocks:
        for entries in block.entries.values():
            for entry in entries:
                entry.allocation_anchor = _section_anchor(entry.section)


def _section_anchor(section: str) -> str | None:
    mapping = {
        "A Section": "grade-a",
        "Coaching": "grade-a",
        "B Sections": "grade-b",
        "B1 Section": "grade-b",
        "B2 Section": "grade-b",
        "B3 Section": "grade-b",
        "Singles": "grade-b",
        "Match Practice": "grade-b",
    }
    return mapping.get(section)


def _group_blocks_by_weekday(blocks: Iterable[WeeklyBlock]) -> list[dict[str, object]]:
    ordered: dict[str, list[WeeklyBlock]] = {weekday: [] for weekday in WEEKDAY_ORDER}
    for block in blocks:
        ordered.setdefault(block.weekday, []).append(block)

    grouped: list[dict[str, object]] = []
    for weekday in WEEKDAY_ORDER:
        day_blocks = ordered.get(weekday)
        if not day_blocks:
            continue
        grouped.append({"weekday": weekday, "blocks": day_blocks})
    return grouped


def _load_player_summaries() -> list[PlayerSummary]:
    summaries: list[PlayerSummary] = []
    for entry in iter_collection("player_summaries"):
        summaries.append(
            PlayerSummary(
                name=str(entry.get("name", "")),
                grade=str(entry.get("grade", "")),
                sessions_allocated=int(entry.get("sessions_allocated", 0)),
                payment_status=str(entry.get("payment_status", "Unknown")),
                notes=str(entry.get("notes", "")),
            )
        )
    return summaries


def _load_session_summaries() -> list[SessionSummary]:
    sessions: list[SessionSummary] = []
    for entry in iter_collection("session_summaries"):
        sessions.append(
            SessionSummary(
                date=_parse_date(entry.get("date")),
                label=str(entry.get("label", "")),
                grade=str(entry.get("grade", "")),
                venue=str(entry.get("venue", "")),
                capacity=int(entry.get("capacity", 0)),
                allocated=int(entry.get("allocated", 0)),
            )
        )
    return sessions


def _build_alerts(players: Iterable[PlayerSummary], sessions: Iterable[SessionSummary]) -> list[AllocationAlert]:
    alerts: list[AllocationAlert] = []

    overdue_players = [player.name for player in players if player.payment_status == "Overdue"]
    if overdue_players:
        alerts.append(
            AllocationAlert(
                category="Payments",
                message=f"Overdue payments: {', '.join(overdue_players)}",
            )
        )

    unfilled = [session for session in sessions if session.remaining_slots > 0]
    if unfilled:
        session_labels = ", ".join(f"{session.label} ({session.remaining_slots} open)" for session in unfilled)
        alerts.append(
            AllocationAlert(
                category="Capacity",
                message=f"Open slots in {session_labels}",
            )
        )

    return alerts


def _parse_date(value: str | None) -> date:
    if not value:
        return date.today()
    return date.fromisoformat(value)
