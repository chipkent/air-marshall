---
description: Improve Dartdoc quality and completeness
argument-hint: [file-or-directory ...]
disable-model-invocation: true
allowed-tools: Read, Edit, Grep, Glob
---

# Improve Dartdoc Comments

Improve the `///` Dartdoc comments in $ARGUMENTS for quality and completeness. If no file is specified, ask which file(s) to improve.

1. Ensure every public class, method, and property has a `///` Dartdoc comment. Skip private members (underscore-prefixed) and test files.
2. Descriptions should clearly explain *what* the code does and *why*, not just restate the signature.
3. Reference parameters inline using `[param]` syntax where it aids clarity.
4. Document return values and thrown exceptions where applicable.
5. Do not remove TODOs.
6. Do not change any logic or behavior — Dartdoc only.
