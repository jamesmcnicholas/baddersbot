from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..services.data_store import iter_collection
from .navigation import build_nav_context

router = APIRouter(prefix="/admin", tags=["admin"])

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@dataclass
class PlayerAllocation:
    name: str
    grade: str
    preference_match: bool
    payment_status: str
    notes: str = ""


@dataclass
class SessionAllocation:
    id: str
    date: date
    label: str
    grade: str
    capacity: int
    assigned: list[PlayerAllocation]
    waitlist: list[PlayerAllocation]
    confidence: str
    notes: str = ""

    @property
    def allocated(self) -> int:
        return len(self.assigned)

    @property
    def remaining(self) -> int:
        return max(self.capacity - self.allocated, 0)

    @property
    def fill_percentage(self) -> int:
        if not self.capacity:
            return 0
        return int((self.allocated / self.capacity) * 100)


@dataclass
class SessionGroupMessage:
    id: str
    label: str
    date: date
    grade: str
    confirmed: list[str]
    waitlist: list[str]
    notes: str
    message: str

    @property
    def has_waitlist(self) -> bool:
        return bool(self.waitlist)


@router.get("/allocation", response_class=HTMLResponse)
async def allocation_management(request: Request) -> HTMLResponse:
    """Render the allocation management workspace."""
    sessions = _load_session_allocations()

    context = {
        "request": request,
        "sessions": sessions,
        "summary": _build_summary(sessions),
    }
    context.update(build_nav_context("allocation"))
    return templates.TemplateResponse("allocation_management.html", context)


@router.get("/allocation/messages", response_class=HTMLResponse)
async def allocation_messages(request: Request) -> HTMLResponse:
    """Render WhatsApp-ready messages for each session."""
    sessions = _load_session_allocations()
    messages = _build_session_messages(sessions)

    context = {
        "request": request,
        "messages": messages,
        "session_count": len(messages),
    }
    context.update(build_nav_context("messages"))
    return templates.TemplateResponse("allocation_messages.html", context)


def _build_summary(sessions: Iterable[SessionAllocation]) -> dict[str, int]:
    sessions = list(sessions)
    return {
        "total_sessions": len(sessions),
        "fully_booked": sum(1 for session in sessions if session.remaining == 0),
        "open_slots": sum(session.remaining for session in sessions),
        "waitlisted_players": sum(len(session.waitlist) for session in sessions),
    }


def _build_session_messages(sessions: Iterable[SessionAllocation]) -> list[SessionGroupMessage]:
    messages: list[SessionGroupMessage] = []
    for session in sessions:
        confirmed_names = [player.name for player in session.assigned]
        waitlist_names = [player.name for player in session.waitlist]
        composed = _compose_session_message(session, confirmed_names, waitlist_names)
        messages.append(
            SessionGroupMessage(
                id=session.id,
                label=session.label,
                date=session.date,
                grade=session.grade,
                confirmed=confirmed_names,
                waitlist=waitlist_names,
                notes=session.notes,
                message=composed,
            )
        )
    messages.sort(key=lambda message: message.date)
    return messages


def _compose_session_message(
    session: SessionAllocation,
    confirmed: Iterable[str],
    waitlist: Iterable[str],
) -> str:
    confirmed = list(confirmed)
    waitlist = list(waitlist)

    weekday = session.date.strftime("%A")
    date_label = session.date.strftime("%d %b")
    time_part, location = _split_label(session.label)

    lines: list[str] = []
    location_fragment = f" at {location}" if location else ""
    lines.append(f"{weekday}'s players{location_fragment} ({date_label})")
    if time_part:
        lines.append("")
        lines.append(f"{time_part}:")

    if confirmed:
        lines.append(_join_names_line(confirmed))
    else:
        lines.append("No confirmed players listed yet.")

    if waitlist:
        lines.append("")
        lines.append(f"Waitlist: {_join_names(waitlist)}")

    if session.notes:
        lines.append("")
        lines.append(f"Notes: {session.notes}")

    lines.append("")
    lines.append("Any cancellations, let me know ASAP! 🏸😊")
    lines.append("The key will need collecting and returning – volunteer sooner rather than later!")

    return "\n".join(lines)


def _split_label(label: str) -> tuple[str, str | None]:
    parts = [part.strip() for part in label.split("-", maxsplit=1)]
    if len(parts) == 2:
        return parts[0], parts[1]
    return label, None


def _join_names_line(names: Iterable[str]) -> str:
    return _join_names(names)


def _join_names(names: Iterable[str]) -> str:
    names = [name.strip() for name in names if name.strip()]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + f", & {names[-1]}"


def _parse_date(value: str | None) -> date:
    if not value:
        return date.today()
    return date.fromisoformat(value)


def _load_session_allocations() -> list[SessionAllocation]:
    allocations: list[SessionAllocation] = []
    for entry in iter_collection("session_allocations"):
        assigned = [
            PlayerAllocation(
                name=str(item.get("name", "")),
                grade=str(item.get("grade", "")),
                preference_match=bool(item.get("preference_match", False)),
                payment_status=str(item.get("payment_status", "Unknown")),
                notes=str(item.get("notes", "")),
            )
            for item in entry.get("assigned", [])
        ]
        waitlist = [
            PlayerAllocation(
                name=str(item.get("name", "")),
                grade=str(item.get("grade", "")),
                preference_match=bool(item.get("preference_match", False)),
                payment_status=str(item.get("payment_status", "Unknown")),
                notes=str(item.get("notes", "")),
            )
            for item in entry.get("waitlist", [])
        ]

        allocations.append(
            SessionAllocation(
                id=str(entry.get("id", "")),
                date=_parse_date(entry.get("date")),
                label=str(entry.get("label", "")),
                grade=str(entry.get("grade", "")),
                capacity=int(entry.get("capacity", 0)),
                assigned=assigned,
                waitlist=waitlist,
                confidence=str(entry.get("confidence", "")),
                notes=str(entry.get("notes", "")),
            )
        )
    return allocations


def _mock_session_allocations() -> list[SessionAllocation]:
    return [
        SessionAllocation(
            id="session-2024-04-02-a",
            date=date(2024, 4, 2),
            label="Tue 6pm - Court 1",
            grade="A",
            capacity=8,
            assigned=[
                PlayerAllocation(name="Amelia Chan", grade="A", preference_match=True, payment_status="Paid"),
                PlayerAllocation(name="Charlotte Lin", grade="A", preference_match=True, payment_status="Pending"),
                PlayerAllocation(name="Oscar Ng", grade="A", preference_match=False, payment_status="Paid", notes="Prefers late"),
                PlayerAllocation(name="Yara Sato", grade="A", preference_match=True, payment_status="Paid"),
            ],
            waitlist=[
                PlayerAllocation(name="Nathan Fox", grade="A", preference_match=True, payment_status="Pending"),
            ],
            confidence="High",
            notes="Two slots reserved for coaching review.",
        ),
        SessionAllocation(
            id="session-2024-04-04-b",
            date=date(2024, 4, 4),
            label="Thu 7pm - Court 2",
            grade="B",
            capacity=10,
            assigned=[
                PlayerAllocation(name="Noah Patel", grade="B", preference_match=True, payment_status="Pending", notes="Prefers late"),
                PlayerAllocation(name="Lena Brooks", grade="B", preference_match=True, payment_status="Paid"),
                PlayerAllocation(name="Ivy Chen", grade="B", preference_match=True, payment_status="Paid"),
                PlayerAllocation(name="Zane Murray", grade="B", preference_match=False, payment_status="Overdue"),
            ],
            waitlist=[
                PlayerAllocation(name="Eva Müller", grade="B", preference_match=True, payment_status="Overdue"),
                PlayerAllocation(name="Theo Ruiz", grade="B", preference_match=False, payment_status="Paid"),
            ],
            confidence="Medium",
            notes="Pending manual swap to satisfy payment priority.",
        ),
        SessionAllocation(
            id="session-2024-04-06-c",
            date=date(2024, 4, 6),
            label="Sat 9am - Court 3",
            grade="C",
            capacity=12,
            assigned=[
                PlayerAllocation(name="Luis Romero", grade="C", preference_match=True, payment_status="Paid"),
                PlayerAllocation(name="Samira Idris", grade="C", preference_match=True, payment_status="Paid"),
                PlayerAllocation(name="Mia Zhang", grade="C", preference_match=True, payment_status="Paid"),
                PlayerAllocation(name="Leo Hernández", grade="C", preference_match=True, payment_status="Pending"),
                PlayerAllocation(name="Aria Kapoor", grade="C", preference_match=False, payment_status="Paid"),
                PlayerAllocation(name="Jon Park", grade="C", preference_match=True, payment_status="Paid"),
            ],
            waitlist=[],
            confidence="High",
            notes="",
        ),
    ]
