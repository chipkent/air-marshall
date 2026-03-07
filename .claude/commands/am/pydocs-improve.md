---
description: Improve docstring quality and completeness
argument-hint: [file-or-directory ...]
disable-model-invocation: true
allowed-tools: Read, Edit, Grep, Glob
---

# Improve Python Docstrings

Improve the docstrings in $ARGUMENTS for quality and completeness. If no file is specified, ask which file(s) to improve.

1. Ensure every public function, class, and method has a docstring. Note: Per project ruff config, `__init__` method docstrings (D107), module-level docstrings (D100), `__init__.py` package docstrings (D104), and test functions in `tests/**` (D103) are not required — skip these.
2. Descriptions should clearly explain *what* the code does and *why*, not just restate the signature.
3. Include Args, Returns, and Raises sections where applicable (Google style, per project convention).
4. Do not remove TODOs.
5. Do not change any logic or behavior — only docstrings.
