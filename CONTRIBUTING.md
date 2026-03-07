# Contributing

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — Python package manager
- Node.js 20+ — required for markdownlint
- [Flutter SDK](https://docs.flutter.dev/get-started/install) — for `app/`

## Setup

```bash
# Install Python dependencies (including dev/lint/test extras)
uv sync --extra dev

# Install pre-commit hooks
pre-commit install --hook-type commit-msg --hook-type pre-commit
```

## Run all checks

```bash
./bin/check.sh
```

This runs ruff format + fix, mypy, markdownlint, dart format, and flutter analyze — with auto-fix where applicable.

## Run tests

```bash
# Unit tests only (default — integration tests excluded)
uv run pytest

# Integration tests (requires live hardware or external services)
uv run pytest -m integration -v --no-cov --log-cli-level=INFO
```

## Flutter

```bash
cd app
flutter test
```

## Commit conventions

All commits and PR titles must follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
The `commitizen` pre-commit hook enforces this on `commit-msg`.
