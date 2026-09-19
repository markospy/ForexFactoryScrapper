#!/usr/bin/env python3
"""Download and build a typed ForexFactory economic-calendar Parquet.

The raw response is retained as JSON and the queryable derivative is a single
``calendar.parquet`` with UTC timestamps and typed numeric values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterable
from zoneinfo import ZoneInfo


LOGGER = logging.getLogger("download_fundamentals")
SYMBOL_RE = re.compile(r"^[A-Z]{6}$")
FOREX_CURRENCIES = {"AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "USD"}
NEW_YORK = ZoneInfo("America/New_York")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download ForexFactory daily events for market Parquet symbols."
    )
    parser.add_argument(
        "--parquet-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "backend/data/market",
        help="Directory containing one SYMBOL.parquet file per forex pair.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "fundamentals",
        help="Directory for raw JSON, staging files, calendar.parquet, and progress.json.",
    )
    parser.add_argument("--start", type=date.fromisoformat, default=date(2015, 1, 1))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2026, 8, 30))
    parser.add_argument("--retry-count", type=int, default=5)
    parser.add_argument("--retry-delay", type=float, default=5.0)
    parser.add_argument("--request-delay", type=float, default=1.0)
    parser.add_argument("--max-days", type=int, help="Stop after this many new days.")
    parser.add_argument("--force", action="store_true", help="Redownload completed days.")
    parser.add_argument("--dry-run", action="store_true", help="Only list discovered pairs.")
    return parser.parse_args()


def discover_symbols(parquet_dir: Path) -> dict[str, tuple[str, str]]:
    """Return symbols and their base/quote currencies from Parquet filenames."""
    if not parquet_dir.is_dir():
        raise FileNotFoundError(f"Parquet directory does not exist: {parquet_dir}")

    symbols: dict[str, tuple[str, str]] = {}
    for path in sorted(parquet_dir.glob("*.parquet")):
        symbol = path.stem.upper()
        if SYMBOL_RE.fullmatch(symbol) and symbol[:3] in FOREX_CURRENCIES and symbol[3:] in FOREX_CURRENCIES:
            symbols[symbol] = (symbol[:3], symbol[3:])
        else:
            LOGGER.warning("Ignoring non-forex Parquet filename: %s", path.name)
    if not symbols:
        raise RuntimeError(f"No SYMBOL.parquet files found in {parquet_dir}")
    return symbols


def record_to_dict(record: Any) -> dict[str, Any]:
    if hasattr(record, "model_dump"):
        return record.model_dump(by_alias=True)
    if isinstance(record, dict):
        return dict(record)
    raise TypeError(f"Unsupported scraper record type: {type(record)!r}")


def get_field(record: dict[str, Any], name: str) -> Any:
    """Read either forex-pytory aliases (Currency) or normalized keys."""
    return record.get(name) if name in record else record.get(name.lower())


def parse_event_value(value: Any) -> tuple[float | None, str]:
    raw = "" if value is None else str(value).strip()
    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*([KMB%]?)", raw, re.IGNORECASE)
    if not match:
        return None, ""
    return float(match.group(1)), match.group(2).upper()


def parse_event_date(value: Any, fallback: date) -> date:
    raw = "" if value is None else str(value).strip()
    for pattern in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, pattern).date()
        except ValueError:
            continue
    return fallback


def release_timestamp(day: date, raw_time: Any) -> tuple[datetime, str]:
    text = "" if raw_time is None else str(raw_time).strip().lower()
    if "tentative" in text:
        kind = "tentative"
    elif not text or "all day" in text or text in {"day", "-", "n/a"}:
        kind = "all_day"
    else:
        kind = "scheduled"

    if kind == "scheduled":
        for pattern in ("%m/%d/%Y %H:%M", "%m/%d/%Y %I:%M%p", "%m/%d/%Y %I:%M %p"):
            try:
                parsed_datetime = datetime.strptime(text.upper(), pattern)
                local = parsed_datetime.replace(tzinfo=NEW_YORK)
                return local.astimezone(timezone.utc), kind
            except ValueError:
                continue

        parsed_time: datetime_time | None = None
        for pattern in ("%I:%M%p", "%I:%M %p", "%H:%M"):
            try:
                parsed_time = datetime.strptime(text.upper(), pattern).time()
                break
            except ValueError:
                continue
        if parsed_time is None:
            LOGGER.warning("Unknown event time %r on %s; treating as all_day", raw_time, day)
            kind = "all_day"
        else:
            local = datetime.combine(day, parsed_time, tzinfo=NEW_YORK)
            return local.astimezone(timezone.utc), kind

    # No release clock exists. The UTC day boundary prevents early disclosure.
    return datetime.combine(day + timedelta(days=1), datetime_time.min, tzinfo=timezone.utc), kind


def normalize_event(day: date, raw_record: dict[str, Any]) -> dict[str, Any] | None:
    currency = str(get_field(raw_record, "Currency") or "").upper()
    if currency not in FOREX_CURRENCIES:
        return None
    event_name = str(get_field(raw_record, "Event") or "").strip()
    if not event_name:
        return None
    event_day = parse_event_date(get_field(raw_record, "Date"), day)
    release_at, time_kind = release_timestamp(event_day, get_field(raw_record, "Time"))
    impact = str(get_field(raw_record, "Impact") or "").strip().lower()
    impact = {"high impact": "high", "medium impact": "medium", "low impact": "low"}.get(impact, impact)
    actual_raw = "" if get_field(raw_record, "Actual") is None else str(get_field(raw_record, "Actual")).strip()
    forecast_raw = "" if get_field(raw_record, "Forecast") is None else str(get_field(raw_record, "Forecast")).strip()
    previous_raw = "" if get_field(raw_record, "Previous") is None else str(get_field(raw_record, "Previous")).strip()
    actual, actual_unit = parse_event_value(actual_raw)
    forecast, forecast_unit = parse_event_value(forecast_raw)
    previous, previous_unit = parse_event_value(previous_raw)
    unit = actual_unit or forecast_unit or previous_unit
    event_id = hashlib.sha256(
        f"{release_at.isoformat()}|{currency}|{event_name}".encode("utf-8")
    ).hexdigest()
    return {
        "event_id": event_id,
        "release_at": release_at,
        "time_kind": time_kind,
        "currency": currency,
        "event_name": event_name,
        "impact": impact or "unknown",
        "actual": actual,
        "forecast": forecast,
        "previous": previous,
        "unit": unit,
        "actual_raw": actual_raw,
        "forecast_raw": forecast_raw,
        "previous_raw": previous_raw,
        "source": "forexfactory",
    }


def fetch_day(day: date, retry_count: int, retry_delay: float) -> list[dict[str, Any]]:
    try:
        from forex_pytory.core.scraper import forex_factory_scraper
    except ImportError as exc:
        raise RuntimeError("Install requirements.txt before running this script") from exc

    last_error: Exception | None = None
    for attempt in range(retry_count + 1):
        try:
            url = forex_factory_scraper.get_url(
                day=day.day, month=day.month, year=day.year, timeline="day"
            )
            return [record_to_dict(item) for item in forex_factory_scraper.get_records(url)]
        except Exception as exc:  # Network and parser errors must be retried on a VPS.
            last_error = exc
            if attempt >= retry_count:
                break
            delay = retry_delay * (2**attempt)
            LOGGER.warning(
                "Fetch failed for %s (attempt %d/%d): %s; retrying in %.1fs",
                day,
                attempt + 1,
                retry_count + 1,
                exc,
                delay,
            )
            time.sleep(delay)
    raise RuntimeError(f"Could not fetch {day}") from last_error


def events_for_currencies(
    day: date, records: Iterable[dict[str, Any]], symbols: dict[str, tuple[str, str]]
) -> list[dict[str, Any]]:
    currencies = {currency for pair in symbols.values() for currency in pair}
    events: list[dict[str, Any]] = []
    for raw_record in records:
        currency = str(get_field(raw_record, "Currency") or "").upper()
        if currency not in currencies:
            continue
        normalized = normalize_event(day, raw_record)
        if normalized is not None:
            events.append(normalized)
    return events


def expected_days(start: date, end: date) -> set[str]:
    return {
        (start + timedelta(days=offset)).isoformat()
        for offset in range((end - start).days + 1)
    }


def completed_days(progress_path: Path) -> set[str]:
    if not progress_path.exists():
        return set()
    with progress_path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    return set(data.get("completed_days", []))


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary_path = Path(stream.name)
        json.dump(payload, stream, ensure_ascii=True, separators=(",", ":"), default=str)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary_path.replace(path)


def write_jsonl_file(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary_path = Path(stream.name)
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=True, separators=(",", ":"), default=str))
            stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary_path.replace(path)


def consolidate_to_parquet(staging_dir: Path, output_dir: Path) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Install pyarrow before consolidating Parquet files") from exc

    events_by_id: dict[str, dict[str, Any]] = {}
    for daily_path in sorted(staging_dir.glob("*.jsonl")):
        with daily_path.open(encoding="utf-8") as stream:
            for line in stream:
                event = json.loads(line)
                event["release_at"] = datetime.fromisoformat(event["release_at"])
                events_by_id[event["event_id"]] = event

    output_dir.mkdir(parents=True, exist_ok=True)
    rows = sorted(events_by_id.values(), key=lambda event: event["release_at"])
    schema = pa.schema([
        ("event_id", pa.string()),
        ("release_at", pa.timestamp("us", tz="UTC")),
        ("time_kind", pa.string()),
        ("currency", pa.string()),
        ("event_name", pa.string()),
        ("impact", pa.string()),
        ("actual", pa.float64()),
        ("forecast", pa.float64()),
        ("previous", pa.float64()),
        ("unit", pa.string()),
        ("actual_raw", pa.string()),
        ("forecast_raw", pa.string()),
        ("previous_raw", pa.string()),
        ("source", pa.string()),
    ])
    table = pa.Table.from_pylist(rows, schema=schema)
    target = output_dir / "calendar.parquet"
    with NamedTemporaryFile(suffix=".parquet", dir=output_dir, delete=False) as stream:
        temporary_path = Path(stream.name)
    pq.write_table(table, temporary_path, compression="zstd")
    temporary_path.replace(target)
    LOGGER.info("Wrote %s: %d events", target, len(rows))


def write_progress(path: Path, days: set[str], symbols: dict[str, tuple[str, str]]) -> None:
    payload = {"completed_days": sorted(days), "symbols": sorted(symbols)}
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary_path = Path(stream.name)
        json.dump(payload, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary_path.replace(path)


def main() -> int:
    args = parse_args()
    if args.start > args.end:
        raise SystemExit("--start must be on or before --end")
    if args.retry_count < 0 or args.retry_delay < 0 or args.request_delay < 0:
        raise SystemExit("retry and request delays must be non-negative")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    symbols = discover_symbols(args.parquet_dir)
    LOGGER.info("Discovered %d forex pairs: %s", len(symbols), ", ".join(symbols))
    if args.dry_run:
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = args.output_dir / "progress.json"
    staging_dir = args.output_dir / "staging"
    done = set() if args.force else completed_days(progress_path)
    processed = 0
    current = args.start

    while current <= args.end:
        day_key = current.isoformat()
        daily_path = staging_dir / f"{day_key}.jsonl"
        raw_path = args.output_dir / "raw" / f"{day_key}.json"
        if day_key in done and daily_path.exists() and not args.force:
            current += timedelta(days=1)
            continue
        if args.max_days is not None and processed >= args.max_days:
            break

        records = fetch_day(current, args.retry_count, args.retry_delay)
        events = events_for_currencies(current, records, symbols)
        write_json_file(raw_path, records)
        write_jsonl_file(daily_path, events)
        done.add(day_key)
        write_progress(progress_path, done, symbols)
        processed += 1
        LOGGER.info("Completed %s: %d source events, %d currency events", current, len(records), len(events))
        current += timedelta(days=1)
        if current <= args.end:
            time.sleep(args.request_delay)
    consolidate_to_parquet(staging_dir, args.output_dir)
    LOGGER.info("Finished: %d new days, output=%s", processed, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())