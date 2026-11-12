# 0004 — Transactions owned by use cases; savepoints for expected violations

Status: Accepted

**Context.** In PostgreSQL a failed statement aborts the whole transaction; retrying in the same transaction
without a rollback fails.

**Decision.** Each use case owns one transaction through the `core` transaction port; `ATOMIC_REQUESTS` is off;
repositories never commit. Expected constraint violations (e.g. duplicate slug) are caught in a nested
`atomic()` savepoint inside the repository, matched by constraint name, and translated to domain errors; the use
case decides on retries.

**Consequences.** Explicit transaction scope; repositories need constraint-name matching. Details:
`docs/architecture.md` §5.
