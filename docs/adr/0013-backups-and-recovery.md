# 0013 — Backups and tested recovery objectives

Status: Accepted (targets and provider pending E13, E14)

**Context.** One host per environment; a backup that has never been restored is not a backup.

**Decision.** Nightly encrypted off-host dump and media copy (copy, not mirror), verified, followed by the
tombstone purge and a heartbeat. Recovery objectives are measured: monthly data drills and quarterly full drills
from a fresh host, including a check that every restored asset reference resolves to a file.

**Consequences.** Up to the agreed RPO of data loss; drill time is a recurring cost. Details:
`docs/engineering.md` §11.
