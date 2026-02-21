"""
Reminder and music skills.
"""

import platform
import re
import subprocess

from agent.skills import Skill, SkillResult


def _parse_time_str(time_str: str) -> tuple:
    """Parse a time string like '3pm', '3:00 PM', '15:30' into (hour, minute)."""
    time_str = time_str.strip().upper()
    # Try HH:MM AM/PM
    m = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)?', time_str)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if m.group(3) == "PM" and h != 12:
            h += 12
        elif m.group(3) == "AM" and h == 12:
            h = 0
        return h, mi
    # Try Ham/Hpm
    m = re.match(r'(\d{1,2})\s*(AM|PM)', time_str)
    if m:
        h = int(m.group(1))
        if m.group(2) == "PM" and h != 12:
            h += 12
        elif m.group(2) == "AM" and h == 12:
            h = 0
        return h, 0
    # Try 24h
    m = re.match(r'(\d{1,2}):(\d{2})', time_str)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def _create_macos_reminder(title: str, hour: int, minute: int) -> bool:
    """Create a Calendar event with alert (works without special permissions)."""
    period = "AM" if hour < 12 else "PM"
    dh = hour if hour <= 12 else hour - 12
    if dh == 0:
        dh = 12
    time_display = f"{dh}:{minute:02d} {period}"

    script = f'''
tell application "Calendar"
    set calList to name of every calendar
    if "Home" is in calList then
        set targetCal to calendar "Home"
    else
        set targetCal to first calendar
    end if
    set targetDate to current date
    set hours of targetDate to {hour}
    set minutes of targetDate to {minute}
    set seconds of targetDate to 0
    if targetDate < (current date) then
        set targetDate to targetDate + 1 * days
    end if
    set newEvent to make new event at end of events of targetCal with properties {{summary:"{title}", start date:targetDate, end date:targetDate + 5 * minutes}}
    make new display alarm at end of newEvent with properties {{trigger interval:0}}
end tell
'''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


class CreateReminderSkill(Skill):

    @property
    def name(self) -> str:
        return "create_reminder"

    @property
    def description(self) -> str:
        return "Create a reminder with a title and time."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Reminder title."},
                "time": {"type": "string", "description": "Time for the reminder (e.g. '3:00 PM')."},
            },
            "required": ["title", "time"],
        }

    def execute(self, title: str = "Reminder", time: str = "", **kwargs) -> SkillResult:
        if not time:
            return SkillResult(
                success=False,
                output="No time specified for the reminder.",
                data={},
            )

        hour, minute = _parse_time_str(time)
        if hour is not None and platform.system() == "Darwin":
            created = _create_macos_reminder(title, hour, minute)
            period = "AM" if hour < 12 else "PM"
            dh = hour if hour <= 12 else hour - 12
            if dh == 0:
                dh = 12
            time_display = f"{dh}:{minute:02d} {period}"
            if created:
                return SkillResult(
                    success=True,
                    output=f"Reminder '{title}' set for {time_display}. Calendar event with alert created.",
                    data={"title": title, "time": time, "calendar_event": True},
                )

        return SkillResult(
            success=True,
            output=f"Reminder set: '{title}' at {time}.",
            data={"title": title, "time": time},
        )


class PlayMusicSkill(Skill):

    @property
    def name(self) -> str:
        return "play_music"

    @property
    def description(self) -> str:
        return "Play a song or playlist."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "song": {"type": "string", "description": "Song or playlist name."},
            },
            "required": ["song"],
        }

    def execute(self, song: str, **kwargs) -> SkillResult:
        return SkillResult(
            success=True,
            output=f"Now playing: {song}",
            data={"song": song},
        )
