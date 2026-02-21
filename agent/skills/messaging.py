"""
Messaging skill — send message to a contact.
"""

from agent.skills import Skill, SkillResult


class SendMessageSkill(Skill):

    @property
    def name(self) -> str:
        return "send_message"

    @property
    def description(self) -> str:
        return "Send a message to a contact."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "description": "Name of the person to send the message to.",
                },
                "message": {
                    "type": "string",
                    "description": "The message content to send.",
                },
            },
            "required": ["recipient", "message"],
        }

    def execute(self, recipient: str, message: str, **kwargs) -> SkillResult:
        return SkillResult(
            success=True,
            output=f"Message sent to {recipient}: \"{message}\"",
            data={"recipient": recipient, "message": message},
        )
