import json, subprocess
from flask import Blueprint, request as flask_request, jsonify
from main import generate_cactus, generate_cloud

bp = Blueprint("api", __name__)

TOOL_LIBRARY = {
    "get_weather": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"}
            },
            "required": ["location"],
        },
    },
    "set_alarm": {
        "name": "set_alarm",
        "description": "Set an alarm for a given time",
        "parameters": {
            "type": "object",
            "properties": {
                "hour": {"type": "integer", "description": "Hour"},
                "minute": {"type": "integer", "description": "Minute"},
            },
            "required": ["hour", "minute"],
        },
    },
    "send_message": {
        "name": "send_message",
        "description": "Send a message to a contact",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Recipient name"},
                "message": {"type": "string", "description": "Message content"},
            },
            "required": ["recipient", "message"],
        },
    },
    "create_reminder": {
        "name": "create_reminder",
        "description": "Create a reminder with a title and time",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Reminder title"},
                "time": {"type": "string", "description": "Reminder time"},
            },
            "required": ["title", "time"],
        },
    },
    "search_contacts": {
        "name": "search_contacts",
        "description": "Search for a contact by name",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
    "play_music": {
        "name": "play_music",
        "description": "Play a song or playlist",
        "parameters": {
            "type": "object",
            "properties": {
                "song": {"type": "string", "description": "Song or playlist name"},
            },
            "required": ["song"],
        },
    },
    "set_timer": {
        "name": "set_timer",
        "description": "Set a countdown timer",
        "parameters": {
            "type": "object",
            "properties": {
                "minutes": {"type": "integer", "description": "Minutes"},
            },
            "required": ["minutes"],
        },
    },
}


def check_openclaw():
    """Check if OpenClaw CLI is installed and reachable."""
    try:
        proc = subprocess.run(
            ["openclaw", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        if proc.returncode == 0:
            return {"available": True, "version": proc.stdout.strip()}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return {"available": False, "version": None}


def generate_openclaw(messages, tools):
    """Run function calling via OpenClaw agent gateway."""
    import time

    user_content = " ".join(m["content"] for m in messages if m["role"] == "user")
    tool_desc = json.dumps(tools, indent=2)
    prompt = (
        f"Given these available tools:\n{tool_desc}\n\n"
        f"User request: {user_content}\n\n"
        'Return ONLY a JSON object: {"function_calls": [{"name": "...", "arguments": {...}}]}'
    )

    start_time = time.time()
    try:
        proc = subprocess.run(
            ["openclaw", "agent", "--message", prompt, "--json", "--timeout", "30"],
            capture_output=True, text=True, timeout=35,
        )
        total_time_ms = (time.time() - start_time) * 1000

        if proc.returncode != 0:
            return {"function_calls": [], "total_time_ms": total_time_ms, "error": proc.stderr.strip()}

        raw = json.loads(proc.stdout)
        content = raw.get("content", raw.get("message", proc.stdout))
        try:
            parsed = json.loads(content) if isinstance(content, str) else content
            function_calls = parsed.get("function_calls", [])
        except (json.JSONDecodeError, AttributeError):
            function_calls = []

        return {"function_calls": function_calls, "total_time_ms": total_time_ms}
    except FileNotFoundError:
        return {
            "function_calls": [],
            "total_time_ms": 0,
            "error": "OpenClaw CLI not installed. Install with: npm install -g openclaw@latest",
        }
    except subprocess.TimeoutExpired:
        return {
            "function_calls": [],
            "total_time_ms": (time.time() - start_time) * 1000,
            "error": "OpenClaw request timed out",
        }
    except Exception as e:
        return {
            "function_calls": [],
            "total_time_ms": (time.time() - start_time) * 1000,
            "error": str(e),
        }


@bp.route("/api/openclaw-status")
def api_openclaw_status():
    return jsonify(check_openclaw())


@bp.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = flask_request.json
    messages = [{"role": "user", "content": data["message"]}]
    tool_names = data.get("tools", [])
    tools = [TOOL_LIBRARY[t] for t in tool_names if t in TOOL_LIBRARY]
    threshold = float(data.get("threshold", 0.99))

    if not tools:
        return jsonify({"error": "No tools selected"}), 400

    local = generate_cactus(messages, tools)

    recommendation = "local" if local["confidence"] >= threshold else "cloud"

    return jsonify({
        "confidence": local["confidence"],
        "local_time_ms": local["total_time_ms"],
        "function_calls": local["function_calls"],
        "recommendation": recommendation,
        "threshold": threshold,
    })


@bp.route("/api/execute", methods=["POST"])
def api_execute():
    data = flask_request.json
    messages = [{"role": "user", "content": data["message"]}]
    tool_names = data.get("tools", [])
    tools = [TOOL_LIBRARY[t] for t in tool_names if t in TOOL_LIBRARY]
    mode = data.get("mode", "local")

    if mode == "local":
        cached = data.get("cached_result")
        if cached:
            result = {
                "function_calls": cached.get("function_calls", []),
                "total_time_ms": cached.get("total_time_ms", 0),
                "confidence": cached.get("confidence", 0),
                "source": "on-device",
            }
        else:
            result = generate_cactus(messages, tools)
            result["source"] = "on-device"
    elif mode == "openclaw":
        result = generate_openclaw(messages, tools)
        result["source"] = "cloud (openclaw)"
    else:
        result = generate_cloud(messages, tools)
        result["source"] = "cloud (gemini)"

    return jsonify(result)
