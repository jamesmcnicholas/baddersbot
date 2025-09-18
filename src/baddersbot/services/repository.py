from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from sqlmodel import delete, select

from .db import AvailabilityModel, PlayerModel, get_session


@dataclass
class PlayerRecord:
    id: str
    name: str
    grade: str
    availability_note: str | None
    payment_status: str | None


@dataclass
class AvailabilitySnapshot:
    player_id: str
    player_name: str
    dates: list[date]


def list_players() -> list[PlayerRecord]:
    with get_session() as session:
        players = session.exec(select(PlayerModel).order_by(PlayerModel.name)).all()
        return [
            PlayerRecord(
                id=player.id,
                name=player.name,
                grade=player.grade,
                availability_note=player.availability_note,
                payment_status=player.payment_status,
            )
            for player in players
        ]


def get_player(player_id: str) -> PlayerRecord | None:
    with get_session() as session:
        player = session.get(PlayerModel, player_id)
        if player is None:
            return None
        return PlayerRecord(
            id=player.id,
            name=player.name,
            grade=player.grade,
            availability_note=player.availability_note,
            payment_status=player.payment_status,
        )


def get_player_availability(player_id: str) -> list[date]:
    with get_session() as session:
        rows = session.exec(
            select(AvailabilityModel.available_date).where(AvailabilityModel.player_id == player_id)
        ).all()
    return sorted({date.fromisoformat(value) for value in rows})


def set_player_availability(player_id: str, dates: Iterable[date]) -> None:
    iso_dates = sorted({day.isoformat() for day in dates})
    with get_session() as session:
        session.exec(delete(AvailabilityModel).where(AvailabilityModel.player_id == player_id))
        session.commit()
        if not iso_dates:
            return
        session.add_all(
            [AvailabilityModel(player_id=player_id, available_date=iso) for iso in iso_dates]
        )
        session.commit()


def list_availability_snapshots() -> list[AvailabilitySnapshot]:
    snapshots: list[AvailabilitySnapshot] = []
    players = list_players()
    for player in players:
        dates = get_player_availability(player.id)
        if not dates:
            continue
        snapshots.append(
            AvailabilitySnapshot(
                player_id=player.id,
                player_name=player.name,
                dates=dates,
            )
        )
    return snapshots
