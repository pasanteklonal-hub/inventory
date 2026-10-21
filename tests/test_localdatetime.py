from datetime import datetime, timezone

from app import format_local_datetime


def test_format_local_datetime_converts_utc_to_system_timezone():
    value = datetime(2024, 1, 2, 3, 4)

    expected = value.replace(tzinfo=timezone.utc).astimezone().strftime('%d/%m/%Y %H:%M')
    assert format_local_datetime(value) == expected
