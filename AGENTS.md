# AGENTS.md

Rules for Claude Code and Codex. This is the only agent rules file; `CLAUDE.md` imports it.
Propose changes to this file by PR, one line at a time.

## Start of every task

1. Read the spec you were given (`docs/specs/NNN-*.md`).
2. Read only the modules and documents the spec names. For anything else, open the relevant section of
   `docs/architecture.md` or `docs/engineering.md`, not whole documents.
3. If the spec is ambiguous or contradicts the docs, stop and ask in the PR. Do not guess.

## Commands

| Command | Use |
| --- | --- |
| `make check` | Before every push: Ruff format/lint, `uv lock --check`, mypy, import-linter, gitleaks |
| `make test-fast` | Domain and application tests, no database, no Django settings |
| `make test` | Full suite against PostgreSQL |
| `make e2e` | Playwright critical journeys |

## Architecture rules (details and reasons: `docs/architecture.md`)

1. Domain modules `core`, `media`, `catalog`, `content`; interface modules `storefront`, `backoffice`.
   Dependency direction: `content → catalog → media → core`. Nothing depends on interface modules.
2. Another module is imported only through its `api.py`.
3. `domain.py` and `application.py` import nothing from `django` or from `models`, `repositories`, `queries`.
4. Repository contracts are `typing.Protocol`s whose signatures contain no Django types.
5. Every write to Product, Asset, Homepage or Menu goes through its use case — including from any admin tool.
6. Reads go through query services that return DTOs. Templates never receive model instances or querysets.
7. The use case owns the transaction. Repositories never commit. An expected constraint violation is caught
   inside a savepoint in the repository; never run another query after an uncaught database error.
8. Invariants that must always hold are database constraints as well. `Model.save()` does not run `full_clean()`.
9. Cross-module foreign keys: string label, `related_name="+"`, listed in the relation allowlist test.
   No ORM traversal across module boundaries.
10. Media files are immutable and never physically deleted by application code (tombstones only).
11. Do not add dependencies, modules, layers, abstractions or features the spec does not ask for.

## Forbidden

- Reading, printing, copying or committing `.env` files, production env files, keys or tokens.
- Pushing to `main`; creating, moving or deleting tags; changing repository settings, rulesets or secrets.
- Running anything against staging or production.
- Editing a migration that is already on `main`.
- Adding a destructive migration operation without an entry in `migrations-approved.txt` approved in the spec.
- Skipping, weakening or deleting tests or checks to make CI pass.
- Using `uv sync --frozen` in CI or Docker (use `--locked`).

## Definition of done

- Every acceptance criterion in the spec is met; the PR description links each one to its evidence (test name).
- `make check` and `make test` green locally; CI green.
- Migrations included; `sqlmigrate` output in the PR for any migration touching existing tables.
- Bug fixes include a test that failed before the fix.
- Same PR updates: spec status; an ADR if a decision was made or changed; the critical-workflows table in
  `docs/architecture.md` if an entry point or use case changed; a runbook if an operation changed.

## Review checklist (reviewing agent)

- **Scope:** every acceptance criterion covered; nothing outside the spec added.
- **Boundaries:** cross-module imports via `api.py`; no Django in domain/application; no cross-module ORM traversal.
- **Contracts:** no Django types; fake and Django implementations both pass the contract suite; mypy clean.
- **Transactions:** use case owns `atomic()`; savepoints only around expected violations.
- **Integrity:** required database constraints exist and are tested with direct ORM writes.
- **Permissions:** each new backoffice endpoint tested for anonymous, staff without permission, and permitted user.
- **Queries:** public-page query budgets unchanged, or changed with a stated reason.
- **Migrations:** compatible with the previous release; destructive operations approved.
- **Admin tooling:** no write path bypasses use cases (inlines, `form.save()`, bulk delete actions).
- **Logs:** no secrets, SQL text or personal data.
- **Docs:** critical-workflows table and spec status updated.

Blocking findings are fixed or answered in the PR before approval.

## Roles

The agent that wrote a change never reviews it. The human approves every merge and is the only one who creates
release tags.
