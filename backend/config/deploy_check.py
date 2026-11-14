"""Deployment-check gate: `python -m backend.config.deploy_check <deferred-file>`.

Runs Django's deployment system checks and classifies the structured `CheckMessage` objects they return; it never
parses the text that `manage.py check --deploy` prints. Only a warning whose id is listed in the deferred file is
accepted (and it is still printed). Everything else fails the gate: any other message of any level, including one
without an id or with an unfamiliar one, and a listed id that is no longer reported. Messages are not filtered by
`SILENCED_SYSTEM_CHECKS`. If the gate itself cannot run, it fails too (docs/engineering.md §7).
"""

import contextlib
import sys
import traceback
from pathlib import Path
from typing import Any

import django
from django.core import checks

EXIT_FAILED_TO_RUN = 2
EXIT_FINDINGS = 1


class DeferredConfigError(Exception):
    """The deferred-warnings file is missing, unreadable or malformed."""


def load_deferred(path: Path) -> frozenset[str]:
    """One check id per line; `#` starts a note. A missing file, a line with several tokens or a duplicate fails."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DeferredConfigError(f"cannot read {path}: {exc}") from exc
    ids: list[str] = []
    for number, line in enumerate(lines, start=1):
        entry = line.split("#", 1)[0].strip()
        if not entry:
            continue
        if len(entry.split()) != 1:
            raise DeferredConfigError(f"{path}:{number}: expected one check id per line, got {entry!r}")
        if entry in ids:
            raise DeferredConfigError(f"{path}:{number}: {entry} is listed twice")
        ids.append(entry)
    return frozenset(ids)


def classify(messages: list[Any], deferred: frozenset[str]) -> tuple[list[Any], list[Any], list[str]]:
    """Split every message into (deferred, unexpected) and list the deferred ids that were not reported.

    Only a WARNING can be deferred: an error, critical, info or debug message fails even if its id is listed. A message
    with no id can never match, so it is unexpected.
    """
    accepted: list[Any] = []
    unexpected: list[Any] = []
    # Django's check order varies; sort by id, never by rendered text, to keep the log stable.
    for message in sorted(messages, key=lambda message: message.id or ""):
        is_deferred = message.level == checks.WARNING and message.id in deferred
        (accepted if is_deferred else unexpected).append(message)
    stale = sorted(deferred - {message.id for message in accepted})
    return accepted, unexpected, stale


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m backend.config.deploy_check <deferred-file>", file=sys.stderr)
        return EXIT_FAILED_TO_RUN
    try:
        return _run(argv[0])
    # Every stage (list, setup, checks, classification, printing) is inside this boundary. SystemExit, even with
    # status 0, is a failure. KeyboardInterrupt and GeneratorExit are not caught.
    except (Exception, SystemExit) as exc:
        return _fail(exc)


def _run(deferred_path: str) -> int:
    deferred = load_deferred(Path(deferred_path))
    django.setup()
    messages = checks.run_checks(include_deployment_checks=True)

    accepted, unexpected, stale = classify(messages, deferred)
    print(f"deploy-check: {len(messages)} message(s): {len(accepted)} deferred, {len(unexpected)} unexpected")
    for message in accepted:
        print(f"[deferred]   {message}")
    for message in unexpected:
        print(f"[UNEXPECTED] {message}")
    if unexpected:
        print(f"deploy-check: FAILED: {len(unexpected)} message(s) are not deferred. Fix the setting.")
        print(f"  Only a warning deliberately deferred to a later phase may be added to {deferred_path}.")
    if stale:
        print(f"deploy-check: FAILED: listed in {deferred_path} but no longer reported as a warning: {' '.join(stale)}")
        print("  Remove those entries.")
    if unexpected or stale:
        return EXIT_FINDINGS
    print("deploy-check: OK; deferred warnings still reported:", *(message.id for message in accepted))
    return 0


def _fail(exc: BaseException) -> int:
    try:
        traceback.print_exception(exc)
        print(f"deploy-check: FAILED to run the deployment checks ({type(exc).__name__}: {exc})", file=sys.stderr)
    except (Exception, SystemExit):  # an error that cannot be rendered is still a failure
        with contextlib.suppress(Exception, SystemExit):  # if this fails too, the status below is all that is left
            print("deploy-check: FAILED to run the deployment checks (the error cannot be rendered)", file=sys.stderr)
    return EXIT_FAILED_TO_RUN


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
