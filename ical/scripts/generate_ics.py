#!/usr/bin/env python3
"""Generate RFC 5545-compliant .ics files from JSON input."""

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower().strip())
    return re.sub(r"[\s_]+", "-", slug)[:40]


def generate_uid(summary: str, date: str) -> str:
    short_uuid = uuid.uuid4().hex[:8]
    slug = slugify(summary)
    return f"{slug}-{date}-{short_uuid}@claude"


def escape_text(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    text = text.replace("\n", "\\n")
    return text


def fold_line(line: str) -> str:
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line

    result = []
    current = b""
    for char in line:
        char_bytes = char.encode("utf-8")
        limit = 75 if not result else 74  # first line 75, continuation 74 (1 for leading space)
        if len(current) + len(char_bytes) > limit:
            result.append(current.decode("utf-8"))
            current = char_bytes
        else:
            current += char_bytes

    if current:
        result.append(current.decode("utf-8"))

    return "\r\n ".join(result)


def fold_content(content: str) -> str:
    lines = content.split("\r\n")
    return "\r\n".join(fold_line(line) for line in lines)


def format_date(date_str: str) -> str:
    return date_str.replace("-", "")


def format_datetime(date_str: str, time_str: str) -> str:
    return f"{date_str.replace('-', '')}T{time_str.replace(':', '')}00"


def build_vevent(event: dict, defaults: dict) -> str:
    date = event.get("date")
    summary = event.get("summary")
    if not date or not summary:
        raise ValueError(f"Event missing required fields (date, summary): {event}")

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise ValueError(f"Invalid date format '{date}', expected YYYY-MM-DD")

    time = event.get("time")
    if time and not re.match(r"^\d{2}:\d{2}$", time):
        raise ValueError(f"Invalid time format '{time}', expected HH:MM")

    tz = event.get("timezone", defaults.get("timezone"))
    reminder = event.get("reminder_minutes", defaults.get("reminder_minutes", 0))
    duration = event.get("duration_minutes", defaults.get("duration_minutes", 60))

    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    uid = generate_uid(summary, date)

    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
    ]

    is_allday = time is None
    if is_allday:
        dt_date = datetime.strptime(date, "%Y-%m-%d")
        next_day = (dt_date + timedelta(days=1)).strftime("%Y%m%d")
        lines.append(f"DTSTART;VALUE=DATE:{format_date(date)}")
        lines.append(f"DTEND;VALUE=DATE:{next_day}")
    else:
        if not tz:
            raise ValueError(
                f"Event '{summary}' has a time but no timezone. "
                "Set 'timezone' at root level or per event."
            )
        dt_str = format_datetime(date, time)
        lines.append(f"DTSTART;TZID={tz}:{dt_str}")
        if duration:
            hours, mins = divmod(duration, 60)
            dur_parts = "PT"
            if hours:
                dur_parts += f"{hours}H"
            if mins:
                dur_parts += f"{mins}M"
            if not hours and not mins:
                dur_parts += "0M"
            lines.append(f"DURATION:{dur_parts}")

    lines.append(f"SUMMARY:{escape_text(summary)}")

    description = event.get("description")
    if description:
        lines.append(f"DESCRIPTION:{escape_text(description)}")

    location = event.get("location")
    if location:
        lines.append(f"LOCATION:{escape_text(location)}")

    url = event.get("url")
    if url:
        lines.append(f"URL:{url}")

    categories = event.get("categories")
    if categories:
        lines.append(f"CATEGORIES:{','.join(categories)}")

    status = event.get("status")
    if status:
        if status not in ("TENTATIVE", "CONFIRMED", "CANCELLED"):
            raise ValueError(f"Invalid status '{status}', expected TENTATIVE/CONFIRMED/CANCELLED")
        lines.append(f"STATUS:{status}")

    transp = event.get("transp")
    if transp:
        if transp not in ("OPAQUE", "TRANSPARENT"):
            raise ValueError(f"Invalid transp '{transp}', expected OPAQUE/TRANSPARENT")
        lines.append(f"TRANSP:{transp}")

    rrule = event.get("rrule")
    if rrule:
        lines.append(f"RRULE:{rrule}")

    if reminder and reminder > 0:
        hours, mins = divmod(reminder, 60)
        trigger_parts = "-PT"
        if hours:
            trigger_parts += f"{hours}H"
        if mins:
            trigger_parts += f"{mins}M"
        if not hours and not mins:
            trigger_parts += "0M"
        lines.extend([
            "BEGIN:VALARM",
            f"TRIGGER:{trigger_parts}",
            "ACTION:DISPLAY",
            "DESCRIPTION:Reminder",
            "END:VALARM",
        ])

    lines.append("END:VEVENT")
    return "\r\n".join(lines)


def generate_ics(data: dict) -> str:
    events = data.get("events")
    if not events:
        raise ValueError("JSON must contain a non-empty 'events' array")

    defaults = {
        "timezone": data.get("timezone"),
        "reminder_minutes": data.get("reminder_minutes", 0),
        "duration_minutes": data.get("duration_minutes", 60),
    }

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Claude//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for event in events:
        lines.append(build_vevent(event, defaults))

    lines.append("END:VCALENDAR")

    content = "\r\n".join(lines)
    return fold_content(content)


def main():
    parser = argparse.ArgumentParser(description="Generate .ics files from JSON")
    parser.add_argument("input", nargs="?", help="JSON input file (default: stdin)")
    parser.add_argument("-o", "--output", required=True, help="Output .ics file path")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    try:
        ics_content = generate_ics(data)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.output, "w", newline="") as f:
        f.write(ics_content)

    event_count = len(data["events"])
    print(f"Generated {args.output} ({event_count} event{'s' if event_count != 1 else ''})")


if __name__ == "__main__":
    main()
