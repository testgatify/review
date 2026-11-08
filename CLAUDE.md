@AGENTS.md

Use the shared public instructions in `AGENTS.md` and the current product scope in `README.md`. This file does not introduce a separate strategy or require access to private TestGatify project documents.
Codex and Claude Code use the same persistent Git start and handoff rules in the “Persistent local Git synchronization” section of `AGENTS.md`. Check `git status --short --branch`, run `git fetch origin`, and use `git pull --ff-only` only for a clean branch that can fast-forward. Report blockers without overwriting work. Then read `AGENTS.md`, `CLAUDE.md`, and `HANDOFF.md`.
