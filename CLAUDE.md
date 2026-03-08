# air-marshall

IoT system for monitoring and controlling a home HVAC setup.
Two Raspberry Pi devices: one controller, one monitor.
Flutter mobile app for the UI.

## Architecture

- `src/air_marshall/hvac_controller/` — HVAC control logic (runs on controller RPi)
- `src/air_marshall/monitor/` — Environmental monitoring (runs on monitor RPi)
- `src/air_marshall/api/` — HTTP API models and client (used by both RPi services)
- `src/air_marshall/database/` — FastAPI/SQLite HTTP service
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
./bin/test.sh              # all unit tests (Python + Flutter)
./bin/test-integration.sh  # all integration tests — starts a live DB server
```

Individual commands:

```sh
uv run pytest                                                      # Python unit tests only
uv run pytest -m integration -v --no-cov --log-cli-level=INFO     # Python integration tests only
cd app && flutter test --exclude-tags integration                  # Flutter unit tests only
cd app && flutter test --tags integration                          # Flutter integration tests only
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
- Write Python docstrings in Google style. Module-level constants and Pydantic model fields use an inline docstring (triple-quoted string immediately after the assignment), not a `#` comment.
- Keep docstrings in sync with the code. When you rename, restructure, or move code, update all affected docstrings in the same change. Stale docstrings are bugs.
- Docstrings must add information beyond what the name and type signature already convey. Do not restate the obvious.
- Do not put operational information (how to run, env vars, deployment) in docstrings. That belongs in external docs. Do not cross-reference external files from docstrings — file paths change and the reference will drift.
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
