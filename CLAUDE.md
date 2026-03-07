# air-marshall

IoT system for monitoring and controlling a home HVAC setup.
Two Raspberry Pi devices: one controller, one monitor.
Flutter mobile app for the UI.

## Architecture

- `src/air_marshall/hvac_controller/` — HVAC control logic (runs on controller RPi)
- `src/air_marshall/monitor/` — Environmental monitoring (runs on monitor RPi)
- `src/air_marshall/shared/` — Shared utilities
- `app/` — Flutter mobile app
- `tests/` — Python unit and integration tests

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — Python package manager
- Node.js 20+ — for markdownlint
- [Flutter SDK](https://docs.flutter.dev/get-started/install) — for `app/`

## Setup

```sh
uv sync --extra dev
pre-commit install --hook-type commit-msg --hook-type pre-commit
```

## Run code quality checks (with auto-fix)

```sh
./bin/check.sh
```

## Individual checks

```sh
uv run ruff format src tests          # format Python
uv run ruff check --fix src tests     # lint Python
uv run mypy src                       # type-check Python
npx --yes markdownlint-cli2 --fix     # lint Markdown
dart format app/lib app/test          # format Dart
cd app && flutter analyze             # lint Dart/Flutter
```

## Running tests

```sh
uv run pytest                                                      # unit tests (integration excluded)
uv run pytest -m integration -v --no-cov --log-cli-level=INFO     # integration tests
cd app && flutter test                                             # Dart/Flutter unit tests
```

## Commit conventions

All commits and PR titles must follow [Conventional Commits](https://www.conventionalcommits.org/).
The commitizen pre-commit hook enforces this on `commit-msg`.

## Coding conventions

- Use f-strings; avoid `%`-style string formatting.
- Avoid `Any` type hints without explicit justification.
- Avoid `hasattr()` and `getattr()` without justification — they can mask bugs.
- Do not access private members (underscore-prefixed) across package boundaries. Test files may access the code they test.
- When moving or removing files, use `git mv` / `git rm` to preserve history.
- Use American English spelling throughout code, comments, docstrings, and docs.
- Write Python docstrings in Google style.
- One source file maps to one test file (`<file>.py` → `test_<file>.py`). Integration tests use `test_<file>_integration.py`.
- Follow the [Dart style guide](https://dart.dev/effective-dart) for Dart/Flutter code in `app/`.
- Run `flutter analyze` to check for lint errors in `app/`.

## Testing

- Always run tests via `uv run pytest`, never bare `pytest`.
- Target 100% unit test coverage for all source files.
- Flutter/Dart tests are run via `cd app && flutter test`.

## Documentation standards

- JSON examples in docs must use ASCII-only characters (no smart quotes, curly apostrophes, etc.).
- Code blocks containing comments must use ` ```json5 ` not ` ```json `.
- All ` ```json ` blocks must be valid and parseable.
- Code samples should be copy-paste ready; use obvious placeholders like `"your-password-here"`.
