"""Infrastructure: pytest-django reaches PostgreSQL 17 and never touches the development database."""

import pytest
from django.db import connection


@pytest.mark.integration
@pytest.mark.django_db
def test_pytest_django_reaches_postgresql_17_test_database() -> None:
    assert connection.vendor == "postgresql"

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)

    # Server major version matches production and CI (E1).
    assert connection.pg_version // 10_000 == 17
    # pytest-django works on a separate `test_*` database, never on the development one.
    assert connection.settings_dict["NAME"].startswith("test_")
