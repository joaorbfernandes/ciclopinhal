# 0015 — Agents share the developer's Git credentials (E4b, option b)

Status: Accepted (temporary; revisit triggers below)

**Context.** E4b asks whether Claude Code and Codex get their own GitHub identity (a machine account) or use the
developer's local credentials (b). The repository is public on GitHub Free, development is solo, and a second
GitHub account for agents is not wanted now.

**Decision.** Option (b). Agents run with the credentials already present on the developer's machine. To keep that
workable, the human performs every remote Git operation (push, pull request, merge, tag, release) and every
repository-settings change; agents work on local branches and commit only when asked.

**Residual risk.** Git and GitHub cannot tell an agent from the developer. "Agents never push to `main`" and "only
the human creates `v*` tags" are therefore documented policy (`AGENTS.md`), not controls: the `v*` tag ruleset limits
creation to the repository admin, and the shared identity is that admin. A mistaken or manipulated agent holding
these credentials could push a branch, open or merge a pull request, create a tag or change settings. Rulesets still
bind the identity if the admin role is not on their bypass list; leave it off the `main` ruleset.

**Mitigations.** `AGENTS.md` forbids those actions and forbids reading secrets; agents are given no deploy keys or
production secrets; the `main` ruleset requires a pull request and the five status checks; once deployments exist, the
`production` environment review gate and the staging-SHA and image-digest checks (ADR-0011) apply regardless of who
tagged.

**Revisit** by moving to option (a), or to signed tags (`docs/engineering.md` §5), before agents are allowed to push,
before a second person gets deploy rights, and in any case before the first production deployment (Phase 3).

**Consequences.** No machine account or agent token to manage. Release identity enforcement depends on process, as
stated in ADR-0011.
