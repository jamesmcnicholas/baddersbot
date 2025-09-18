from __future__ import annotations

from pathlib import Path
from typing import Iterable

from sqlmodel import Field, Session, SQLModel, create_engine, select

from .data_store import iter_collection

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DB_PATH = _DATA_DIR / "baddersbot.db"
_ENGINE = create_engine(f"sqlite:///{_DB_PATH}", connect_args={"check_same_thread": False})


class PlayerModel(SQLModel, table=True):
    __tablename__ = "players"

    id: str = Field(primary_key=True)
    name: str
    grade: str
    availability_note: str | None = None
    payment_status: str | None = None


class AvailabilityModel(SQLModel, table=True):
    __tablename__ = "availabilities"

    id: int | None = Field(default=None, primary_key=True)
    player_id: str = Field(foreign_key="players.id")
    available_date: str


def init_db() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(_ENGINE)
    _seed_players_if_needed()


def get_session() -> Session:
    return Session(_ENGINE)


def _seed_players_if_needed() -> None:
    with get_session() as session:
        existing = session.exec(select(PlayerModel).limit(1)).first()
        if existing:
            return

        players = list(iter_collection("player_directory"))
        if not players:
            return

        models = [
            PlayerModel(
                id=str(player.get("id", "")),
                name=str(player.get("name", "")),
                grade=str(player.get("grade", "")),
                availability_note=str(player.get("availability_note", "")),
                payment_status=str(player.get("payment_status", "")),
            )
            for player in players
        ]
        session.add_all(models)
        session.commit()


def upsert_players(records: Iterable[dict[str, str]]) -> None:
    """Utility helper for future sync tasks."""
    with get_session() as session:
        for record in records:
            player = session.get(PlayerModel, record["id"])
            if player is None:
                player = PlayerModel(**record)
                session.add(player)
            else:
                for key, value in record.items():
                    setattr(player, key, value)
        session.commit()
