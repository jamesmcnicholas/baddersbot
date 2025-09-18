from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

_FIXTURE_FILE = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "mock_data.json"


class JsonDataStore:
    """Simple JSON-backed data source to feed the early UI screens."""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path
        self._cache: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        if self._cache is None:
            with self._fixture_path.open("r", encoding="utf-8") as handle:
                self._cache = json.load(handle)
        return self._cache

    def collection(self, key: str) -> list[dict[str, Any]]:
        payload = self._load()
        items = payload.get(key)
        if items is None:
            return []
        if not isinstance(items, list):
            raise TypeError(f"Fixture key '{key}' is not a list")
        return items

    def document(self, key: str) -> dict[str, Any]:
        payload = self._load()
        item = payload.get(key, {})
        if not isinstance(item, dict):
            raise TypeError(f"Fixture key '{key}' is not a dict")
        return item


@lru_cache(maxsize=1)
def get_data_store() -> JsonDataStore:
    return JsonDataStore(_FIXTURE_FILE)


def iter_collection(key: str) -> Iterable[dict[str, Any]]:
    yield from get_data_store().collection(key)


def get_document(key: str) -> dict[str, Any]:
    return get_data_store().document(key)
