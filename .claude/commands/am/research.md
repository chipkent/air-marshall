---
description: Research methodology and output format for technology and domain investigations
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, WebFetch, WebSearch
---

# Research Methodology

Use this process for all technology and domain research tasks.

## Process

1. **Define the question** — State the specific decision or question before researching. Avoid scope creep.
2. **Gather from authoritative sources** — Official documentation, datasheets, GitHub repos, and RFCs. Prefer primary sources over blog posts.
3. **Evaluate 2–4 options** — Do not evaluate more than 4; pick the most plausible candidates.
4. **Produce a structured report** (see format below).

## Output Format

For each research task, produce a report with this structure:

**Problem**: One paragraph describing the decision to be made and why it matters.

**Options**: A brief description of each candidate option (2–4).

**Tradeoffs**: A comparison table or bulleted list covering relevant dimensions (latency, reliability, complexity, community support, hardware compatibility, etc.).

**Recommendation**: A clear recommended option with rationale. If no single option is clearly superior, say so and explain what additional information would resolve the tie.

**Sources**: Numbered list of URLs or document references used.

**Unknowns**: Any assumptions made or open questions that need validation before acting on this recommendation.

## Constraints

- Never write code or modify any files.
- Flag when a question requires hands-on hardware testing that cannot be resolved through research alone.
- Use American English spelling throughout.
