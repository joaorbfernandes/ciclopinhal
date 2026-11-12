# 0005 — Validation layers and database constraints

Status: Accepted

**Context.** `Model.save()` does not call `full_clean()`; bulk operations and raw SQL skip validation entirely.

**Decision.** Forms validate shape, the domain validates meaning, and the database enforces every invariant that
must always hold (`Meta.constraints`), tested with direct invalid writes. Simple reference data (category, brand,
settings) relies on ModelForm validation plus database constraints until a real rule requires a use case.

**Consequences.** Some rules exist in two places (domain and constraint) by design. Constraint list:
`docs/architecture.md` §6.
