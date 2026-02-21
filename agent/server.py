"""
FastAPI Gateway — single backend serving Web UI, Telegram bot, and mobile app.

Endpoints:
  POST /api/chat        — main chat (privacy → routing → skill execution)
  GET  /api/skills      — list available skills
  POST /api/privacy     — standalone privacy check
  WS   /ws              — WebSocket for real-time chat
  GET  /                — serves React frontend
"""

import asyncio
import json
import os
import re
import sys
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure cactus is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "cactus" / "python" / "src"))
os.environ.setdefault("CACTUS_NO_CLOUD_TELE", "1")

from agent.privacy import PrivacyResult, RiskLevel, scan_privacy, redact_pii
from agent.skills import SkillRegistry, SkillResult, get_registry

# Import all skills and register them
from agent.skills.browse import BrowseSkill
from agent.skills.files import FileReadSkill, FileWriteSkill, FileListSkill
from agent.skills.calendar_mgr import CalendarAddSkill, CalendarListSkill, CalendarDeleteSkill
from agent.skills.weather import WeatherSkill
from agent.skills.messaging import SendMessageSkill
from agent.skills.alarm_timer import SetAlarmSkill, SetTimerSkill
from agent.skills.contacts import SearchContactsSkill
from agent.skills.reminders import CreateReminderSkill, PlayMusicSkill


def _register_all_skills():
    reg = get_registry()
    for skill_cls in [
        BrowseSkill, FileReadSkill, FileWriteSkill, FileListSkill,
        CalendarAddSkill, CalendarListSkill, CalendarDeleteSkill,
        WeatherSkill, SendMessageSkill, SetAlarmSkill, SetTimerSkill,
        SearchContactsSkill, CreateReminderSkill, PlayMusicSkill,
    ]:
        reg.register(skill_cls())


# ---------------------------------------------------------------------------
# Lazy-load the hybrid router (heavy — loads FunctionGemma model)
# The Cactus C library is NOT thread-safe. We must serialize all inference
# calls with a lock to prevent concurrent cactus_reset / cactus_complete.
# ---------------------------------------------------------------------------
_hybrid_router = None
_model_lock = threading.Lock()


def _get_hybrid_router():
    global _hybrid_router
    if _hybrid_router is None:
        # Import from project root main.py
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from main import generate_hybrid
        _hybrid_router = generate_hybrid
    return _hybrid_router


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class RoutingOverride(str, Enum):
    auto = "auto"
    local = "local"
    cloud = "cloud"


class ChatRequest(BaseModel):
    message: str
    routing_override: RoutingOverride = RoutingOverride.auto
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    function_calls: list
    skill_results: list
    privacy: dict
    routing: dict
    total_time_ms: float


class PrivacyCheckRequest(BaseModel):
    text: str


class SkillInfo(BaseModel):
    name: str
    description: str
    parameters: dict


# ---------------------------------------------------------------------------
# Core chat logic (shared by REST, WebSocket, and Telegram)
# ---------------------------------------------------------------------------

def process_chat(
    user_message: str,
    routing_override: str = "auto",
    conversation_history: Optional[list] = None,
) -> dict:
    """
    Full pipeline: privacy check → routing → inference → skill execution.
    Returns a dict suitable for ChatResponse.
    """
    start = time.time()
    registry = get_registry()

    # Phase 0: Privacy scan
    privacy_result = scan_privacy(user_message)

    # Determine effective routing
    effective_override = routing_override
    if privacy_result.risk_level == RiskLevel.HIGH and routing_override == "auto":
        effective_override = "local"
    elif privacy_result.risk_level == RiskLevel.MEDIUM and routing_override == "auto":
        effective_override = "local"

    # Build messages — only pass current user message to the hybrid router.
    # Conversation history confuses generate_cloud which sends ALL user
    # messages to Gemini, causing wrong tool selection.
    messages = [{"role": "user", "content": user_message}]

    # Get tool definitions from skill registry — filter to only the core
    # function-calling tools that generate_hybrid was designed for.
    # The new skills (web_browse, file_*, calendar_*) are executed as a
    # second pass after the model picks a tool.
    CORE_TOOLS = {
        "get_weather", "set_alarm", "send_message", "create_reminder",
        "search_contacts", "play_music", "set_timer",
    }
    all_tools = registry.get_tool_definitions()
    tools = [t for t in all_tools if t["name"] in CORE_TOOLS]

    # Run inference — acquire lock to serialize Cactus model access
    generate_hybrid = _get_hybrid_router()

    with _model_lock:
        if effective_override == "local":
            # Fast path: skip SmartRouter pre-inference (embeddings, similarity)
            # and call FunctionGemma directly. ~3x faster for privacy-forced queries.
            # Extract just the action clause — FunctionGemma 270M can't parse
            # long multi-clause PII sentences reliably.
            # Split on comma/period/semicolon and find the clause with action words.
            _ACTION_WORDS = {"set", "get", "send", "play", "search", "create",
                             "remind", "what", "weather", "alarm", "timer",
                             "message", "find", "call", "music"}
            clauses = re.split(r'[,;.]\s*', user_message)
            action_clauses = [c for c in clauses
                              if any(w in c.lower().split() for w in _ACTION_WORDS)]
            clean_msg = action_clauses[0] if action_clauses else user_message
            clean_messages = [{"role": "user", "content": clean_msg.strip()}]
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from main import generate_cactus
            local_result = generate_cactus(clean_messages, tools)
            # If empty, retry with original message
            if not local_result.get("function_calls"):
                local_result = generate_cactus(messages, tools)
            result = {
                "function_calls": local_result.get("function_calls", []),
                "total_time_ms": local_result.get("total_time_ms", 0),
                "confidence": local_result.get("confidence", 0),
                "source": "on-device (privacy-forced)",
            }
        elif effective_override == "cloud":
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from main import generate_cloud
            result = generate_cloud(messages, tools)
            result["source"] = "cloud (user-forced)"
        else:
            result = generate_hybrid(messages, tools)

    # Post-process: remap set_alarm → create_reminder when query is about
    # calendar events, reminders, or tasks (FunctionGemma often confuses them)
    _REMINDER_WORDS = {"calendar", "event", "remind", "reminder", "task", "schedule"}
    lower_msg = user_message.lower()
    if any(w in lower_msg for w in _REMINDER_WORDS):
        for fc in result.get("function_calls", []):
            if fc.get("name") == "set_alarm":
                # Parse time directly from user query (more reliable than model output)
                time_match = re.search(
                    r'(?:at|by)\s+(\d{1,2}[.:]\d{2}\s*(?:am|pm)?|\d{1,2}\s*(?:am|pm))',
                    lower_msg
                )
                time_str = time_match.group(1).replace(".", ":") if time_match else None
                if not time_str:
                    # Fall back to model's hour/minute
                    args = fc.get("arguments", {})
                    h, m = int(args.get("hour", 0)) % 24, int(args.get("minute", 0))
                    period = "AM" if h < 12 else "PM"
                    dh = h if h <= 12 else h - 12
                    if dh == 0:
                        dh = 12
                    time_str = f"{dh}:{m:02d} {period}"
                # Extract title from query
                title_match = re.search(r'(?:to|for)\s+(.+?)(?:\s+at\s+|\s+by\s+|$)', lower_msg)
                title = title_match.group(1).strip() if title_match else "Reminder"
                fc["name"] = "create_reminder"
                fc["arguments"] = {"title": title, "time": time_str}

    # Execute skills from function calls
    skill_results = []
    for fc in result.get("function_calls", []):
        skill_name = fc.get("name", "")
        skill_args = fc.get("arguments", {})
        sr = registry.execute(skill_name, skill_args)
        skill_results.append({
            "skill": skill_name,
            "success": sr.success,
            "output": sr.output,
            "data": sr.data,
        })

    total_ms = (time.time() - start) * 1000

    # Build human-readable response
    if skill_results:
        response_parts = []
        for sr in skill_results:
            if sr["success"]:
                response_parts.append(sr["output"])
            else:
                response_parts.append(f"[Error] {sr['output']}")
        response_message = "\n\n".join(response_parts)
    else:
        response_message = "I couldn't determine which action to take. Could you rephrase?"

    return {
        "message": response_message,
        "function_calls": result.get("function_calls", []),
        "skill_results": skill_results,
        "privacy": {
            "risk_level": privacy_result.risk_level.value,
            "pii_types": privacy_result.pii_types,
            "recommendation": privacy_result.recommendation,
            "summary": privacy_result.summary,
        },
        "routing": {
            "source": result.get("source", "unknown"),
            "override": effective_override,
            "confidence": result.get("confidence", 0),
        },
        "total_time_ms": total_ms,
    }


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    _register_all_skills()
    print(f"Registered {len(get_registry().list_skills())} skills.")
    yield


app = FastAPI(
    title="Privacy-First Hybrid Agent",
    description="OpenClaw-inspired agent with confidential privacy layer",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        process_chat,
        req.message,
        req.routing_override.value,
        None,
    )
    return ChatResponse(**result)


@app.get("/api/skills", response_model=List[SkillInfo])
async def list_skills():
    registry = get_registry()
    return [
        SkillInfo(
            name=s.name,
            description=s.description,
            parameters=s.parameters,
        )
        for s in registry.list_skills()
    ]


@app.post("/api/privacy")
async def privacy_check(req: PrivacyCheckRequest):
    result = scan_privacy(req.text)
    return {
        "risk_level": result.risk_level.value,
        "pii_types": result.pii_types,
        "recommendation": result.recommendation,
        "summary": result.summary,
        "pii_count": len(result.pii_found),
        "redacted": redact_pii(req.text, result),
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "skills": len(get_registry().list_skills())}


# ---------------------------------------------------------------------------
# WebSocket for real-time chat
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_chat(ws: WebSocket):
    await ws.accept()
    conversation_history = []

    try:
        while True:
            data = await ws.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                payload = {"message": data, "routing_override": "auto"}

            user_msg = payload.get("message", "")
            override = payload.get("routing_override", "auto")

            # Send typing indicator
            await ws.send_json({"type": "typing", "status": True})

            # Process in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                process_chat,
                user_msg,
                override,
                list(conversation_history),
            )

            # Update conversation history
            conversation_history.append({"role": "user", "content": user_msg})
            conversation_history.append({"role": "assistant", "content": result["message"]})

            # Keep history manageable
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]

            await ws.send_json({"type": "response", **result})

    except WebSocketDisconnect:
        pass


# ---------------------------------------------------------------------------
# Serve React frontend (static files)
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).resolve().parent / "static"

if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = STATIC_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(STATIC_DIR / "index.html"))
