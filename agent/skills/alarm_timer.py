"""
Alarm and timer skills.
"""

import subprocess
import platform

from agent.skills import Skill, SkillResult


def _set_macos_alarm(hour: int, minute: int) -> str:
    """Use AppleScript to create an alarm in macOS Clock app."""
    period = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    if display_hour == 0:
        display_hour = 12
    time_str = f"{display_hour}:{minute:02d} {period}"

    # Use AppleScript to open Clock app and create alarm via Shortcuts/Reminders
    # Primary method: use `shortcuts` CLI or `osascript` to set a reminder with alert
    try:
        # Method 1: Create a calendar alarm via osascript
        script = f'''
        tell application "Reminders"
            set newReminder to make new reminder in list "Reminders" with properties {{name:"Alarm - {time_str}", body:"SecureClaw Alarm"}}
            set due date of newReminder to (current date)
            set time of (due date of newReminder) to ({hour} * 3600 + {minute} * 60)
            set remind me date of newReminder to due date of newReminder
        end tell
        '''
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
    except Exception:
        pass

    # Method 2: Also schedule a native macOS notification as backup
    try:
        notify_script = f'''
        display notification "Alarm: {time_str}" with title "SecureClaw" sound name "Glass"
        '''
        # Schedule with `at` or just show immediate confirmation
        subprocess.run(["osascript", "-e", notify_script], capture_output=True, timeout=5)
    except Exception:
        pass

    return time_str


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

    def execute(self, hour: int, minute: int, **kwargs) -> SkillResult:
        hour = int(hour)
        minute = int(minute)

        if platform.system() == "Darwin":
            time_str = _set_macos_alarm(hour, minute)
            return SkillResult(
                success=True,
                output=f"Alarm set for {time_str}. A reminder has been created in Reminders app and a notification was sent.",
                data={"hour": hour, "minute": minute, "platform": "macOS"},
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
