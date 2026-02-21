"""
Calendar manager skill — local JSON-backed calendar with add/list/delete.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from agent.skills import Skill, SkillResult

CALENDAR_FILE = Path.home() / "agent-workspace" / ".calendar.json"


def _load_events() -> list:
    if CALENDAR_FILE.exists():
        try:
            return json.loads(CALENDAR_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_events(events: list):
    CALENDAR_FILE.parent.mkdir(parents=True, exist_ok=True)
    CALENDAR_FILE.write_text(json.dumps(events, indent=2), encoding="utf-8")


class CalendarAddSkill(Skill):

    @property
    def name(self) -> str:
        return "calendar_add"

    @property
    def description(self) -> str:
        return "Add an event to the calendar with a title, date, and optional time and description."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Event title.",
                },
                "date": {
                    "type": "string",
                    "description": "Event date (e.g. '2026-02-21' or 'tomorrow').",
                },
                "time": {
                    "type": "string",
                    "description": "Event time (e.g. '3:00 PM'). Optional.",
                },
                "description": {
                    "type": "string",
                    "description": "Event description. Optional.",
                },
            },
            "required": ["title", "date"],
        }

    def execute(self, title: str, date: str, time: str = "", description: str = "", **kwargs) -> SkillResult:
        events = _load_events()
        event = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "date": date,
            "time": time,
            "description": description,
            "created_at": datetime.now().isoformat(),
        }
        events.append(event)
        _save_events(events)
        time_str = f" at {time}" if time else ""
        return SkillResult(
            success=True,
            output=f"Added event '{title}' on {date}{time_str}.",
            data=event,
        )


class CalendarListSkill(Skill):

    @property
    def name(self) -> str:
        return "calendar_list"

    @property
    def description(self) -> str:
        return "List upcoming calendar events, optionally filtered by date."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Filter events by date (e.g. '2026-02-21'). Optional — lists all if omitted.",
                },
            },
            "required": [],
        }

    def execute(self, date: str = "", **kwargs) -> SkillResult:
        events = _load_events()
        if not events:
            return SkillResult(success=True, output="No events on the calendar.")

        if date:
            events = [e for e in events if e.get("date", "") == date]
            if not events:
                return SkillResult(success=True, output=f"No events on {date}.")

        lines = []
        for e in events:
            time_str = f" at {e['time']}" if e.get("time") else ""
            desc_str = f" — {e['description']}" if e.get("description") else ""
            lines.append(f"• [{e['id']}] {e['title']} on {e['date']}{time_str}{desc_str}")

        return SkillResult(
            success=True,
            output="\n".join(lines),
            data={"count": len(events)},
        )


class CalendarDeleteSkill(Skill):

    @property
    def name(self) -> str:
        return "calendar_delete"

    @property
    def description(self) -> str:
        return "Delete a calendar event by its ID."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "The ID of the event to delete.",
                },
            },
            "required": ["event_id"],
        }

    def execute(self, event_id: str, **kwargs) -> SkillResult:
        events = _load_events()
        original_count = len(events)
        events = [e for e in events if e.get("id") != event_id]

        if len(events) == original_count:
            return SkillResult(
                success=False,
                output=f"Event '{event_id}' not found.",
                error="Event not found.",
            )

        _save_events(events)
        return SkillResult(
            success=True,
            output=f"Deleted event '{event_id}'.",
            data={"deleted_id": event_id},
        )
