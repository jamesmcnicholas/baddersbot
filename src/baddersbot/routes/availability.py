from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from ..services.repository import (
    get_player,
    get_player_availability,
    list_availability_snapshots,
    list_players,
    set_player_availability,
)
from .navigation import build_nav_context

router = APIRouter(prefix="/admin", tags=["admin"])

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@dataclass
class PlayerOption:
    id: str
    name: str
    grade: str

    @property
    def label(self) -> str:
        return f"{self.name} (Grade {self.grade})"


@router.get("/availability", response_class=HTMLResponse)
async def availability_planner(request: Request) -> HTMLResponse:
    players = _load_player_options()
    context = {
        "request": request,
        "players": players,
        "submissions": list_availability_snapshots(),
        "flash": None,
    }
    context.update(build_nav_context("availability"))
    return templates.TemplateResponse("availability_planner.html", context)


@router.post("/availability", response_class=HTMLResponse)
async def submit_availability(
    request: Request,
    player_id: str = Form(...),
    available_dates: str = Form(default=""),
) -> HTMLResponse:
    player_records = {option.id: option for option in _load_player_options()}
    player = player_records.get(player_id)
    if not player:
        return await availability_planner(request)

    dates = _parse_dates(available_dates)
    set_player_availability(player.id, dates)

    saved_dates = get_player_availability(player.id)

    context = {
        "request": request,
        "players": list(player_records.values()),
        "submissions": list_availability_snapshots(),
        "flash": {
            "message": f"Saved availability for {player.name} ({len(saved_dates)} dates).",
            "severity": "success",
        },
        "recent_selection": {
            "player_id": player.id,
            "dates": [day.isoformat() for day in saved_dates],
        },
    }
    context.update(build_nav_context("availability"))
    return templates.TemplateResponse("availability_planner.html", context)


@router.get("/availability/{player_id}/slots", response_class=JSONResponse)
async def availability_slots(player_id: str) -> JSONResponse:
    player = get_player(player_id)
    if player is None:
        return JSONResponse({"player_id": player_id, "dates": []}, status_code=404)
    dates = get_player_availability(player_id)
    return JSONResponse({"player_id": player_id, "dates": [day.isoformat() for day in dates]})


def _load_player_options() -> list[PlayerOption]:
    options: list[PlayerOption] = []
    for record in list_players():
        options.append(
            PlayerOption(
                id=record.id,
                name=record.name,
                grade=record.grade,
            )
        )
    return sorted(options, key=lambda option: option.name)


def _parse_dates(raw: str) -> list[date]:
    dates: list[date] = []
    for value in [item.strip() for item in raw.split(",") if item.strip()]:
        try:
            dates.append(date.fromisoformat(value))
        except ValueError:
            continue
    return sorted(set(dates))
