#!/usr/bin/env python3
"""Repair ``calendar.parquet`` when the exporter assumed the wrong page timezone.

``download_fundamentals.py`` reads the clock text of each ForexFactory row and
converts it as ``America/New_York``. ForexFactory, however, renders the calendar
in the timezone it picks for the visitor, which is not always New York: a run
from a European host is served Central European Time. When that happens every
``scheduled`` release is stored 5-7 hours late (6 hours most of the year, 5 or 7
inside the windows where the US and the EU switch DST on different dates).

The conversion is reversible, so the file can be repaired without scraping
again:

1. Read ``release_at`` back in the timezone the exporter *assumed*
   (``--assumed-tz``). That recovers the exact wall clock the page showed.
2. Re-attach that wall clock to the timezone the page *actually* used
   (``--actual-tz``) and convert to UTC.

``all_day`` and ``tentative`` rows are left untouched: the exporter puts them at
a plain UTC day boundary without any timezone conversion, so they were never
affected. ``event_id`` is recomputed with the exporter's own formula because it
hashes ``release_at``; ``source_event_id`` is the stable key and never changes.

Examples
--------
    python scripts/repair_calendar_timezone.py --dry-run \\
        --input ../backend/data/fundamentals/calendar.parquet

    python scripts/repair_calendar_timezone.py \\
        --input ../backend/data/fundamentals/calendar.parquet
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import shutil
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

LOGGER = logging.getLogger("repair_calendar_timezone")

# Rows whose timestamp came from a wall-clock conversion. Everything else was
# written as a plain UTC day boundary and must be preserved as is.
CONVERTED_TIME_KINDS = frozenset({"scheduled"})

# Anchor used to tell a correct file from a shifted one. US Non-Farm Payrolls
# have been released at 08:30 America/New_York for decades, DST included.
ANCHOR_EVENT_NAME = "Non-Farm Employment Change"
ANCHOR_TZ = "America/New_York"
ANCHOR_WALL_CLOCK = (8, 30)
# A handful of rows may legitimately miss the anchor (reschedules, bad source
# rows). Require a large majority rather than unanimity.
ANCHOR_MIN_RATIO = 0.9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re-interpret calendar.parquet timestamps under the right page timezone."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to calendar.parquet.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Destination (default: overwrite --input, keeping a .bak copy).",
    )
    parser.add_argument(
        "--assumed-tz",
        default="America/New_York",
        help="Timezone the exporter assumed when it wrote the file.",
    )
    parser.add_argument(
        "--actual-tz",
        default="Europe/Madrid",
        help="Timezone ForexFactory actually rendered (any CET zone works).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing anything.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Repair even when the anchor check says the file is already correct.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not keep a .bak copy when overwriting in place.",
    )
    return parser.parse_args()


def load_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:  # pragma: no cover - environment issue
        raise SystemExit(f"Unknown timezone: {name}") from exc


def recompute_event_id(release_at: datetime, currency: str, event_name: str) -> str:
    """Same formula as ``download_fundamentals.normalize_event``."""
    return hashlib.sha256(
        f"{release_at.isoformat()}|{currency}|{event_name}".encode("utf-8")
    ).hexdigest()


def reinterpret(
    release_at: datetime, assumed: ZoneInfo, actual: ZoneInfo
) -> tuple[datetime, bool]:
    """Move a timestamp from the assumed timezone to the actual one.

    Returns the corrected UTC timestamp and whether the recovered wall clock
    round-trips cleanly in ``actual``. It does not on the two DST edges, where a
    local time either does not exist or happens twice; the caller reports those.
    """
    wall_clock = release_at.astimezone(assumed).replace(tzinfo=None)
    localised = wall_clock.replace(tzinfo=actual)
    corrected = localised.astimezone(timezone.utc)
    round_trips = corrected.astimezone(actual).replace(tzinfo=None) == wall_clock
    return corrected, round_trips


def anchor_wall_clocks(
    table, assumed_or_target: ZoneInfo
) -> list[tuple[int, int]]:
    """Wall clock of every anchor row, expressed in ``assumed_or_target``."""
    names = table.column("event_name").to_pylist()
    kinds = table.column("time_kind").to_pylist()
    stamps = table.column("release_at").to_pylist()
    out: list[tuple[int, int]] = []
    for name, kind, stamp in zip(names, kinds, stamps):
        if name != ANCHOR_EVENT_NAME or kind not in CONVERTED_TIME_KINDS:
            continue
        if stamp is None:
            continue
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        local = stamp.astimezone(assumed_or_target)
        out.append((local.hour, local.minute))
    return out


def anchor_ratio(wall_clocks: list[tuple[int, int]]) -> float:
    if not wall_clocks:
        return 0.0
    hits = sum(1 for value in wall_clocks if value == ANCHOR_WALL_CLOCK)
    return hits / len(wall_clocks)


def describe_anchor(label: str, wall_clocks: list[tuple[int, int]]) -> None:
    if not wall_clocks:
        LOGGER.warning("%s: no anchor rows (%s) found", label, ANCHOR_EVENT_NAME)
        return
    common = Counter(f"{h:02d}:{m:02d}" for h, m in wall_clocks).most_common(3)
    LOGGER.info(
        "%s: %d anchor rows, %.1f%% at %02d:%02d %s (top: %s)",
        label,
        len(wall_clocks),
        anchor_ratio(wall_clocks) * 100,
        ANCHOR_WALL_CLOCK[0],
        ANCHOR_WALL_CLOCK[1],
        ANCHOR_TZ,
        ", ".join(f"{clock} x{count}" for clock, count in common),
    )


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stdout
    )

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - dependency issue
        raise SystemExit("Install pyarrow before running this script") from exc

    if not args.input.is_file():
        raise SystemExit(f"Input not found: {args.input}")

    assumed = load_zone(args.assumed_tz)
    actual = load_zone(args.actual_tz)
    anchor_zone = load_zone(ANCHOR_TZ)

    table = pq.read_table(args.input)
    required = {"release_at", "time_kind", "currency", "event_name", "event_id"}
    missing = required - set(table.column_names)
    if missing:
        raise SystemExit(f"Missing columns in {args.input}: {sorted(missing)}")

    LOGGER.info("Read %s: %d rows", args.input, table.num_rows)
    before = anchor_wall_clocks(table, anchor_zone)
    describe_anchor("before", before)

    if anchor_ratio(before) >= ANCHOR_MIN_RATIO and not args.force:
        LOGGER.info(
            "The anchor already lands at %02d:%02d %s; nothing to repair. "
            "Use --force to convert anyway.",
            ANCHOR_WALL_CLOCK[0],
            ANCHOR_WALL_CLOCK[1],
            ANCHOR_TZ,
        )
        return 0

    stamps = table.column("release_at").to_pylist()
    kinds = table.column("time_kind").to_pylist()
    currencies = table.column("currency").to_pylist()
    names = table.column("event_name").to_pylist()
    event_ids = table.column("event_id").to_pylist()

    new_stamps: list[datetime | None] = []
    new_event_ids: list[str | None] = []
    shifts: Counter[str] = Counter()
    converted = 0
    skipped = 0
    ambiguous: list[str] = []

    for stamp, kind, currency, name, event_id in zip(
        stamps, kinds, currencies, names, event_ids
    ):
        if stamp is None or kind not in CONVERTED_TIME_KINDS:
            new_stamps.append(stamp)
            new_event_ids.append(event_id)
            skipped += 1
            continue
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        corrected, round_trips = reinterpret(stamp, assumed, actual)
        if not round_trips:
            ambiguous.append(f"{stamp.isoformat()} {currency} {name}")
        delta = corrected - stamp
        shifts[f"{delta // timedelta(hours=1)}h"] += 1
        new_stamps.append(corrected)
        new_event_ids.append(recompute_event_id(corrected, currency or "", name or ""))
        converted += 1

    LOGGER.info(
        "Converted %d rows (%s), left %d untouched (%s)",
        converted,
        ", ".join(f"{count} by {shift}" for shift, count in sorted(shifts.items())),
        skipped,
        "/".join(sorted(set(kinds) - CONVERTED_TIME_KINDS)) or "none",
    )
    if ambiguous:
        LOGGER.warning(
            "%d rows fell on a DST edge in %s and were resolved with the "
            "standard rule; first: %s",
            len(ambiguous),
            args.actual_tz,
            ambiguous[0],
        )

    repaired = table.set_column(
        table.column_names.index("release_at"),
        "release_at",
        pa.array(new_stamps, type=table.schema.field("release_at").type),
    ).set_column(
        table.column_names.index("event_id"),
        "event_id",
        pa.array(new_event_ids, type=table.schema.field("event_id").type),
    )
    metadata = dict(repaired.schema.metadata or {})
    metadata[b"page_tz"] = args.actual_tz.encode("utf-8")
    repaired = repaired.replace_schema_metadata(metadata)

    after = anchor_wall_clocks(repaired, anchor_zone)
    describe_anchor("after", after)
    if anchor_ratio(after) < ANCHOR_MIN_RATIO and not args.force:
        raise SystemExit(
            f"Refusing to write: after the repair only {anchor_ratio(after):.1%} of "
            f"the anchor rows land at {ANCHOR_WALL_CLOCK[0]:02d}:"
            f"{ANCHOR_WALL_CLOCK[1]:02d} {ANCHOR_TZ}. Check --actual-tz."
        )

    if args.dry_run:
        LOGGER.info("Dry run: nothing written.")
        return 0

    target = args.output or args.input
    if target == args.input and not args.no_backup:
        backup = args.input.with_suffix(args.input.suffix + ".bak")
        if backup.exists() and not args.force:
            raise SystemExit(f"Backup already exists: {backup}. Use --force to replace it.")
        shutil.copy2(args.input, backup)
        LOGGER.info("Backup written to %s", backup)

    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(suffix=".parquet", dir=target.parent, delete=False) as stream:
        temporary_path = Path(stream.name)
    try:
        pq.write_table(repaired, temporary_path, compression="zstd")
        os.replace(temporary_path, target)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    LOGGER.info("Wrote %s: %d rows", target, repaired.num_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
