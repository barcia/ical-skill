---
name: ical
description: >-
  Create .ics (iCalendar) files for importing events into Apple Calendar,
  Google Calendar, Outlook, and other calendar apps. Use when asked to "create
  calendar event", "add to calendar", "export to ics", "generate ical",
  "schedule", "reminder", "recurring event", "training schedule", "weekly plan",
  "meeting invite", or when creating any events that need calendar import.
  Supports single events, batch/multi-event exports, recurring patterns,
  reminders/alarms, and timezone handling.
metadata:
  author: ivan
  version: 1.0.0
---

# iCal Event Creator

Generate RFC 5545-compliant `.ics` files. Two methods available:

1. **Script** (`scripts/generate_ics.py`) — Preferred for multiple events or long descriptions. Handles UID generation, line folding, and text escaping automatically.
2. **Manual** — Write `.ics` directly using the reference sections below.

## Generator Script

Run `scripts/generate_ics.py` with JSON input:

```bash
python3 scripts/generate_ics.py events.json -o calendar.ics
```

JSON schema:

```json
{
  "timezone": "Europe/Madrid",
  "reminder_minutes": 30,
  "events": [
    {
      "date": "2026-03-15",
      "time": "10:00",
      "duration_minutes": 90,
      "summary": "Team sync",
      "description": "Agenda:\n1. Review\n2. Planning",
      "location": "Office Room 3B",
      "url": "https://meet.google.com/abc",
      "categories": ["Work", "Meetings"],
      "status": "CONFIRMED",
      "transp": "OPAQUE",
      "rrule": "FREQ=WEEKLY;COUNT=12;BYDAY=MO"
    }
  ]
}
```

**Root fields** (global defaults, overrideable per event):
- `timezone` — IANA zone (required for timed events)
- `reminder_minutes` — 0 to skip VALARM (default: 0)
- `duration_minutes` — default duration (default: 60)

**Per event:**
- Required: `date` (YYYY-MM-DD), `summary`
- Optional: `time` (HH:MM — omit for all-day), `duration_minutes`, `description`, `location`, `url`, `categories`, `status`, `transp`, `rrule`, `reminder_minutes`

The script generates unique UIDs, applies line folding (75 octets), escapes text, and validates input.

---

## Manual Reference

### Single Event Template

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Claude//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:a1b2c3d4-e5f6-7890-abcd-ef1234567890@claude
DTSTAMP:20260217T100000Z
DTSTART;TZID=Europe/Madrid:20260218T180000
DTEND;TZID=Europe/Madrid:20260218T190000
SUMMARY:Event Title
DESCRIPTION:Event details
BEGIN:VALARM
TRIGGER:-PT30M
ACTION:DISPLAY
DESCRIPTION:Reminder
END:VALARM
END:VEVENT
END:VCALENDAR
```

## Required Fields

**VCALENDAR:** `VERSION:2.0`, `PRODID:-//Claude//EN`, `CALSCALE:GREGORIAN`, `METHOD:PUBLISH`

**VEVENT:** `UID`, `DTSTAMP` (UTC with Z), `DTSTART`, `DTEND` or `DURATION`, `SUMMARY`

## Date-Time Formats

| Format | Example | Use |
|--------|---------|-----|
| Timezone | `DTSTART;TZID=Europe/Madrid:20260218T180000` | Preferred for timed events |
| UTC | `DTSTART:20260218T170000Z` | Only for DTSTAMP |
| All-day | `DTSTART;VALUE=DATE:20260218` | Full-day events |
| Floating | `DTSTART:20260218T180000` | Avoid — ambiguous across apps |

Always use `TZID=` for timed events. Common zones: `Europe/Madrid`, `Europe/London`, `America/New_York`, `America/Los_Angeles`, `Asia/Tokyo`.

For all-day events, set DTEND to the *next* day: a single-day event on Feb 18 → `DTEND;VALUE=DATE:20260219`.

## DURATION (alternative to DTEND)

Use `DURATION` instead of `DTEND` when the length is known:

- `DURATION:PT45M` — 45 minutes
- `DURATION:PT1H` — 1 hour
- `DURATION:PT1H30M` — 1 hour 30 minutes
- `DURATION:P1D` — All day

Do not combine DTEND and DURATION — use one or the other.

## UID Generation

Format: `{descriptive-slug}-{date}@claude` — each UID must be unique within the file.

- Single event: `meeting-kickoff-20260218@claude`
- Batch export: `training-20260218@coach`, `training-20260219@coach`, ...

## Multiple Events

One VCALENDAR wrapping all VEVENT blocks. Never create separate VCALENDAR blocks.

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Claude//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:training-20260218@coach
DTSTAMP:20260217T100000Z
DTSTART;TZID=Europe/Madrid:20260218T070000
DURATION:PT1H
SUMMARY:Easy run 8km
END:VEVENT
BEGIN:VEVENT
UID:training-20260219@coach
DTSTAMP:20260217T100000Z
DTSTART;TZID=Europe/Madrid:20260219T180000
DURATION:PT1H15M
SUMMARY:Intervals 6x1000m
END:VEVENT
END:VCALENDAR
```

## Reminders (VALARM)

Place inside VEVENT, before `END:VEVENT`:

```
BEGIN:VALARM
TRIGGER:-PT30M
ACTION:DISPLAY
DESCRIPTION:Reminder
END:VALARM
```

Common triggers: `-PT15M`, `-PT30M`, `-PT1H`, `-PT2H`, `-P1D`.

## Recurring Events (RRULE)

Add RRULE property inside VEVENT. Always bound with `COUNT` or `UNTIL`.

| Pattern | RRULE |
|---------|-------|
| Weekly on Mon, Wed, Fri (8 weeks) | `RRULE:FREQ=WEEKLY;COUNT=24;BYDAY=MO,WE,FR` |
| Every 2 weeks on Saturday | `RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=SA` |
| Weekly until a date | `RRULE:FREQ=WEEKLY;UNTIL=20260401T235959Z;BYDAY=TU,TH` |
| Monthly first Saturday | `RRULE:FREQ=MONTHLY;BYDAY=1SA` |
| Daily for 7 days | `RRULE:FREQ=DAILY;COUNT=7` |

Exclude specific dates with `EXDATE`: `EXDATE;TZID=Europe/Madrid:20260225T180000`

Note: RRULE creates identical events. For varied schedules (different workouts each day), use separate VEVENTs instead.

## Optional Fields

| Property | Example | Purpose |
|----------|---------|---------|
| `DESCRIPTION` | `DESCRIPTION:Warm up 10min\nMain set...` | Event details (multi-line) |
| `LOCATION` | `LOCATION:Retiro Park` | Place or address |
| `URL` | `URL:https://meet.google.com/abc` | Meeting link |
| `CATEGORIES` | `CATEGORIES:Training,Running` | Tags (comma-separated) |
| `STATUS` | `STATUS:TENTATIVE` | `TENTATIVE` / `CONFIRMED` / `CANCELLED` |
| `TRANSP` | `TRANSP:TRANSPARENT` | Show as free (default: `OPAQUE` = busy) |
| `SEQUENCE` | `SEQUENCE:1` | Increment when updating existing event |

## Text Escaping

In property values: `\n` for newlines, `\,` for commas, `\;` for semicolons, `\\` for backslash.

## Line Folding

Lines MUST NOT exceed 75 octets. Fold by breaking and starting the next line with a single space:

```
DESCRIPTION:This is a long description that needs folding because it exc
 eeds the seventy-five octet limit per line defined in RFC 5545
```

The leading space on continuation lines is a fold marker, not part of the value. Apply to any long property.

## Filename

Use descriptive kebab-case: `training-week-2026-02-18.ics`, `meeting-kickoff.ics`, `birthday-maria.ics`
