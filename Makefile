# One entry point for developers, agents and CI (docs/engineering.md §1).
#
# Public targets:  setup  up  check  test-fast  test      (e2e is added in M6)
# `check` is the sum of lint, lock-check, typecheck, imports and secrets; CI calls those parts as separate steps.
# `deploy-check` is run by the CI `migrations` job and is not part of `check`.

# Optional local overrides: KEY=value lines, no quotes (see .env.example). Ignored by Git and Docker.
-include .env
export

UV_RUN := uv run --frozen
# mypy scope (docs/engineering.md §1): contracts, implementations, composition roots, fakes. `wildcard` keeps it empty-safe
# until the modules exist; `backend/config/env.py` is typed and keeps the check meaningful in M0. The contract suite
# joins the scope in M1.
MYPY_SCOPE := backend/config/env.py backend/config/deploy_check.py \
	$(wildcard backend/*/domain.py backend/*/application.py backend/*/api.py backend/*/repositories.py backend/*/services.py) \
	$(wildcard tests/fakes)
# Pinned by tag and digest. The Docker image is the only gitleaks install, so Docker + uv are the only prerequisites.
GITLEAKS_IMAGE := ghcr.io/gitleaks/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f
GITLEAKS := docker run --rm --user "$$(id -u):$$(id -g)" -v "$(CURDIR):/repo" $(GITLEAKS_IMAGE)

DEPLOY_SETTINGS := backend.config.settings.prod
DEPLOY_DEFERRED := deploy-warnings-deferred.txt

.PHONY: setup up check lint lock-check typecheck imports secrets deploy-check test-fast test

setup:
	uv sync --locked

up:
	docker compose up -d --wait db

check: lint lock-check typecheck imports secrets

lint:
	$(UV_RUN) ruff format --check .
	$(UV_RUN) ruff check .

lock-check:
	uv lock --check

typecheck:
	$(UV_RUN) mypy $(MYPY_SCOPE)

imports:
	$(UV_RUN) lint-imports

# Commit history, then the working tree (uncommitted and untracked files). Findings are redacted in the output.
secrets:
	$(GITLEAKS) git --no-banner --redact /repo
	$(GITLEAKS) dir --no-banner --redact /repo

# Django's deployment checks with production settings and dummy values (no real secret, no database connection).
# backend/config/deploy_check.py reads the structured check messages (no text parsing) and prints every one. Known
# deferred warnings (DEPLOY_DEFERRED) are accepted; any other message fails, and so does a listed warning that is no longer
# reported, and so does any failure to run the checks. The environment is set explicitly so a local .env cannot change
# the result; the single command keeps its exit status (no pipeline).
deploy-check:
	@secret="$$($(UV_RUN) python -c 'import secrets; print(secrets.token_urlsafe(64))')" && \
	DJANGO_SETTINGS_MODULE=$(DEPLOY_SETTINGS) SECRET_KEY="$$secret" ALLOWED_HOSTS=example.invalid DEBUG=false \
	  POSTGRES_DB=dummy POSTGRES_USER=dummy POSTGRES_PASSWORD=dummy POSTGRES_HOST=localhost POSTGRES_PORT=5432 \
	  $(UV_RUN) python -m backend.config.deploy_check $(DEPLOY_DEFERRED)

# Domain and application tests: no Django settings, no database.
# pytest exits with 5 when nothing is collected; none exist until M1, so that case is reported and accepted.
test-fast:
	@env -u DJANGO_SETTINGS_MODULE $(UV_RUN) pytest -m "domain or app"; rc=$$?; \
	if [ $$rc -eq 5 ]; then echo "test-fast: no domain or application tests yet (first ones arrive in M1)"; exit 0; fi; \
	exit $$rc

# Everything, with the test settings, against the PostgreSQL started by `make up`.
test: test-fast
	DJANGO_SETTINGS_MODULE=backend.config.settings.test $(UV_RUN) pytest
