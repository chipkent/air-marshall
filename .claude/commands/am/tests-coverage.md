---
description: Write missing Python unit tests until all source files reach 100% coverage
argument-hint: [source-file ...]
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Test Coverage

Drive Python unit test coverage to 100%. If file(s) are specified via `$ARGUMENTS`, limit work to those files only. Otherwise, process all files in `src/air_marshall/`.

For each source file:

1. Verify a corresponding test file exists — create it if it does not (`src/air_marshall/<subpackage>/foo.py` → `tests/<subpackage>/test_foo.py`)
2. Run that test file individually: `uv run pytest tests/<subpackage>/test_foo.py -v`
3. Read the `term-missing` coverage output to identify uncovered lines in the source file
4. Add missing test cases until the file reaches 100% coverage. For async functions, mark tests with `@pytest.mark.asyncio` (project uses `asyncio_mode = "strict"`).
5. Flag any tests that appear redundant or meaningless and ask before removing them

Run test files one-by-one — the coverage report will show per-file line coverage for the full `air_marshall` package, making it clear which lines in the target file are still uncovered.

After processing all target files, run the full test suite to confirm everything passes together:
`uv run pytest`
