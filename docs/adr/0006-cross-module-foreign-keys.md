# 0006 — Cross-module foreign keys

Status: Accepted (on-delete behaviour of featured selections pending D4)

**Context.** Application imports and database references are different couplings; import-linter cannot see
string-label foreign keys.

**Decision.** Foreign keys may cross modules only in the allowed direction, declared by string label with
`related_name="+"`. No ORM traversal across modules. A pytest test compares all cross-module relations with an
explicit allowlist. `PROTECT` for every reference to a media asset (product gallery, brand logo, homepage
content, site logo), so an image still in use cannot be removed.

**Consequences.** PostgreSQL guarantees referential integrity without media knowing its users; adding a
cross-module relation is a deliberate allowlist change. Site identity lives in `content` (not `core`) because it
references a media asset.
