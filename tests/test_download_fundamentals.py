from datetime import date

from scripts.download_fundamentals import (
    exception_status_code,
    extract_raw_times,
    normalize_event,
    release_timestamp,
)


def test_normalize_event_preserves_source_id_and_normalizes_holiday_values():
    event = normalize_event(
        date(2015, 1, 1),
        {
            "ID": "58395",
            "Time": "01/01/2015 00:00",
            "Currency": "USD",
            "Event": "Bank Holiday",
            "Forecast": "n/a",
            "Actual": "n/a",
            "Previous": "n/a",
            "Impact": "n/a",
        },
    )

    assert event is not None
    assert event["source_event_id"] == "58395"
    assert event["impact"] == "holiday"
    assert event["actual_raw"] == ""
    assert event["actual"] is None


def test_normalize_event_parses_real_time_and_thousands_separators():
    event = normalize_event(
        date(2020, 1, 10),
        {
            "ID": "123",
            "Time": "10/01/2020 08:30",
            "Currency": "USD",
            "Event": "Non-Farm Employment Change",
            "Forecast": "1,234K",
            "Actual": "1,250K",
            "Previous": "1,100K",
            "Impact": "high",
        },
    )

    assert event is not None
    assert event["time_kind"] == "scheduled"
    assert event["actual"] == 1250.0
    assert event["forecast"] == 1234.0
    assert event["previous"] == 1100.0


def test_release_timestamp_rejects_ambiguous_month_first_dates():
    timestamp, kind = release_timestamp(date(2020, 10, 1), "01/10/2020 08:30")

    assert kind == "scheduled"
    assert timestamp.isoformat() == "2020-10-01T12:30:00+00:00"


def test_exception_status_code_reads_nested_http_response():
    class Response:
        status_code = 429

    class HttpError(Exception):
        response = Response()

    error = RuntimeError("wrapped")
    error.__cause__ = HttpError("rate limited")

    assert exception_status_code(error) == 429


def test_extract_raw_times_preserves_calendar_semantics_and_inheritance():
        html = """
        <table>
            <tr class="calendar__row" data-event-id="1">
                <td class="calendar__time">All Day</td>
            </tr>
            <tr class="calendar__row" data-event-id="2">
                <td class="calendar__time"></td>
            </tr>
            <tr class="calendar__row" data-event-id="3">
                <td class="calendar__time">Tentative</td>
            </tr>
            <tr class="calendar__row" data-event-id="4">
                <td class="calendar__time">Day 1</td>
            </tr>
        </table>
        """

        assert extract_raw_times(html) == {
                "1": "All Day",
                "2": "All Day",
                "3": "Tentative",
                "4": "Day 1",
        }