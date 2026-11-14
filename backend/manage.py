#!/usr/bin/env python
"""Django command-line entry point: `python backend/manage.py <command>`."""

import os
import sys
from pathlib import Path


def main() -> None:
    # Replace the script directory (`backend/`) with the repository root so every module is imported as
    # `backend.<name>` and never under a second, top-level name.
    sys.path[0] = str(Path(__file__).resolve().parent.parent)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.dev")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
