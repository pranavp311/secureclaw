"""
Telegram bot — privacy-aware hybrid agent accessible via Telegram.

Commands:
  /start   — welcome + skill list
  /skills  — list available skills
  /local   — force next request to run locally
  /cloud   — force next request to run on cloud
  /auto    — reset to auto routing
  /privacy — check privacy status of a message

Regular messages go through: privacy check → hybrid router → skill execution.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Ensure imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "cactus" / "python" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("CACTUS_NO_CLOUD_TELE", "1")

from agent.privacy import scan_privacy, RiskLevel
from agent.server import process_chat, _register_all_skills

logger = logging.getLogger(__name__)

# Per-user routing override state
_user_overrides: Dict[int, str] = {}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _privacy_badge(risk_level: str) -> str:
    badges = {
        "low": "🟢 Low Risk",
        "medium": "🟡 Medium Risk",
        "high": "🔴 High Risk",
    }
    return badges.get(risk_level, "⚪ Unknown")


def _routing_badge(source: str) -> str:
    if "on-device" in source or "local" in source:
        return "📱 On-Device"
    elif "cloud" in source:
        return "☁️ Cloud"
    return "❓ Unknown"


def _format_response(result: dict) -> str:
    """Format a chat result into a Telegram-friendly message."""
    parts = []

    # Privacy badge
    privacy = result.get("privacy", {})
    risk = privacy.get("risk_level", "low")
    parts.append(f"{_privacy_badge(risk)}")

    if privacy.get("pii_types"):
        parts.append(f"⚠️ PII detected: {', '.join(privacy['pii_types'])}")

    # Routing info
    routing = result.get("routing", {})
    source = routing.get("source", "unknown")
    parts.append(f"{_routing_badge(source)} | {result.get('total_time_ms', 0):.0f}ms")

    parts.append("")  # blank line

    # Main response
    parts.append(result.get("message", "No response."))

    # Function calls summary
    fcs = result.get("function_calls", [])
    if fcs:
        parts.append("")
        parts.append(f"🔧 Tools called: {', '.join(fc.get('name', '?') for fc in fcs)}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from agent.skills import get_registry
    registry = get_registry()
    skills = registry.list_skills()

    text = (
        "🛡️ *Privacy-First Hybrid Agent*\n\n"
        "I'm an intelligent assistant that protects your privacy. "
        "Sensitive prompts are automatically processed on-device using FunctionGemma, "
        "while complex tasks use Gemini cloud — you're always in control.\n\n"
        f"*{len(skills)} skills available:*\n"
    )
    for s in skills:
        text += f"  • `{s.name}` — {s.description}\n"

    text += (
        "\n*Commands:*\n"
        "  /skills — list skills\n"
        "  /local — force on-device processing\n"
        "  /cloud — force cloud processing\n"
        "  /auto — auto routing (default)\n"
        "  /privacy <text> — check text for PII\n"
        "\nJust send me a message to get started!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from agent.skills import get_registry
    registry = get_registry()
    skills = registry.list_skills()

    text = f"*Available Skills ({len(skills)}):*\n\n"
    for s in skills:
        text += f"🔹 `{s.name}`\n   {s.description}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_local(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    _user_overrides[user_id] = "local"
    await update.message.reply_text(
        "📱 *Routing set to LOCAL*\nAll requests will be processed on-device.\n"
        "Use /auto to reset.",
        parse_mode="Markdown",
    )


async def cmd_cloud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    _user_overrides[user_id] = "cloud"
    await update.message.reply_text(
        "☁️ *Routing set to CLOUD*\nAll requests will use Gemini cloud.\n"
        "Use /auto to reset.",
        parse_mode="Markdown",
    )


async def cmd_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    _user_overrides.pop(user_id, None)
    await update.message.reply_text(
        "🔄 *Routing set to AUTO*\nPrivacy layer + SmartRouter will decide.",
        parse_mode="Markdown",
    )


async def cmd_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "Usage: `/privacy <text to check>`",
            parse_mode="Markdown",
        )
        return

    result = scan_privacy(text)
    badge = _privacy_badge(result.risk_level.value)

    response = f"{badge}\n\n"
    response += f"*Summary:* {result.summary}\n"
    response += f"*Recommendation:* {result.recommendation}\n"

    if result.pii_found:
        response += f"\n*PII found ({len(result.pii_found)}):*\n"
        for m in result.pii_found:
            response += f"  • `{m.pii_type.value}` (confidence: {m.confidence:.0%})\n"

    await update.message.reply_text(response, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Message handler (main chat)
# ---------------------------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    user_id = update.effective_user.id
    override = _user_overrides.get(user_id, "auto")

    # Send typing action
    await update.message.chat.send_action("typing")

    # Process in thread pool
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            process_chat,
            user_msg,
            override,
            None,
        )
        response = _format_response(result)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        response = f"❌ Error processing request: {e}"

    # Split long messages (Telegram limit: 4096 chars)
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i + 4000])
    else:
        await update.message.reply_text(response)


# ---------------------------------------------------------------------------
# Bot startup
# ---------------------------------------------------------------------------

def run_telegram_bot():
    """Start the Telegram bot (blocking)."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("ERROR: Set TELEGRAM_BOT_TOKEN environment variable.")
        print("  1. Talk to @BotFather on Telegram")
        print("  2. Create a bot and get the token")
        print("  3. export TELEGRAM_BOT_TOKEN='your-token'")
        sys.exit(1)

    _register_all_skills()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("skills", cmd_skills))
    app.add_handler(CommandHandler("local", cmd_local))
    app.add_handler(CommandHandler("cloud", cmd_cloud))
    app.add_handler(CommandHandler("auto", cmd_auto))
    app.add_handler(CommandHandler("privacy", cmd_privacy))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Telegram bot started. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_telegram_bot()
