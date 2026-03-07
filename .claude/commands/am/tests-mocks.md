---
description: Verify and fix MagicMock/AsyncMock usage in test files
argument-hint: [test-file ...]
disable-model-invocation: true
allowed-tools: Read, Edit, Bash, Grep, Glob
---

# Test Mocks Review

Review the test file(s) in $ARGUMENTS and ensure mocks are applied correctly. If no file is specified, ask which test file(s) to review.

1. Async functions must be mocked with `AsyncMock`, not `MagicMock`.
2. Sync functions must use `MagicMock` (or `patch`).
3. Confirm mock targets are patched at the right import location (where the name is used, not where it's defined). For example, if `air_marshall.monitor.foo` imports `requests`, patch `air_marshall.monitor.foo.requests`, not `requests` directly.
4. Flag any mock that could silently pass due to incorrect type.
5. After fixing all issues, run the test file to confirm all tests pass: `uv run pytest <test-file> -v`

Report all issues found and fix them.
