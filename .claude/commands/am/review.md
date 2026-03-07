---
description: Thorough code review against project standards
argument-hint: [file-or-directory ...]
allowed-tools: Read, Bash, Grep, Glob
---

# Code Review

Perform a thorough code review of $ARGUMENTS. If no file is specified, ask which file(s) to review.

**General quality:**

1. Logic correctness, edge cases, error handling
2. Imports — flag unused; flag missing ones
3. TODOs — note any and whether they should be addressed now
4. Logging — consistent and appropriate; no debug noise left in

**Docstrings** (Python, `src/` files only):
5. Every public function, class, and method has a docstring (except items exempt per D107/D100/D104 in ruff config)
6. Docstrings are accurate and reflect actual behavior (Google style)

**Project conventions** (from CLAUDE.md):
7. No access to private members (underscore-prefixed) across package boundaries
8. American English spelling throughout

**Python** (when reviewing Python files):
9. F-strings used — no `%`-style formatting
10. No `Any` type hints without explicit justification
11. No `hasattr()` or `getattr()` without justification
12. Run `uv run ruff check <file>` and report any lint issues
13. Run `uv run mypy <file>` and report any type errors (src/ files only)

**Dart/Flutter** (when reviewing files in `app/`):
14. Run `dart format --output=none --set-exit-if-changed <file>` and report any formatting issues
15. Run `flutter analyze` and report any issues
16. Follow Dart style guide conventions (dart.dev/effective-dart)

Do not modify any files — this is a review-only command. Present all findings with suggested fixes.
