# 0009 — Immutable media files and deferred physical deletion

Status: Accepted (variant timing pending the M3 measurement)

**Context.** A database dump and a media copy are taken at different moments; deleting a file between them would
leave a restored row pointing to a missing file.

**Decision.** Media files are immutable (generated names, never overwritten). Deleting an asset removes its row
and records a tombstone in the same transaction; files are physically removed only by the backup job's final
step, after dump, copy and verification succeed, and only for tombstones older than that run's dump start.

**Consequences.** Temporary extra disk usage; restore drills must find zero missing files. Details:
`docs/architecture.md` §8, `docs/engineering.md` §11.
