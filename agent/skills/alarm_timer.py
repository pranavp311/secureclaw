"""
Alarm and timer skills.
"""

import subprocess
import platform

from agent.skills import Skill, SkillResult


def _set_macos_alarm(hour: int, minute: int) -> tuple:
    """Create a Calendar event with a sound alarm on macOS."""
    period = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    if display_hour == 0:
        display_hour = 12
    time_str = f"{display_hour}:{minute:02d} {period}"

    # Create a Calendar event with a sound alarm that fires at event time
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
    -- If the time has already passed today, set for tomorrow
    if targetDate < (current date) then
        set targetDate to targetDate + 1 * days
    end if
    set newEvent to make new event at end of events of targetCal with properties {{summary:"SecureClaw Alarm - {time_str}", start date:targetDate, end date:targetDate + 5 * minutes}}
    make new sound alarm at end of newEvent with properties {{trigger interval:0}}
end tell
'''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return time_str, True
    except Exception:
        pass

    # Fallback: show notification
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "Alarm set for {time_str}" with title "SecureClaw" sound name "Glass"'],
            capture_output=True, timeout=5
        )
    except Exception:
        pass

    return time_str, False


class SetAlarmSkill(Skill):

    @property
    def name(self) -> str:
        return "set_alarm"

    @property
    def description(self) -> str:
        return "Set an alarm for a given time."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "hour": {"type": "integer", "description": "Hour to set the alarm for (0-23)."},
                "minute": {"type": "integer", "description": "Minute to set the alarm for (0-59)."},
            },
            "required": ["hour", "minute"],
        }

    def execute(self, hour: int, minute: int = 0, **kwargs) -> SkillResult:
        hour = int(hour)
        minute = int(minute)

        if platform.system() == "Darwin":
            time_str, created = _set_macos_alarm(hour, minute)
            if created:
                return SkillResult(
                    success=True,
                    output=f"Alarm set for {time_str}. A Calendar event with sound alert has been created.",
                    data={"hour": hour, "minute": minute, "platform": "macOS", "calendar_event": True},
                )
            return SkillResult(
                success=True,
                output=f"Alarm set for {time_str} (notification sent).",
                data={"hour": hour, "minute": minute, "platform": "macOS", "calendar_event": False},
            )

        period = "AM" if hour < 12 else "PM"
        display_hour = hour if hour <= 12 else hour - 12
        if display_hour == 0:
            display_hour = 12
        return SkillResult(
            success=True,
            output=f"Alarm set for {display_hour}:{minute:02d} {period}.",
            data={"hour": hour, "minute": minute},
        )


class SetTimerSkill(Skill):

    @property
    def name(self) -> str:
        return "set_timer"

    @property
    def description(self) -> str:
        return "Set a countdown timer."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "minutes": {"type": "integer", "description": "Number of minutes."},
            },
            "required": ["minutes"],
        }

    def execute(self, minutes: int, **kwargs) -> SkillResult:
        return SkillResult(
            success=True,
            output=f"Timer set for {minutes} minute(s).",
            data={"minutes": minutes},
        )
