"""
File read/write skill — sandboxed to ~/agent-workspace/.
"""

import os
from pathlib import Path

from agent.skills import Skill, SkillResult

WORKSPACE_DIR = Path.home() / "agent-workspace"


def _ensure_workspace():
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_path(filename: str) -> Path:
    """Resolve filename within the sandbox, preventing path traversal."""
    resolved = (WORKSPACE_DIR / filename).resolve()
    if not str(resolved).startswith(str(WORKSPACE_DIR.resolve())):
        raise ValueError(f"Path traversal blocked: {filename}")
    return resolved


class FileReadSkill(Skill):

    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "Read the contents of a file from the agent workspace."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name or relative path of the file to read.",
                },
            },
            "required": ["filename"],
        }

    def execute(self, filename: str, **kwargs) -> SkillResult:
        _ensure_workspace()
        try:
            path = _safe_path(filename)
            if not path.exists():
                return SkillResult(
                    success=False,
                    output=f"File not found: {filename}",
                    error="File does not exist.",
                )
            content = path.read_text(encoding="utf-8", errors="replace")
            if len(content) > 10000:
                content = content[:10000] + "\n\n[... truncated at 10000 chars]"
            return SkillResult(
                success=True,
                output=content,
                data={"filename": filename, "size": path.stat().st_size},
            )
        except ValueError as e:
            return SkillResult(success=False, output=str(e), error=str(e))
        except Exception as e:
            return SkillResult(success=False, output=f"Read failed: {e}", error=str(e))


class FileWriteSkill(Skill):

    @property
    def name(self) -> str:
        return "file_write"

    @property
    def description(self) -> str:
        return "Write content to a file in the agent workspace."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name or relative path of the file to write.",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file.",
                },
                "append": {
                    "type": "string",
                    "description": "Set to 'true' to append instead of overwrite.",
                },
            },
            "required": ["filename", "content"],
        }

    def execute(self, filename: str, content: str, append: str = "false", **kwargs) -> SkillResult:
        _ensure_workspace()
        try:
            path = _safe_path(filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append.lower() == "true" else "w"
            path.write_text(content, encoding="utf-8") if mode == "w" else path.open("a").write(content)
            return SkillResult(
                success=True,
                output=f"Written {len(content)} chars to {filename}.",
                data={"filename": filename, "size": len(content), "mode": mode},
            )
        except ValueError as e:
            return SkillResult(success=False, output=str(e), error=str(e))
        except Exception as e:
            return SkillResult(success=False, output=f"Write failed: {e}", error=str(e))


class FileListSkill(Skill):

    @property
    def name(self) -> str:
        return "file_list"

    @property
    def description(self) -> str:
        return "List files in the agent workspace directory."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Subdirectory to list (default: root of workspace).",
                },
            },
            "required": [],
        }

    def execute(self, path: str = "", **kwargs) -> SkillResult:
        _ensure_workspace()
        try:
            target = _safe_path(path) if path else WORKSPACE_DIR
            if not target.is_dir():
                return SkillResult(
                    success=False,
                    output=f"Not a directory: {path}",
                    error="Path is not a directory.",
                )
            entries = []
            for item in sorted(target.iterdir()):
                rel = item.relative_to(WORKSPACE_DIR)
                if item.is_dir():
                    entries.append(f"📁 {rel}/")
                else:
                    size = item.stat().st_size
                    entries.append(f"📄 {rel} ({size} bytes)")
            if not entries:
                return SkillResult(success=True, output="Workspace is empty.")
            return SkillResult(
                success=True,
                output="\n".join(entries),
                data={"count": len(entries)},
            )
        except ValueError as e:
            return SkillResult(success=False, output=str(e), error=str(e))
        except Exception as e:
            return SkillResult(success=False, output=f"List failed: {e}", error=str(e))
