# Only the `dev` target exists in M0. The `builder` and `prod` targets arrive with Phase 1 (docs/engineering.md §2).

FROM python:3.13-slim AS dev

# Keep the uv version in step with CI (.github/workflows/ci.yml) and `required-version` in pyproject.toml.
COPY --from=ghcr.io/astral-sh/uv:0.9.17 /uv /uvx /bin/

# The virtualenv lives outside /app so the bind-mounted source never shadows it.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=backend.config.settings.dev

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked

# Source is mounted by Compose; the command is overridden there as needed.
CMD ["python", "backend/manage.py", "runserver", "0.0.0.0:8000"]
