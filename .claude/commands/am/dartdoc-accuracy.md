---
description: Correct inaccurate Dartdoc comments to match the actual implementation
argument-hint: [file-or-directory ...]
disable-model-invocation: true
allowed-tools: Read, Edit, Grep, Glob
---

# Dartdoc Accuracy Check

Check that the `///` Dartdoc comments in $ARGUMENTS are factually accurate and reflect the actual implementation. If no file is specified, ask which file(s) to review.

- Read the source code carefully, then read each Dartdoc comment.
- Correct any description, parameter reference, or return value that does not match what the code actually does.
- If a class, method, or property has no Dartdoc comment, skip it — use `/am:dartdoc-improve` to add missing comments.
- Do not remove TODOs.
- Do not change any logic or behavior — Dartdoc only.
