---
description: Correct inaccurate docstrings to match the actual implementation
argument-hint: [file-or-directory ...]
disable-model-invocation: true
allowed-tools: Read, Edit, Grep, Glob
---

# Python Docstring Accuracy Check

Check that the docstrings in $ARGUMENTS are factually accurate and reflect the actual implementation. If no file is specified, ask which file(s) to review.

- Read the source code carefully, then read each docstring.
- Correct any description, parameter, or return value that does not match what the code actually does.
- If a function or method has no docstring, skip it — use `/am:pydocs-improve` to add missing docstrings.
- Do not remove TODOs.
- Do not change any logic or behavior — only docstrings.
