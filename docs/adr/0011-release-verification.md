# 0011 — Single immutable image and release verification

Status: Accepted (release identity model: E4b option b, ADR-0015)

**Context.** The repository is public on GitHub Free, where environment required reviewers are available. An
agent using the developer's credentials is still indistinguishable from the developer for Git operations.

**Decision.** The image is built once per `main` commit and promoted by digest. Production runs only from a `v*`
tag and fails unless the tag commit is on `main`, a successful staging Deployment exists for that SHA, and the
deployed digest is the one recorded by that staging Deployment. Who may tag is enforced by a tag ruleset when
agents have their own identity (E4b a), otherwise by documented policy (E4b b).

**Consequences.** What reaches production must pass the staged-SHA and immutable-digest checks. A production
environment review gate adds human deployment approval; Git tag identity enforcement still depends on E4b.
Details: `docs/engineering.md` §3, §5.
