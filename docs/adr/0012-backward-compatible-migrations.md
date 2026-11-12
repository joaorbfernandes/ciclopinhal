# 0012 — Backward-compatible migrations

Status: Accepted

**Context.** Rollback redeploys the previous image without reversing migrations.

**Decision.** Migrations are expand/contract: the previous release must run on the new schema. Destructive
operations fail CI unless listed in `migrations-approved.txt`. Production migrations run only in the pipeline,
after a pre-deploy dump.

**Consequences.** Removals and renames take two releases; rollback is always an image redeploy. Details:
`docs/engineering.md` §8.
