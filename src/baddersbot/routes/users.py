from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .navigation import build_nav_context
from ..services.data_store import iter_collection

router = APIRouter(prefix="/admin", tags=["admin"])

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@dataclass
class PlayerRecord:
    id: str
    name: str
    grade: str
    availability_note: str
    payment_status: str

    def matches_query(self, query: str) -> bool:
        haystack = " ".join([self.name, self.grade, self.payment_status, self.availability_note]).lower()
        return query.lower() in haystack


@router.get("/users", response_class=HTMLResponse)
async def manage_users(request: Request, q: str | None = Query(default=None, alias="search")) -> HTMLResponse:
    records = _load_players()
    filtered = _filter_records(records, q)

    context = {
        "request": request,
        "records": filtered,
        "total_count": len(records),
        "visible_count": len(filtered),
        "search_query": q or "",
    }
    context.update(build_nav_context("users"))
    return templates.TemplateResponse("user_management.html", context)


def _filter_records(records: Iterable[PlayerRecord], query: str | None) -> list[PlayerRecord]:
    records = list(records)
    if not query:
        return records
    return [record for record in records if record.matches_query(query)]


def _load_players() -> list[PlayerRecord]:
    records: list[PlayerRecord] = []
    for entry in iter_collection("player_directory"):
        records.append(
            PlayerRecord(
                id=str(entry.get("id", "")),
                name=str(entry.get("name", "")),
                grade=str(entry.get("grade", "")),
                availability_note=str(entry.get("availability_note", "")),
                payment_status=str(entry.get("payment_status", "Unknown")),
            )
        )
    return records
