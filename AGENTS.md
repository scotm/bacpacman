# Agent Guidelines

## Build/Lint/Test Commands
- `ruff check .` - lint with ruff
- `black .` - format with black (88 char line length)
- `mypy bacpacman/` - type checking
- `pyright` - additional type checking
- `python -m bacpacman.main` - run CLI
- No test framework configured - add pytest for testing

## Code Style
- **Imports**: Standard library first, third-party second, local last
- **Types**: Use type hints (mypy/pyright strict)
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error Handling**: Use try/catch with specific Azure exceptions
- **Formatting**: Black with 88 char line length, ruff for linting
- **Structure**: Click CLI commands in cli.py, business logic in separate modules