#!/usr/bin/env bash
# Run hardware tests on the monitor Raspberry Pi.
# Must be run on the device with SHT45 Trinkey and Automation HAT attached.
# Usage: ./bin/test-hardware.sh
set -uo pipefail

uv run pytest -m hardware -v --no-cov --log-cli-level=INFO
