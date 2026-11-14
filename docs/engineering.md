# Engineering & operations

How code moves from a laptop to production and how production is kept safe.
Architecture rules are in `docs/architecture.md`; reasons are in the ADRs.

Status markers: **Open** = not decided yet (decision ID in brackets). **Optional** = improvement that is safe to
skip. Everything else is policy.

## 1. Toolchain and local environment (ADR-0010)

| Topic | Policy |
| --- | --- |
| Versions | Python 3.13, Django 5.2 LTS, PostgreSQL 17 — confirmed against official support schedules before M0 [E1] |
| Dependencies | uv manages Python, venv and dependencies; `uv.lock` committed; runtime deps in `[project.dependencies]`, tools in the `dev` group |
| Lock consistency | CI runs `uv lock --check`; CI and Docker install with `uv sync --locked`. `--frozen` only in local commands after CI has verified the lock. A dependency PR changes `pyproject.toml` and `uv.lock` together |
| Lint and format | Ruff (check + format) |
| Types | mypy on `*/domain.py`, `*/application.py`, `*/api.py`, `*/repositories.py`, `*/services.py`, `tests/fakes/` and the contract suite, with `disallow_untyped_defs`, `disallow_incomplete_defs`, `warn_return_any` (domain/application), `ignore_missing_imports` for `django.*` |
| Architecture checks | import-linter (`include_external_packages = true`) + relation allowlist test |
| Tests | pytest + pytest-django; markers `domain`, `app`, `integration`, `http`, `e2e`; Playwright for e2e |
| Local shape | PostgreSQL in Docker Compose (same major version as production); app runs on the host via uv; Compose also defines an `app` service on the `dev` image |
| Settings | `config/settings/{base,dev,test,prod}.py`; values from environment variables via a small typed helper `config/env.py` that fails on missing values in prod; `prod.py` asserts `DEBUG is False` |
| Commands | One `Makefile`: `setup`, `up`, `check`, `test-fast`, `test`, `e2e` — the same commands for you, agents and CI |
| Hooks | No pre-commit framework; `make check` runs the same checks as CI |
| Reproducibility | Fresh clone + Docker + uv → `make setup && make up && make test` passes |

## 2. Docker

One multi-stage `Dockerfile`:

- `builder`: official `python:3.13-slim` + uv binary from the official uv image; `uv sync --locked --no-dev`.
- `prod`: slim base; only `.venv`, `backend/`, `frontend/` and collected static; non-root user with fixed UID;
  `collectstatic` at build time with build-only settings (no secrets); Gunicorn with explicit `--timeout` and
  worker count from env; static files served by WhiteNoise with hashed names.
- `dev`: adds the `dev` group, mounts source, runs `runserver`.
- Media is never in the image: Django storage on a persistent volume (`/data/media`) [E11].
- `.dockerignore` excludes `.git`, `.env*`, tests, caches, local media.
- Images tagged with the full git SHA (releases also `vX.Y.Z`), pushed to GHCR.

### Health, readiness, restart, recovery

Docker and Compose do **not** restart a container because it is unhealthy.

| Mechanism | Behaviour | Setting |
| --- | --- | --- |
| `/healthz` | 200 if the process serves requests; no database call | Docker `HEALTHCHECK`, 30 s interval, 3 retries |
| `/readyz` | `SELECT 1` against PostgreSQL; 503 if unreachable | Used by deploy smoke tests and uptime monitor only |
| Schema check | `manage.py migrate --check` | Deploy step, not inside `/readyz` |
| Restart policy | Restarts on process exit (crash, OOM, reboot) | `restart: unless-stopped` on app, proxy, database |
| Gunicorn master | Replaces dead workers; kills workers past `--timeout` | — |
| Startup order | `depends_on: condition: service_healthy` | App → database |
| Deploy wait | `docker compose up -d --wait` fails if services don't become healthy | Deploy script |
| Running but unhealthy | Nothing automatic → uptime alert → runbook (logs, restart, rollback) | — |

## 3. Git and GitHub

Trunk-based: `main` is always deployable; every change is a PR from a short-lived branch (`feat/`, `fix/`,
`chore/`), one spec or milestone step per branch; squash merge, PR title = commit message referencing the spec.

**Approved [E4] — public repository on GitHub Free.** All code, documentation and history are publicly visible;
never commit secrets or confidential information. The capability comparison below is retained for reference:

| Feature | Public, any plan | Private, Pro/Team | Private, Free |
| --- | --- | --- | --- |
| Rulesets (branches and tags) | Yes | Yes | No |
| Environments, environment secrets, deployment tag policies | Yes | Yes | No |
| Required reviewers on environments | Yes | No | No |
| Secret scanning + push protection | Yes | Only with paid Secret Protection (Team/Enterprise) | No |

Repository settings (public GitHub Free):

- `main` ruleset: PR required, linear history, required status checks, no force-push, no deletion. With E4b
  option (a): one approving review required.
- `v*` tag ruleset: only Repository admin may create; nobody may update or delete.
- Merge method: squash only.
- Dependabot weekly for uv, GitHub Actions and Docker base images; Actions pinned to commit SHAs.
- Enable native secret scanning and push protection. Keep gitleaks in local `make check` and in the CI `secrets` job as defense in depth.
  Any exposed credential is rotated immediately; rewriting Git history alone does not revoke a secret.
- When production deployments are introduced, configure a `production` Environment with a required human reviewer and
  restrict its deployment refs to `v*` tags. Test that approval is enforced before deployment.
  The environment review gate supplements, rather than replaces, the staging-SHA and image-digest verification.

**Decided [E4b] — release identity model: (b), temporarily (ADR-0015).** Agents share the developer's local
credentials, so "only the human tags releases" is a documented policy, not a control; the human performs every remote
Git operation. The alternative, (a), is a dedicated machine account (collaborator, write access, 2FA) whose token
Claude Code uses, never your login, with Codex's identity verified; only you would bypass the tag ruleset. ADR-0015
lists the residual risk and when to revisit.

## 4. Continuous integration

Runs on every PR and push to `main`. All jobs block merge.

| Job | Checks |
| --- | --- |
| `quality` | `ruff format --check`, `ruff check`, `uv lock --check`, mypy, `lint-imports` |
| `test` | Domain + application tests with `DJANGO_SETTINGS_MODULE` unset; then full pytest against a PostgreSQL service container; relation allowlist; query budgets |
| `migrations` | `makemigrations --check --dry-run`; migrate an empty database; destructive-operation check (from M2); `check --deploy` with prod settings and dummy secrets |
| `security` | `pip-audit` on the exported lockfile (blocks on known vulnerabilities with an available fix) |
| `secrets` | gitleaks over the PR's commits (defense in depth alongside native push protection) |
| `image` | Build `prod` target, run against PostgreSQL, `/healthz` 200, `id -u` ≠ 0 (from Phase 1) |
| `e2e` | Playwright journeys against the `dev` app service (from M6) |

## 5. Continuous deployment and releases (ADR-0011)

| Step | Policy |
| --- | --- |
| Build | On merge to `main`, build the image once, tagged with the SHA |
| Staging | Deploy automatically: pull → `migrate` in a one-off container → `migrate --check` → restart with `--wait` → smoke tests. A GitHub Deployment (environment `staging`, ref = SHA) records the image digest; its status becomes `success` only after smoke tests pass |
| Release | You complete the release gate (section 9), then create annotated tag `vX.Y.Z` on the staged commit; the tag message links the checklist; GitHub Release notes from PR titles |
| Production | Triggered by a `v*` tag; the `production` environment accepts only `v*` tags. The job fails unless: (1) the tag commit is an ancestor of `origin/main`; (2) a successful staging Deployment exists for that exact SHA; (3) it deploys `image@sha256:<digest>` from that Deployment, never a tag or a rebuild |
| Production steps | Pre-deploy database dump → `migrate` → `migrate --check` → restart with `--wait` → smoke tests |
| Smoke tests | `/healthz`, `/readyz`, home, one listing, one product page return 200 |
| Rollback | Redeploy the previous image digest. Migrations are never reversed automatically (they are backward compatible) |
| Transport | SSH from Actions with a deploy-only key; `docker compose` on the host |
| Optional | Signed release tags (`git verify-tag` against an allowed signer stored as an environment variable; key on a hardware token). Required only if E4b = (b) and enforced human authorization is wanted |

## 6. Configuration and secrets

- Secrets only in environment variables. Local `.env` (gitignored); committed `.env.example` lists every variable
  without values.
- Deploy-time secrets in GitHub environment secrets (`staging`, `production` separate); runtime secrets in a
  root-owned `0600` env file on each host.
- Separate `SECRET_KEY`, database credentials and accounts per environment; no production data in staging or dev.
- Agents never receive real secrets (`AGENTS.md`).
- Settings are never logged; error reports scrub `password`, `token`, `secret`, `key` fields.

## 7. Security hardening

| Item | When |
| --- | --- |
| `check --deploy` passes with prod settings (CI) | M0 |
| `DEBUG=False`, explicit `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SECURE_PROXY_SSL_HEADER` | Phase 2 |
| HTTPS only: `SECURE_SSL_REDIRECT`, secure + HttpOnly session and CSRF cookies, `SameSite=Lax` | Phase 2 |
| HSTS: 1 hour on staging; 1 year in production after a week without issues; no preload | Phase 3 |
| Groups: Owner (catalogue, media, content permissions) and superuser; permission checked in every admin controller or hook | M5 |
| Staff login at a non-default URL; password validators with minimum length 12; inactivity session expiry | M5 |
| Host: SSH keys only, no root login, firewall 22/80/443, unattended OS security updates | Phase 2 |
| Database roles: `owner` runs migrations; `app` has SELECT/INSERT/UPDATE/DELETE only | Phase 2 |
| Deploy key limited to the deploy user; tokens with minimal scopes | Phase 2 |
| Django security releases applied within 7 days; green Dependabot PRs merged weekly | M0 onward |
| **Open [E16]** CSP, login rate limiting, staff 2FA | Before go-live |

Django's `check --deploy` warnings for rows not yet introduced are never suppressed. They are listed in
`deploy-warnings-deferred.txt` and printed by `make deploy-check` (CI job `migrations`). The gate reads Django's
structured check messages, not the printed text. It fails on any message that is not a listed warning (whatever its level
or id, including none), on a listed warning that is no longer reported, on an invalid list, and on any failure to run
the checks, so each phase removes its entries with its setting.

## 8. Migrations (ADR-0012)

- Every model change ships with its migration; CI fails on missing migrations.
- PRs show `sqlmigrate` output for migrations touching existing tables.
- Backward compatible by default (expand/contract): the previous release must run on the new schema.
- `RemoveField`, `DeleteModel`, `RenameField`, `RenameModel`, column type changes and `NOT NULL` without default
  fail a CI check unless listed in `migrations-approved.txt` with the release that completes the contract step.
- Data migrations have a reverse function or are marked irreversible with a reason.
- Production migrations run only through the pipeline, after the pre-deploy dump. No manual SQL except a runbook
  step recorded in the release notes.
- Concurrent index operations in non-atomic migrations once a table exceeds ~100k rows. Squashing deferred until a
  module exceeds ~50 migrations.

## 9. Quality gates

**Merge gate:** CI green; each acceptance criterion linked to evidence; independent agent review resolved; your
approval.

**Release gate:** release SHA on staging with smoke tests green; changed flows checked manually on staging;
migration notes reviewed; last data restore drill ≤ 35 days old; last full drill within the RTO target.

Other test policies: no coverage-percentage gate (report published); every bug fix adds a failing-first test;
test data from plain builder functions per module; permission matrix tests from M5.

## 10. Performance and observability

| Topic | Policy |
| --- | --- |
| Query budgets | Asserted in tests for home, listing, detail (`django_assert_max_num_queries`), from M4 |
| Request logs | Structured JSON to stdout via stdlib `logging`: time, level, request id, user id (not email), path, status, duration. Dev keeps plain text |
| Request id | Middleware; returned in a response header and logged |
| **Optional** production query metrics | Query count and DB time via `connection.execute_wrapper()` (integers only, no SQL). Enabled permanently only after staging validation: prod settings and real Gunicorn worker model; per-request counters if threads are used; under concurrent load each logged count equals the page's test budget; overhead of p50/p95 within an agreed threshold (proposal ≤ 2% of p95 or ≤ 1 ms, whichever is larger). Otherwise logs keep duration and status only |
| Exception reporting | **Open [E10]** Sentry free tier (PII off, scrubbing on) or Django error emails |
| Uptime | External monitor on `/readyz` and homepage, email alerts (Phase 3) |
| Logs on host | Docker `json-file` driver with size rotation |
| Images | WebP variants, `srcset`, explicit dimensions, lazy loading (see `docs/architecture.md`, Media) |
| Baseline | At go-live: server p95 for home/listing/detail and a mobile Lighthouse run (performance and accessibility), recorded in `docs/perf-baseline.md`; rerun per release; targets set after measurement [E15] and the accessibility level agreed in P7 |
| Dev tools | `django-debug-toolbar` in the `dev` group only |

## 11. Hosting, backups and recovery (ADR-0013)

**Open [E9]** Hosting. Proposal: one small Linux VPS per environment running Docker Compose with Caddy
(automatic HTTPS), app, PostgreSQL with a named volume, and the media volume.

### Backups [E14 for provider and retention]

1. Nightly host cron job: `pg_dump -Fc`, then media copy, both uploaded off-host to S3-compatible storage,
   encrypted before upload. Extra dump before every production migration.
2. Media copy never propagates deletions (copy, not mirror).
3. Verification: `pg_restore --list` on the new dump succeeds.
4. **Purge step, last:** only after dump, copy and verification succeed, the job runs a management command that
   physically removes files whose tombstone is older than this run's dump start.
5. Heartbeat to the uptime monitor only after all steps succeed; a missing heartbeat alerts.
6. Retention proposal: 7 daily, 4 weekly, 6 monthly; media objects kept in backup at least as long as the longest
   dump retention. Server credentials can write but not delete backups.

### Recovery [E13]

- Monthly data drill: restore latest dump + media into a scratch stack; `migrate --check`; every restored `Asset`
  reference (original and variants) resolves to an existing file (zero missing; orphans reported); three product
  pages render; elapsed time recorded in `docs/runbooks/restore-log.md`.
- Full drill before go-live and quarterly: fresh VPS, runbook only; elapsed time = measured RTO. A missed target
  means fixing the runbook or renegotiating E13.
- Runbooks in `docs/runbooks/` (deploy, rollback, restore, rotate secrets, HTTPS, disk full), written when each
  procedure is first executed.

### Maintenance

Weekly: merge green Dependabot PRs; review exception and uptime alerts. Monthly: restore drill, OS reboot if
needed, disk check, prune old images. Django/PostgreSQL: security patches within 7 days; major upgrades as their
own spec (move to the next Django LTS in its own release).

## 12. Process and documentation (ADR-0014)

1. **Spec** — `docs/specs/NNN-title.md` (template below); references ADRs instead of restating them.
2. **Implement** — one agent on a branch; reads `AGENTS.md`, the spec and only the named modules.
3. **Focused tests** — those listed in the spec, first where practical; `make check` green.
4. **Independent review** — the other agent reviews the PR diff against the spec and the `AGENTS.md` checklist.
5. **Acceptance** — you verify criteria with linked evidence; merge gate.
6. **Docs in the same PR** — spec status, ADR if a decision changed, critical-workflows row, runbook.

Documentation set: `README.md`, `AGENTS.md` (+ `CLAUDE.md` importing it), `docs/product.md`,
`docs/architecture.md`, `docs/engineering.md`, `docs/adr/`, `docs/specs/`, `docs/runbooks/`, `api.py` docstrings.
Every fact lives in one file; others link to it. Not created: per-module READMEs, wiki, changelog file.

Context sharing: specs point to paths and ADR numbers, never paste code or discussions; review handoff = PR link +
spec path; review results stay in the PR.

### Spec template

```markdown
# NNN — Title

Status: draft | in progress | done
Milestone: Mx
ADRs: 000X, 000Y

## Goal
One or two sentences.

## Acceptance criteria
- [ ] Observable, testable statement

## Out of scope
- ...

## Files expected to change
- path/...

## Tests to add
- level: what it proves
```

## 13. Phases

| Phase | With | Exit |
| --- | --- | --- |
| 0 Foundations | M0 | See `docs/specs/001-m0-foundation.md` |
| 1 Build-time quality | M1–M4 | Settings-free test step; destructive-migration check; query budgets; `image` job; prod image answers `/healthz` |
| 2 Staging | before/with M5 | E9–E12 decided; a merged PR reaches staging without manual steps; a broken release fails smoke tests and is rolled back by the runbook; JSON logs, request id, `/readyz`, exception reporting; two database roles; optional query metrics validated or left off |
| 3 Production | after M6 | E13–E16 decided; release checks reject a tag on a non-`main` commit and a tag on an unstaged SHA; `v1.0.0` runs the staging digest; tombstone purge active before the first production backup; first data and full restore drills passed; uptime and backup alerts triggered once; HSTS raised; performance baseline recorded |
| 4 Operating | continuous | Restore log entry ≤ 35 days old; no Django security release older than 7 days unapplied |

## 14. Deferred, with triggers

| Item | Trigger |
| --- | --- |
| Caching | p95 above target with query budgets met |
| Lighthouse CI | Repeated manual regressions |
| Point-in-time recovery | 24 h data loss no longer acceptable |
| Hosted log aggregation | Local logs insufficient in an incident |
| Image vulnerability scanning | Dependabot base-image updates insufficient |
| Pre-commit hooks | Frequent CI failures from formatting |
| `django-stubs` | ORM bugs that types would have caught |
| Restart-on-unhealthy watchdog | A running-but-unhealthy incident needed a manual restart |
| Optimistic locking for products | More than one editor expected |
| Background job runner | A workflow that must not run inside a request |
| Paid Secret Protection / Enterprise reviewers | Moving to a Team organization or a second person with deploy rights |
