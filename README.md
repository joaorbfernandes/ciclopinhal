# CICLOPINHALEND

Configurable web platform for small businesses — website, product catalogue, brands, categories, images and
content managed through a simple backoffice — starting with Ciclopinhal.
Django + PostgreSQL modular monolith, built by one developer with Claude Code and Codex.

**Status:** pre-M0. The commands below exist only after M0 is complete (`docs/specs/001-m0-foundation.md`).

## Prerequisites

- Docker with Compose
- uv

## Everyday commands (after M0)

```sh
make setup      # install the locked environment (uv sync --locked)
make up         # start local PostgreSQL (Docker Compose)
make check      # format, lint, lockfile, types, architecture, secrets
make test-fast  # domain + application tests (no database)
make test       # full suite against PostgreSQL
make e2e        # critical browser journeys (from M6)
```

## Documentation

| Read | For |
| --- | --- |
| `docs/product.md` | What V1 does, what it does not, open product decisions |
| `docs/architecture.md` | Modules, boundaries, layers, critical workflows |
| `docs/engineering.md` | Toolchain, Git/CI/CD, security, data protection, operations |
| `docs/adr/` | Why key decisions were made (index in `docs/architecture.md`) |
| `docs/specs/` | Units of work with acceptance criteria |
| `AGENTS.md` | Rules for Claude Code and Codex |
