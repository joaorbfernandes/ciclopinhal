# 0014 — Specification-driven process with independent agent review

Status: Accepted

**Context.** A solo developer with two coding agents needs independent review and low context cost.

**Decision.** Every change follows spec → implementation → focused tests → review by the agent that did not
write it → human acceptance → documentation update in the same PR. `AGENTS.md` is the single agent rules file;
every fact lives in one document.

**Consequences.** One review round per PR; documentation stays current because it ships with the change.
Details: `docs/engineering.md` §12.
