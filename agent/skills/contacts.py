"""
Contact search skill.
"""

from agent.skills import Skill, SkillResult


class SearchContactsSkill(Skill):

    @property
    def name(self) -> str:
        return "search_contacts"

    @property
    def description(self) -> str:
        return "Search for a contact by name."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Name to search for."},
            },
            "required": ["query"],
        }

    def execute(self, query: str, **kwargs) -> SkillResult:
        return SkillResult(
            success=True,
            output=f"Found contact: {query}",
            data={"query": query},
        )
