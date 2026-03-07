#!/usr/bin/env bash
# Run all code quality checks with auto-fix where possible.
# Usage: ./bin/check.sh
# Requires: uv, Node.js (for markdownlint), Flutter SDK
set -euo pipefail

echo "==> ruff format (auto-fix)"
uv run ruff format src tests

echo "==> ruff check (auto-fix)"
uv run ruff check --fix src tests

echo "==> mypy"
uv run mypy src

echo "==> markdownlint (auto-fix)"
npx --yes markdownlint-cli2 --fix

echo "==> dart format (auto-fix)"
dart format app/lib app/test

echo "==> flutter analyze"
cd app && flutter analyze

echo "All checks passed."
