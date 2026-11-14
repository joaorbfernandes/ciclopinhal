"""Architecture rule 9: a relation between two project modules is allowed only when listed here.

Cross-module foreign keys use a string label and `related_name="+"` (ADR-0006). Each entry is
"<app_label>.<Model>.<field>"; a milestone adds an entry together with the relation it introduces.
"""

from typing import Any

import pytest
from django.apps import apps

# Empty in M0: there are no project models yet.
ALLOWED_CROSS_MODULE_RELATIONS: frozenset[str] = frozenset()


def _project_cross_module_relations() -> dict[str, Any]:
    """Forward relations declared on project models that point at a model of another app."""
    project_labels = {config.label for config in apps.get_app_configs() if config.name.startswith("backend.")}
    found: dict[str, Any] = {}
    for model in apps.get_models():
        if model._meta.app_label not in project_labels:
            continue
        for field in model._meta.get_fields():
            if not field.is_relation or field.auto_created or field.related_model is None:
                continue
            if field.related_model._meta.app_label == model._meta.app_label:
                continue
            found[f"{model._meta.app_label}.{model.__name__}.{field.name}"] = field
    return found


@pytest.mark.integration
def test_cross_module_relations_are_allowlisted_and_use_no_reverse_accessor() -> None:
    found = _project_cross_module_relations()

    not_allowed = sorted(set(found) - ALLOWED_CROSS_MODULE_RELATIONS)
    assert not not_allowed, f"Cross-module relations missing from the allowlist: {not_allowed}"

    reverse_accessors = sorted(name for name, field in found.items() if field.remote_field.related_name != "+")
    assert not reverse_accessors, f'Cross-module relations must set related_name="+": {reverse_accessors}'


@pytest.mark.integration
def test_allowlist_has_no_stale_entries() -> None:
    stale = sorted(ALLOWED_CROSS_MODULE_RELATIONS - set(_project_cross_module_relations()))
    assert not stale, f"Allowlist entries that match no relation: {stale}"
