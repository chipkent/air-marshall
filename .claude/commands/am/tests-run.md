---
description: Run all Python and Flutter unit tests
disable-model-invocation: true
allowed-tools: Bash
---

# Run Tests

Run Python unit tests:

```sh
uv run pytest
```

Run Flutter/Dart unit tests:

```sh
cd app && flutter test
```

Report the results. If tests fail, summarize what failed and why.
