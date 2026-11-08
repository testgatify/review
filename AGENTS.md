# TestGatify Review — shared contributor and agent instructions

These public instructions apply to Codex, Claude Code and human contributors. Read this file, `HANDOFF.md`, `README.md`, `pyproject.toml`, and the relevant code/tests before editing. `CLAUDE.md` imports these same rules; no private document or chat history is required.

## Brand and product scope

- **TestGatify — Independent AI Testing & Evaluation** is the umbrella brand. Review is one existing open-source product, not the full scope of the brand.
- **TestGatify Review** generates structured test scenarios from requirements using Claude, applies deterministic static checks to scenario design, and exports Excel and Jira Xray CSV files.
- ACCEPT / MINOR REWORK / MAJOR REWORK describe scenario-design readiness. The gate does not execute the application, verify its behavior, or evaluate a deployed AI system. Keep this distinction in reports, examples and documentation.
- **TestGatify Operations** is a separate private management panel. **TestGatify Website** is a future corporate presentation site. LLM, RAG and Agent Evaluation tools are future work, not available capabilities of Review. An LLM-as-judge step or Playwright execution in the roadmap is not implemented functionality.
- Canonical public repositories are `testgatify/review` (this product) and `testgatify/.github` (brand profile). `testgatify-review` is the Python package/CLI name, not a different GitHub repository. Preserve both names in their proper contexts.

## Change workflow

1. Check the current branch, working tree and latest upstream changes. Preserve work already in progress. Use a separate branch and a PR; do not merge, rename/move repositories, or create services as part of an ordinary change.
2. Make the smallest change that satisfies the task. Preserve the existing package layout, CLI commands, config semantics, export formats and tests unless the task authorizes a change.
3. Use synthetic, public or explicitly permitted data. Never copy private plans, customer/employer records, financial information, unpublished datasets, internal reports, credentials or other private project files into this repository, its history, issues or PR descriptions.
4. Document present behavior separately from proposals. Do not invent model results, benchmarks, customers or certifications. Keep seeded examples clearly labeled as hand-written fixtures.
5. Do not make paid model calls or generate live model examples unless the user explicitly requests that action. Default verification is offline; generator tests use a fake client.
6. Run the existing test suite after changes, and report the exact results or blockers. Keep application execution and model evaluation out of static-gate claims.
7. At the end of each meaningful task, update `HANDOFF.md` with changes, tests, the PR/branch and the exact next step. In the PR, summarize changes, tests, limitations and next steps so another agent can continue. Chat memories and other repositories do not synchronize automatically. Carry across only public-safe decisions explicitly relevant to this product.

## Local verification

Python 3.10+; CI uses Python 3.12:

```sh
python -m venv .venv
# Activate .venv using the command for your shell.
python -m pip install -e '.[dev]'
python -m pytest -v
```

No API key is needed for tests, static review or export. Read `README.md` for CLI examples; `generate` and `run` can call the paid model API and are not offline verification commands.
## Persistent local Git synchronization

At the start of every work session, before editing files:
1. Run `git status --short --branch` to inspect the branch and local changes, then `git fetch origin`.
2. If the worktree is clean and the tracked upstream is only ahead, run `git pull --ff-only`. Continue if it is already current.
3. If there are local changes, conflicts, divergent branches, no tracked upstream, or a fetch/pull failure, preserve everything and report the blocker to the user. Do not reset, rebase, stash, or overwrite work to force synchronization.
4. After the Git check and any safe update, read `AGENTS.md`, `CLAUDE.md`, and `HANDOFF.md`, then the repository-specific files named above.
5. At the end of each meaningful task, update `HANDOFF.md` with changes, verification, and the next step. The update reaches other local copies only after commit and push.

This routine applies to the current local repository; it does not synchronize other repositories or chat histories.
