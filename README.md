# iCal Skill

Agent skill for creating RFC 5545-compliant `.ics` calendar files importable into Apple Calendar, Google Calendar, Outlook, and other calendar apps.

Designed to be used with AI coding agents (Claude Code, Cursor, etc.) as a [skill](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/tutorials#create-custom-slash-commands). The agent reads `ical/SKILL.md`, follows the instructions, and uses the included Python script to generate valid `.ics` files.

## What It Does

| Capability | Description |
|------------|-------------|
| **Single events** | Create timed or all-day events with timezone support |
| **Multiple events** | Batch export several events into a single `.ics` file |
| **Recurring events** | Create repeating events with RRULE patterns |
| **Reminders** | Add VALARM alerts with configurable trigger times |
| **Structured output** | Automatic UID generation, line folding, and text escaping |

## Requirements

- **Python 3.10+** (script uses only stdlib, no extra dependencies)

## Setup

Clone the repo and register `ical/SKILL.md` as a skill in your agent:

```bash
git clone git@github.com:barcia/ical-skill.git
```

The skill path to register is `ical/SKILL.md`.

## How It Works

The agent can either write `.ics` files directly (using the manual reference in SKILL.md) or use the generator script for batch/complex events:

```bash
python3 ical/scripts/generate_ics.py events.json -o calendar.ics
```

The script takes a JSON file with event data and produces a valid `.ics` file with proper UIDs, line folding, and text escaping.

### Example JSON input

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
      "description": "Weekly alignment meeting",
      "location": "Office Room 3B"
    },
    {
      "date": "2026-03-16",
      "summary": "Company holiday"
    }
  ]
}
```

## Project Structure

```
ical/
├── SKILL.md                    # Agent skill definition (entry point)
└── scripts/
    └── generate_ics.py         # JSON → .ics generator
```

## License

[GPL-3.0](LICENSE)
