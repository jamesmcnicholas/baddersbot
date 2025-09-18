from __future__ import annotations

import argparse
from pathlib import Path

from fastapi.testclient import TestClient

from baddersbot.app import app

PAGES: dict[str, str] = {
    "/admin/dashboard": "admin/dashboard/index.html",
    "/admin/availability": "admin/availability/index.html",
    "/admin/allocation": "admin/allocation/index.html",
    "/admin/users": "admin/users/index.html",
    "/admin/allocation/messages": "admin/allocation/messages/index.html",
}


def build_site(output_dir: Path) -> None:
    client = TestClient(app)
    output_dir.mkdir(parents=True, exist_ok=True)

    for path, relative in PAGES.items():
        response = client.get(path)
        response.raise_for_status()
        destination = output_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(response.text, encoding="utf-8")
        print(f"[build] {path} -> {relative}")

    # Provide a friendly landing page that links to the rendered views.
    index_html = """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <title>Baddersbot Admin Prototype</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 3rem; color: #1f2430; }
          h1 { margin-bottom: 1.5rem; }
          ul { list-style: none; padding: 0; }
          li { margin-bottom: 0.75rem; }
          a { color: #1e88e5; text-decoration: none; font-weight: 600; }
          a:hover { text-decoration: underline; }
        </style>
      </head>
      <body>
        <h1>Baddersbot Admin Prototype</h1>
        <p>Select a view to explore the static snapshot built from FastAPI templates.</p>
        <ul>
          <li><a href="admin/dashboard/index.html">Dashboard</a></li>
          <li><a href="admin/availability/index.html">Availability Planner</a></li>
          <li><a href="admin/allocation/index.html">Allocation Console</a></li>
          <li><a href="admin/users/index.html">Player Directory</a></li>
          <li><a href="admin/allocation/messages/index.html">Allocation Messages</a></li>
        </ul>
      </body>
    </html>
    """
    (output_dir / "index.html").write_text(index_html.strip(), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build static HTML snapshots of the admin app.")
    parser.add_argument("--output", type=Path, default=Path("dist"), help="Output directory for static files")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_site(args.output)


if __name__ == "__main__":
    main()
