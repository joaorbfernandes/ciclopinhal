# 0007 — Frontend/backend separation through DTOs

Status: Accepted

**Context.** V1 is server-rendered, but a future React frontend must not require rewriting rules or persistence.

**Decision.** `frontend/` (templates, CSS, JS) and `backend/` (Python) are separate directories in one
deployment. Templates receive only DTOs from query services; display decisions are made in DTOs. No REST API is
added in V1 for separation alone.

**Consequences.** Templates cannot trigger queries; a future API is a new adapter over the same use cases and
queries.
