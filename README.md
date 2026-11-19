# CICLOPINHALEND

Configurable web platform for small businesses — website, product catalogue, brands, categories, images,
services, events and content managed through a simple backoffice — starting with Ciclopinhal.
Django + PostgreSQL modular monolith, built by one developer with Claude Code and Codex.

**Status:** M0 (repository foundation, `docs/specs/001-m0-foundation.md`) and M1 (catalog domain and `CreateProduct`
without persistence, `docs/specs/002-m1-catalog-domain.md`) are done. Next: M2 (catalog persistence) and, in parallel,
the UX0 discovery and design track. The full V1 roadmap is in `docs/architecture.md` §13.

## Prerequisites

- Docker with Compose
- uv

## Everyday commands

```sh
make setup      # install the locked environment (uv sync --locked)
make up         # start local PostgreSQL (Docker Compose)
make check      # format, lint, lockfile, types, architecture, secrets
make test-fast  # domain + application tests (no database)
make test       # full suite against PostgreSQL
make e2e        # critical browser journeys (from M6)
```

A fresh clone with Docker and uv runs `make setup && make up && make test`. The local database listens on
`127.0.0.1:5433`; change that or any other setting in an untracked `.env` (names in `.env.example`). To run the app
in the `dev` image instead of on the host: `docker compose --profile app up`.

## Documentation

| Read | For |
| --- | --- |
| `docs/product.md` | What V1 does, what it does not, open product decisions |
| `docs/architecture.md` | Modules, boundaries, layers, critical workflows |
| `docs/engineering.md` | Toolchain, Git/CI/CD, security, data protection, operations |
| `docs/adr/` | Why key decisions were made (index in `docs/architecture.md`) |
| `docs/specs/` | Units of work with acceptance criteria |
| `AGENTS.md` | Rules for Claude Code and Codex |
