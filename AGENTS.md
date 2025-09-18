# Repository Guidelines

## Project Structure & Module Organization
- Keep high-level specs in the repository root; the authoritative scope lives in `requirements.md`.
- Add production code under `src/`, grouping modules by domain (`players`, `sessions`, `allocation`, `reporting`). Example: `src/allocation/engine.py`.
- Place experiments and throwaway prototypes in `spikes/` with a README explaining intent and lifespan.
- Mirror the module layout in `tests/` (e.g., `tests/allocation/test_engine.py`) so the mapping from code to coverage stays obvious.

## Build, Test, and Development Commands
- Create a virtual environment (`python -m venv .venv && source .venv/bin/activate`) before installing dependencies.
- Install local requirements with `pip install -r requirements.txt`; regenerate the file via `pip freeze > requirements.txt` when dependencies change.
- Run the service in watch mode using `uvicorn baddersbot.app:app --reload`; reserve this command name when scaffolding the API entrypoint.
- Execute the automated test suite with `pytest`; add `pytest -k allocation` for targeted runs during investigations.

## Coding Style & Naming Conventions
- Target Python 3.11, using `ruff` and `black` for linting/formatting (`black src tests` and `ruff check src tests`).
- Prefer type hints everywhere; fail CI if `mypy` reports errors.
- Name modules with lowercase underscores (`allocation_rules.py`), classes in PascalCase, and functions in snake_case.
- Keep functions under 40 lines; refactor shared logic into `services/` or `domain/` subpackages when it grows.

## Testing Guidelines
- Use `pytest` with descriptive test names (`test_allocation_respects_grade_constraints`).
- Cover both auto-allocation paths and manual override flows; include regression tests for previously reported issues.
- Require >90% branch coverage for allocation modules; track with `pytest --cov=src/allocation --cov-report=term-missing`.

## Commit & Pull Request Guidelines
- Write commits in the imperative mood (`Add allocation fairness guard`); keep scopes under ~150 lines to ease review.
- Reference GitHub issues in commit bodies (`Refs #12`) and list manual test evidence when applicable.
- Pull requests must summarize business impact, outline validation steps, and include screenshots for UI-facing changes.

## Security & Configuration Tips
- Store secrets in `.env` (never commit); load them via `pydantic` settings or `python-dotenv`.
- Rotate API keys quarterly and document credentials in the internal vault, linking from the PR description when updates occur.
- Add new environment variables to `.env.example` with safe defaults so other agents can bootstrap quickly.
