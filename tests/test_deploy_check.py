"""`make deploy-check` fails closed: every non-deferred message fails it and so does any failure to run it.

Regression tests for two defects of the first implementation, which parsed the text printed by
`manage.py check --deploy` in a shell pipeline:
  1. Warnings without an id, or with a dotted id such as `foundation.deploy.W001`, were printed but not counted.
  2. A failing parser command (exit status 23, say) did not fail the target.

The tests run the real target. A fixture settings module (production settings plus one extra check or setting)
and a fixture deferred file are injected through the Makefile variables DEPLOY_SETTINGS and DEPLOY_DEFERRED.
"""

import os
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import pytest
from django.core import checks

from backend.config.deploy_check import DeferredConfigError, classify, load_deferred

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFERRED_FILE = REPO_ROOT / "deploy-warnings-deferred.txt"
DEFERRED_IDS = ("security.W004", "security.W008", "security.W012", "security.W016")
FIXTURE_MODULE = "deploy_gate_fixture_settings"

_missing = [tool for tool in ("make", "uv") if shutil.which(tool) is None]
# make and uv are prerequisites (README). Missing locally (for example in the dev container) skips; in CI it must fail.
needs_make = pytest.mark.skipif(bool(_missing) and not os.environ.get("CI"), reason=f"{', '.join(_missing)} not found")
pytestmark = pytest.mark.integration


def _check_module(factory: str, extra: str = "") -> str:
    return textwrap.dedent(
        f"""
        from django.core import checks

        {extra}

        @checks.register(checks.Tags.security, deploy=True)
        def fixture_check(app_configs, **kwargs):
            return [{factory}]
        """
    )


_CRASHING_CHECK = textwrap.dedent(
    """
    from django.core import checks

    @checks.register(checks.Tags.security, deploy=True)
    def crashing_check(app_configs, **kwargs):
        raise RuntimeError("check failed")
    """
)

# Rendering must not be able to end the gate with 0: an error whose own text cannot be rendered, and a check message
# whose `obj` raises when it is converted to text.
_UNRENDERABLE_ERROR = textwrap.dedent(
    """
    class Unrenderable(Exception):
        def __str__(self):
            raise SystemExit(0)

    raise Unrenderable()
    """
)


def _unrenderable_message_module(check_id: str, exception: str) -> str:
    return textwrap.dedent(
        f"""
        from django.core import checks

        class Exploding:
            def __str__(self):
                raise {exception}

        @checks.register(checks.Tags.security, deploy=True)
        def fixture_check(app_configs, **kwargs):
            return [checks.Warning("Fixture warning.", obj=Exploding(), id="{check_id}")]
        """
    )


def _run_make(
    tmp_path: Path,
    *,
    settings_body: str | None = None,
    deferred_text: str | None = None,
    deferred_path: Path | None = None,
    broken_tools: tuple[str, ...] = (),
) -> tuple[int, str]:
    """Run `make deploy-check`; return (exit status, stdout + stderr)."""
    command = ["make", "deploy-check"]
    env = {**os.environ, "PYTHONPATH": str(tmp_path), "PYTHONDONTWRITEBYTECODE": "1"}
    if settings_body is not None:
        (tmp_path / f"{FIXTURE_MODULE}.py").write_text(
            "from backend.config.settings.prod import *  # noqa: F403\n" + settings_body, encoding="utf-8"
        )
        command.append(f"DEPLOY_SETTINGS={FIXTURE_MODULE}")
    if deferred_text is not None:
        deferred_path = tmp_path / "deferred.txt"
        deferred_path.write_text(deferred_text, encoding="utf-8")
    if deferred_path is not None:
        command.append(f"DEPLOY_DEFERRED={deferred_path}")
    if broken_tools:  # stand-ins that fail with status 23, ahead of the real tools on PATH
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        for tool in broken_tools:
            shim = bin_dir / tool
            shim.write_text("#!/bin/sh\nexit 23\n", encoding="utf-8")
            shim.chmod(0o755)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    result = subprocess.run(command, cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=120, check=False)
    return result.returncode, result.stdout + result.stderr


def _real_deferred() -> str:
    return DEFERRED_FILE.read_text(encoding="utf-8")


@needs_make
def test_real_configuration_passes_and_prints_every_deferred_warning(tmp_path: Path) -> None:
    status, output = _run_make(tmp_path)
    assert status == 0, output
    assert "4 deferred, 0 unexpected" in output
    for check_id in DEFERRED_IDS:
        assert f"({check_id})" in output, output
    assert output.count("[deferred]") == len(DEFERRED_IDS)
    assert "[UNEXPECTED]" not in output


# --- Defect 1: warnings the text parser missed -------------------------------------------------------------------


@needs_make
@pytest.mark.parametrize(
    "factory",
    [
        pytest.param('checks.Warning("Fixture warning without an id.")', id="no-id"),
        pytest.param('checks.Warning("Fixture warning.", id="foundation.deploy.W001")', id="dotted-id"),
        pytest.param('checks.Warning("Fixture warning.", id="W001")', id="no-namespace"),
        pytest.param('checks.Warning("Fixture warning.", id="a.b.c.d.X001")', id="deep-namespace"),
        pytest.param('checks.Warning("Fixture warning.", id="not an id!")', id="unfamiliar-id"),
    ],
)
def test_warning_that_is_not_deferred_fails_whatever_its_id(tmp_path: Path, factory: str) -> None:
    status, output = _run_make(tmp_path, settings_body=_check_module(factory), deferred_text=_real_deferred())
    assert status != 0, output
    assert "[UNEXPECTED]" in output
    assert "Fixture warning" in output
    assert "deploy-check: OK" not in output


@needs_make
@pytest.mark.parametrize(
    "factory",
    [
        pytest.param('checks.Info("Fixture note.", id="foundation.deploy.I001")', id="info"),
        pytest.param('checks.Debug("Fixture note.", id="foundation.deploy.D001")', id="debug"),
        pytest.param('checks.Error("Fixture error.", id="foundation.deploy.E001")', id="error"),
        pytest.param('checks.Critical("Fixture critical.", id="foundation.deploy.C001")', id="critical"),
    ],
)
def test_message_of_any_level_that_is_not_deferred_fails(tmp_path: Path, factory: str) -> None:
    status, output = _run_make(tmp_path, settings_body=_check_module(factory), deferred_text=_real_deferred())
    assert status != 0, output
    assert "[UNEXPECTED]" in output


@needs_make
def test_listing_an_id_defers_only_warnings(tmp_path: Path) -> None:
    body = _check_module('checks.Error("Fixture error.", id="foundation.deploy.E001")')
    status, output = _run_make(
        tmp_path, settings_body=body, deferred_text=_real_deferred() + "foundation.deploy.E001\n"
    )
    assert status != 0, output
    assert "[UNEXPECTED]" in output and "Fixture error" in output


@needs_make
def test_dotted_id_can_be_deferred_and_stays_visible(tmp_path: Path) -> None:
    body = _check_module('checks.Warning("Fixture warning.", id="foundation.deploy.W001")')
    deferred = _real_deferred() + "foundation.deploy.W001  # fixture\n"
    status, output = _run_make(tmp_path, settings_body=body, deferred_text=deferred)
    assert status == 0, output
    assert "5 deferred, 0 unexpected" in output
    assert "[deferred]   ?: (foundation.deploy.W001) Fixture warning." in output


@needs_make
def test_silenced_system_checks_do_not_hide_a_warning(tmp_path: Path) -> None:
    body = _check_module(
        'checks.Warning("Fixture warning.", id="foundation.deploy.W001")',
        extra='SILENCED_SYSTEM_CHECKS = ["foundation.deploy.W001"]',
    )
    status, output = _run_make(tmp_path, settings_body=body, deferred_text=_real_deferred())
    assert status != 0, output
    assert "[UNEXPECTED]" in output


@needs_make
def test_listed_warning_that_is_no_longer_reported_fails(tmp_path: Path) -> None:
    status, output = _run_make(tmp_path, deferred_text=_real_deferred() + "security.W099\n")
    assert status != 0, output
    assert "no longer reported" in output and "security.W099" in output


# --- Defect 2: failures that did not propagate -------------------------------------------------------------------


@needs_make
def test_failing_text_tools_cannot_turn_a_failing_check_into_success(tmp_path: Path) -> None:
    # The first implementation piped the check output through sed, sort and grep; with those exiting 23 it reported OK.
    body = _check_module('checks.Warning("Fixture warning without an id.")')
    status, output = _run_make(
        tmp_path,
        settings_body=body,
        deferred_text=_real_deferred(),
        broken_tools=("sed", "sort", "grep", "awk", "tr", "cut", "uniq"),
    )
    assert status != 0, output
    assert "[UNEXPECTED]" in output
    assert "deploy-check: OK" not in output


@needs_make
@pytest.mark.parametrize(
    "body",
    [
        pytest.param('raise RuntimeError("settings failed")', id="settings-raise"),
        pytest.param("raise SystemExit(23)", id="settings-exit-23"),
        pytest.param("raise SystemExit(0)", id="settings-exit-0"),
        pytest.param("import deploy_gate_module_that_does_not_exist", id="settings-import-error"),
        pytest.param(_CRASHING_CHECK, id="check-raises"),
        pytest.param(_UNRENDERABLE_ERROR, id="settings-error-cannot-be-rendered"),
    ],
)
def test_failure_to_run_the_checks_fails_closed(tmp_path: Path, body: str) -> None:
    status, output = _run_make(tmp_path, settings_body=body, deferred_text=_real_deferred())
    assert status != 0, output
    assert "FAILED to run the deployment checks" in output
    assert "deploy-check: OK" not in output


@needs_make
@pytest.mark.parametrize(
    ("listed", "exception"),
    [
        pytest.param(False, "SystemExit(0)", id="unlisted-exit-0"),
        pytest.param(True, "SystemExit(0)", id="listed-exit-0"),
        pytest.param(False, 'RuntimeError("cannot render")', id="unlisted-runtime-error"),
    ],
)
def test_message_that_cannot_be_rendered_fails_closed(tmp_path: Path, listed: bool, exception: str) -> None:
    # A real deployment warning whose `obj.__str__()` raises: sorting, printing or classifying it must not end the gate
    # with status 0 before the findings are classified.
    check_id = "foundation.deploy.W001"
    deferred = _real_deferred() + (f"{check_id}\n" if listed else "")
    body = _unrenderable_message_module(check_id, exception)
    status, output = _run_make(tmp_path, settings_body=body, deferred_text=deferred)
    assert status != 0, output
    assert "FAILED to run the deployment checks" in output
    assert "deploy-check: OK" not in output


@needs_make
def test_failure_report_that_cannot_be_written_fails_closed(tmp_path: Path) -> None:
    # The settings fail, then every write to stderr raises SystemExit(0): neither diagnostic can be written. The status
    # is all that is left, and it must still be non-zero. Nothing can be asserted about the output.
    body = textwrap.dedent(
        """
        import sys

        class UnwritableStderr:
            def write(self, text):
                raise SystemExit(0)

            def flush(self):
                pass

        sys.stderr = UnwritableStderr()
        raise RuntimeError("settings failed")
        """
    )
    status, output = _run_make(tmp_path, settings_body=body, deferred_text=_real_deferred())
    assert status != 0, output
    assert "deploy-check: OK" not in output


@needs_make
@pytest.mark.parametrize(
    "deferred_text",
    [
        pytest.param("security.W004 security.W008\n", id="two-ids-on-one-line"),
        pytest.param(
            "security.W004\nsecurity.W008\nsecurity.W012\nsecurity.W016\nsecurity.W004\n", id="duplicate-entry"
        ),
    ],
)
def test_invalid_deferred_configuration_fails_closed(tmp_path: Path, deferred_text: str) -> None:
    status, output = _run_make(tmp_path, deferred_text=deferred_text)
    assert status != 0, output
    assert "FAILED to run the deployment checks" in output
    assert "deploy-check: OK" not in output


@needs_make
@pytest.mark.parametrize("kind", ["missing", "directory"])
def test_unreadable_deferred_file_fails_closed(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "nope.txt" if kind == "missing" else tmp_path
    status, output = _run_make(tmp_path, deferred_path=path)
    assert status != 0, output
    assert "FAILED to run the deployment checks" in output
    assert "deploy-check: OK" not in output


# --- Classification itself ---------------------------------------------------------------------------------------


def test_every_message_is_classified_exactly_once() -> None:
    messages: list[Any] = [
        checks.Warning("no id"),
        checks.Warning("listed", id="a.b.W001"),
        checks.Warning("unlisted", id="a.b.W002"),
        checks.Error("listed but an error", id="a.b.W001"),
        checks.Info("info", id="a.b.I001"),
        checks.Debug("debug"),
    ]
    accepted, unexpected, stale = classify(messages, frozenset({"a.b.W001", "a.b.W003"}))
    assert [m.msg for m in accepted] == ["listed"]
    assert len(accepted) + len(unexpected) == len(messages)
    assert {id(m) for m in accepted}.isdisjoint({id(m) for m in unexpected})
    assert stale == ["a.b.W003"]


def test_deferred_file_must_be_well_formed(tmp_path: Path) -> None:
    good = tmp_path / "good.txt"
    good.write_text("# note\n\na.W001  # note\nb.c.W002\n", encoding="utf-8")
    assert load_deferred(good) == frozenset({"a.W001", "b.c.W002"})
    for name, text in {"two": "a.W001 b.W002\n", "dup": "a.W001\na.W001\n"}.items():
        bad = tmp_path / f"{name}.txt"
        bad.write_text(text, encoding="utf-8")
        with pytest.raises(DeferredConfigError):
            load_deferred(bad)
    with pytest.raises(DeferredConfigError):
        load_deferred(tmp_path / "missing.txt")
