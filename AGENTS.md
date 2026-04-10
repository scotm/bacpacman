# Agent Guidelines

## Project

`bacpacman` is a Python CLI for exporting Azure SQL databases to `.bacpac` files and importing them into local SQL Server. It uses Click and the Azure SDK for Python (`azure-identity`, `azure-mgmt-resource`, `azure-mgmt-sql`). Full user workflows may require the Azure CLI (`az`) and `sqlpackage`; the tool checks for these and surfaces setup hints.

- **Python**: `>=3.10.9` (see `pyproject.toml`).
- **Layout**: Application code under `bacpacman/` — `main.py` (entry), `cli.py` (Click commands), `azure_handler.py`, `sql_handler.py`, `config.py`, `ui.py`.

## Setup

```bash
uv pip install -e .[dev]
```

Use `pip install -e .[dev]` if you are not using `uv`. Optional runtime extras from the README (e.g. `keyring`, `questionary`) are pulled in via `[dev]` where listed.

## Build / Lint / Typecheck

- `ruff check .` — lint (rules in `[tool.ruff]` / `[tool.ruff.lint]` in `pyproject.toml`)
- `black .` — format (88 character line length)
- `mypy bacpacman/` — type checking
- `pyright` — additional type checking

## Run the CLI

- `python -m bacpacman.main` — from a checkout without installing the script
- `bacpacman` — console script after editable install (`[project.scripts]` in `pyproject.toml`)

## Tests

There is no pytest (or other) test suite committed yet; `.gitignore` includes `.pytest_cache/`. When adding automated tests, prefer `pytest` and a `tests/` tree, and document the command here.

## Code Style

- **Imports**: Standard library first, third-party second, local (`bacpacman`) last.
- **Types**: Use type hints; keep changes consistent with mypy/pyright.
- **Naming**: `snake_case` for functions and variables; `PascalCase` for classes.
- **Error handling**: Use `try`/`except` with specific Azure SDK or standard-library exceptions; avoid bare `except:`.
- **Formatting**: Black (88 columns) and Ruff as in `pyproject.toml`.
- **Structure**: Click commands stay in `cli.py`; put Azure and SQL logic in dedicated modules, not in the CLI layer.
