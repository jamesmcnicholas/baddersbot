from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class NavLink:
    key: str
    label: str
    href: str


_NAV_LINKS: tuple[NavLink, ...] = (
    NavLink(key="dashboard", label="Dashboard", href="/admin/dashboard"),
    NavLink(key="users", label="Users", href="/admin/users"),
    NavLink(key="availability", label="Availability", href="/admin/availability"),
    NavLink(key="allocation", label="Allocation", href="/admin/allocation"),
    NavLink(key="messages", label="Messages", href="/admin/allocation/messages"),
)


def build_nav_context(active_key: str) -> dict[str, object]:
    """Return template context entries for the global admin navigation bar."""
    return {
        "nav_links": tuple(_adapt_links(_NAV_LINKS, active_key)),
    }


def _adapt_links(links: Iterable[NavLink], active_key: str) -> Iterable[dict[str, object]]:
    for link in links:
        yield {
            "key": link.key,
            "label": link.label,
            "href": link.href,
            "is_active": link.key == active_key,
        }
