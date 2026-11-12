# 0008 — Administration writes go through use cases

Status: Accepted (technology pending the administration spike)

**Context.** Admin tools write models directly by default (inlines, `form.save()`, bulk delete), which bypasses
domain rules.

**Decision.** Whichever tool is chosen — Django Admin or Wagtail for V1 — every write to Product, Asset, Homepage
or Menu goes through its use case, and known bypass paths are closed. The tool is chosen after a timeboxed spike
on W1 and W4 (`docs/architecture.md` §10). A fully custom backoffice is a future capability unless explicitly
approved for V1.

**Consequences.** Some admin customisation is needed in either candidate. Because rules live in use cases, a
later custom backoffice is a new interface adapter, not a rewrite.
