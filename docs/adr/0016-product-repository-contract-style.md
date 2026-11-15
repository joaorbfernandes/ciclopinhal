# 0016 — Product repository contracts exchange domain entities

Status: Accepted (Product aggregate only)

**Context.** ADR-0003 left open whether rule-bearing aggregates use primitive/DTO contracts (Variant D) or
domain-entity contracts (Variant E), to be decided by a PoC before M1 with the hard gates and selection rule in
`docs/architecture.md` §4. The PoC implemented the same minimal `CreateProduct` workflow in both styles, with the
same behavioural scenarios, fakes, Django repositories on PostgreSQL and database constraints. It ran on the
unmerged branch `spike/contract-style-poc`; its code and report are not part of the repository.

**Alternatives.**
- D: the contract carries plain frozen dataclasses; invariants live in pure functions that each use case calls before
  writing. Simpler code; enforcement depends on every write path calling the validator.
- E: the contract carries the `Product` entity, which cannot be constructed in an invalid state.

**Decision.** For the Product aggregate, Variant E:
- `ProductRepository` (a `typing.Protocol` in `catalog/application.py`) accepts and returns `Product` entities; its
  signatures contain no Django types.
- `Product` enforces its invariants on every construction, including copies and rehydration; a domain factory
  normalises input (e.g. trimming) before construction.
- The Django repository maps ORM rows to entities and back; loading a row validates the persisted state.
- Domain and application code import nothing from Django (unchanged, `AGENTS.md` rule 3).

**Evidence.** Both variants passed every hard gate and the same behavioural tests, and both behave correctly
through `CreateProduct`; D is not shown to produce wrong data through the supported use case. Final verification:
`make check` passed, `make test-fast` 117 passed, `make test` 227 passed against PostgreSQL 17; the independent
review approved the result. Scoring under §4:

| Criterion | Result |
| --- | --- |
| Rule enforcement locality (primary) | E wins: each invariant is enforced in one place, whatever the caller |
| Implementation complexity | D wins |
| Mapping/DTO overhead, required unique SKU change cost, test clarity, reviewability | Tie |

E wins the primary criterion and is worse on one other, within the rule's limit of two.

**Consequences.**
- Mapping code exists in the repository (row ↔ entity), as ADR-0003 anticipated.
- Python cannot restrict construction to a factory; a rule that must hold for every instance belongs in the
  entity's construction check, and a factory-only check is a defect. Deliberate bypasses (e.g. `object.__setattr__`)
  remain possible and are a review matter.
- Rehydration validates, so tightening an invariant can make existing rows impossible to load as `Product`
  entities; edit and delete use cases then fail for them. Public pages are unaffected because reads go through query
  services returning DTOs (architecture §3). A spec that tightens a Product invariant must:
  1. assess existing data before deployment (query for violating rows);
  2. plan data corrections under ADR-0012, or state explicit compatibility handling (e.g. the rule applies to new
     writes only and is not part of rehydration);
  3. coordinate the domain rule with a database constraint where one can express it (ADR-0005);
  4. include a test that a representative historical row still loads, or fails as the spec intends.
- PostgreSQL enforces constraints identically in both styles; database constraints stay required (ADR-0005).

**Limitations.**
- Applies to Product only. Every other aggregate (Asset, Homepage, Menu) chooses its contract style in the spec that
  introduces it, under the same hard gates; entity contracts are not imposed by this decision.
- The PoC covered one aggregate and one workflow; it ran locally, not in CI.
- Not approved by this ADR: slug format (D12), SKU policy, name limits, price precision and the P4 pricing rules. The
  PoC used them as experimental rules only; they are decided in `docs/product.md` §7 and the milestone specs.
