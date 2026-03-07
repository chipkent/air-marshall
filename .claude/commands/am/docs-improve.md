---
description: Systematically improve markdown documentation
argument-hint: [markdown-file ...]
disable-model-invocation: true
allowed-tools: Read, Edit, Grep, Glob, WebFetch
---

# Improve Markdown Documentation

Improve the markdown documentation in $ARGUMENTS. If no file is specified, ask which file(s) to improve.

1. **Content audit** — identify missing information by comparing docs against the source code (code is authoritative)
2. **Accuracy** — correct any factual errors
3. **Structure and reorganization** — improve the outline and logical flow; rearrange sections to match an improved outline
4. **Internal links** — ensure all relevant files and sections are linked
5. **Link validation** — verify all hyperlinks point to the correct destination
6. **External references** — identify products or services that should be hyperlinked
7. **General polish** — fix grammar, formatting, and clarity
8. **Lint check** — after making all changes, run markdownlint on modified files to catch any formatting issues introduced:
   `npx --yes markdownlint-cli2 --fix <modified-files>`

Only do major rewrites if clearly necessary. Prefer targeted improvements over wholesale revisions.
