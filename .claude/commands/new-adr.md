---
description: Create the next numbered ADR from the template
argument-hint: <short title>
---

Create a new architecture decision record titled "$ARGUMENTS".

1. List `docs/adr/` and find the highest existing number `NNNN`. The new number is `NNNN + 1`, zero-padded to four digits.
2. Copy `docs/adr/0000-template.md` to `docs/adr/<number>-<kebab-case-title>.md`.
3. Fill in the title, today's date, and status `Proposed`. Draft Decision, Why, Alternatives, and Consequences from the conversation so far; ask me for anything you cannot infer.
4. Add a row to the index table in `docs/adr/README.md`.
5. Show me the file path. Do not commit.
