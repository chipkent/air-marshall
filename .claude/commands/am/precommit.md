---
description: Run code quality checks, then all unit tests
disable-model-invocation: true
allowed-tools: Bash
---

# Pre-commit Checks

Run code quality checks (format, lint, type-check, markdownlint, dart format, flutter analyze):

```sh
./bin/check.sh
```

Then run all unit tests:

```sh
./bin/test.sh
```

Report any failures. The check script auto-fixes formatting and lint issues where possible. If anything still fails after the script, summarize what failed and why — do not attempt to write fixes autonomously.
