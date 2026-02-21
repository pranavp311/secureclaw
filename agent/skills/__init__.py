"""
Skill registry — auto-discovers and registers all skills as tool definitions
compatible with generate_hybrid.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SkillResult:
    success: bool
    output: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Skill(ABC):
    """Base class for all agent skills."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema for parameters."""
        ...

    @abstractmethod
    def execute(self, **kwargs) -> SkillResult:
        ...

    def to_tool_definition(self) -> dict:
        """Convert skill to a tool definition for generate_hybrid."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class SkillRegistry:
    """Central registry for all available skills."""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill):
        self._skills[skill.name] = skill

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    def get_tool_definitions(self) -> List[dict]:
        return [s.to_tool_definition() for s in self._skills.values()]

    def execute(self, name: str, arguments: dict) -> SkillResult:
        skill = self._skills.get(name)
        if skill is None:
            return SkillResult(
                success=False,
                output=f"Unknown skill: {name}",
                error=f"Skill '{name}' not found in registry.",
            )
        try:
            return skill.execute(**arguments)
        except Exception as e:
            return SkillResult(
                success=False,
                output=f"Skill '{name}' failed: {e}",
                error=str(e),
            )


# Global registry instance
registry = SkillRegistry()


def get_registry() -> SkillRegistry:
    return registry
