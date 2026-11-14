"""Locale is Portuguese (Portugal), times are shown in Lisbon, and the database stores UTC."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
from django.conf import settings
from django.db import connection
from django.utils import timezone, translation


@pytest.mark.integration
def test_locale_settings() -> None:
    assert settings.LANGUAGE_CODE == "pt-pt"
    assert settings.TIME_ZONE == "Europe/Lisbon"
    assert settings.USE_TZ is True
    assert translation.get_supported_language_variant(settings.LANGUAGE_CODE) in {"pt-pt", "pt"}


@pytest.mark.integration
@pytest.mark.django_db
def test_datetimes_are_aware_and_stored_as_utc() -> None:
    # The default time zone is Lisbon, but the connection and therefore every stored timestamp stay in UTC.
    assert timezone.get_current_timezone_name() == "Europe/Lisbon"
    assert connection.timezone_name == "UTC"
    assert settings.DATABASES["default"].get("TIME_ZONE") is None  # no per-database override

    # 12:00 in Lisbon during summer time (UTC+1) is 11:00 UTC; it comes back aware, in UTC, as the same instant.
    lisbon_noon = datetime(2026, 7, 1, 12, 0, tzinfo=ZoneInfo("Europe/Lisbon"))
    assert timezone.is_aware(timezone.now())
    with connection.cursor() as cursor:
        cursor.execute("SHOW TIME ZONE")
        assert cursor.fetchone() == ("UTC",)
        cursor.execute("SELECT %s::timestamptz", [lisbon_noon])
        (stored,) = cursor.fetchone()
    assert stored.utcoffset().total_seconds() == 0
    assert stored.hour == 11
    assert stored == lisbon_noon
    assert stored == datetime(2026, 7, 1, 11, 0, tzinfo=UTC)
