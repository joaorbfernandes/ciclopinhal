# 0003 — Repository contracts without framework types; query services for reads

Status: Accepted (contract style per aggregate pending the PoC)

**Context.** Use cases must be testable with fakes and independent of persistence mechanics, without duplicating
the ORM.

**Decision.** Use cases depend on `typing.Protocol` contracts owned by the consuming module, whose signatures
contain no Django types. One contract per aggregate written through use cases; no generic or per-model
repositories. Reads use concrete query services returning DTOs. A shared contract suite runs against fakes and
Django implementations.

**Consequences.** Application tests run without a database or Django settings; mapping code exists where
contracts are entity-based. Primitive/DTO vs entity contracts is decided by the PoC (`docs/architecture.md` §4).
