# 0010 — Toolchain and reproducible environments

Status: Accepted (versions to confirm, E1)

**Context.** Laptop, CI, agents and Docker must install identical dependencies and run identical checks.

**Decision.** uv with a committed `uv.lock`, verified by `uv lock --check` and installed with `uv sync --locked`;
Ruff; mypy scoped to contracts, implementations, composition roots and fakes with complete-annotation flags;
import-linter; pytest. One Makefile as the shared entry point. PostgreSQL in Docker Compose locally.

**Consequences.** Stale lockfiles and protocol mismatches fail CI; ORM calls stay untyped (django-stubs
deferred). Details: `docs/engineering.md` §1.
