# Contributing

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — Python package manager
- Node.js 20+ — required for markdownlint
- [Flutter SDK](https://docs.flutter.dev/get-started/install) — for `app/`

## Setup

```sh
# Install Python dependencies (including dev/lint/test extras)
uv sync --extra dev

# Install pre-commit hooks
pre-commit install --hook-type commit-msg --hook-type pre-commit
```

## Run all checks

```sh
./bin/check.sh
```

This runs ruff format + fix, mypy, markdownlint, dart format, and flutter analyze — with auto-fix where applicable.

## Run tests

```sh
./bin/test.sh              # all unit tests (Python + Flutter)
./bin/test-integration.sh  # all integration tests — starts a live DB server
```

To run a subset:

```sh
# Python unit tests only
uv run pytest

# Python integration tests only
uv run pytest -m integration -v --no-cov --log-cli-level=INFO

# Flutter unit tests only
cd app && flutter test --exclude-tags integration

# Flutter integration tests only (requires a running DB server)
cd app && flutter test --tags integration
```

## Commit conventions

All commits and PR titles must follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
The `commitizen` pre-commit hook enforces this on `commit-msg`.
