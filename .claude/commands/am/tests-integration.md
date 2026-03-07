---
description: Run Python integration tests with verbose output and live logs
disable-model-invocation: true
allowed-tools: Bash
---

# Integration Tests

Run Python integration tests:

```sh
uv run pytest -m integration -v --no-cov --log-cli-level=INFO
```

Report the results. If tests fail, summarize what failed and why.
