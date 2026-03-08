#!/usr/bin/env bash
# Run all unit tests with coverage.
# Usage: ./bin/test.sh
# Requires: uv, Flutter SDK, lcov
set -uo pipefail

python_exit=0
flutter_exit=0

echo "==> Python tests"
uv run pytest || python_exit=$?

echo "==> Flutter tests"
cd app
flutter test --coverage || flutter_exit=$?
lcov --summary coverage/lcov.info

if [ $python_exit -ne 0 ] || [ $flutter_exit -ne 0 ]; then
    echo "Tests failed (Python: $python_exit, Flutter: $flutter_exit)"
    exit 1
fi

echo "All tests passed."
