# 0001 — Django/PostgreSQL modular monolith

Status: Accepted

**Context.** One developer with two coding agents; a small business site that must later grow (filters, APIs,
checkout) without a rewrite.

**Decision.** One Django application in one deployment, split into modules with owned rules and one-way
dependencies. PostgreSQL is the only database. No microservices, queues or distributed components.

**Consequences.** Simple operations and transactions; boundaries must be enforced by tooling (ADR-0002) rather
than by network separation.

Details: `docs/architecture.md` §1.
