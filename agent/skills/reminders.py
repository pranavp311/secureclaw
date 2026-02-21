"""
Reminder and music skills.
"""

from agent.skills import Skill, SkillResult


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
