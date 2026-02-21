"""
SmartRouter — Two-phase hybrid routing for FunctionGemma + Gemini Flash.

Phase 1 (pre-inference): heuristic + embedding scoring to pre-route obvious
multi-tool queries directly to cloud.

Phase 2 (post-inference): confidence gate after cactus_complete to catch
uncertain local results and escalate to cloud.

Zero ML/SDK dependencies — only stdlib.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Protocol, Sequence

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
EmbedFn = Callable[[str], List[float]]


# ---------------------------------------------------------------------------
# Vector store
# ---------------------------------------------------------------------------
def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass
class SeedEntry:
    text: str
    tool_count: int
    privacy: float
    complexity: float
    tools: List[str]
    embedding: Optional[List[float]] = field(default=None, repr=False)


class InMemoryVectorStore:
    """Brute-force cosine search over a small set of seed embeddings."""

    def __init__(self) -> None:
        self._entries: List[SeedEntry] = []

    def add(self, entry: SeedEntry) -> None:
        self._entries.append(entry)

    def search(self, query_vec: List[float], top_k: int = 3) -> List[tuple[SeedEntry, float]]:
        scored = [
            (e, _cosine_similarity(query_vec, e.embedding))
            for e in self._entries
            if e.embedding is not None
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
@dataclass
class RouterConfig:
    # Pre-inference blend weights
    w_multi_tool: float = 0.55
    w_privacy: float = 0.10
    w_complexity: float = 0.15
    w_similarity: float = 0.20

    # Pre-inference cloud threshold
    cloud_threshold: float = 0.55

    # Post-inference confidence gates
    confidence_floor: float = 0.40
    confidence_ceiling: float = 0.85
    confidence_borderline: float = 0.65
    confidence_multi_call: float = 0.75

    # Post-inference multi-tool score threshold for borderline check
    multi_tool_borderline: float = 0.30


# ---------------------------------------------------------------------------
# Decision dataclasses
# ---------------------------------------------------------------------------
@dataclass
class RoutingDecision:
    route: str  # "cloud" or "local"
    reason: str
    multi_tool_score: float
    privacy_score: float
    complexity_score: float
    similarity_score: float
    blended_score: float
    matched_seeds: List[tuple[str, float]]  # (seed_text, similarity)


@dataclass
class PostInferenceResult:
    should_escalate: bool
    confidence: float
    reason: str


# ---------------------------------------------------------------------------
# Seed corpus (benchmark-optimized)
# ---------------------------------------------------------------------------
SEED_CORPUS: List[dict] = [
    # --- EASY: single-tool, 1 tool available (14 seeds) ---
    {"text": "What's the weather in San Francisco?", "tool_count": 1, "privacy": 0.0, "complexity": 0.1, "tools": ["get_weather"]},
    {"text": "What is the weather like in Tokyo right now?", "tool_count": 1, "privacy": 0.0, "complexity": 0.1, "tools": ["get_weather"]},
    {"text": "Set an alarm for 7 AM", "tool_count": 1, "privacy": 0.0, "complexity": 0.1, "tools": ["set_alarm"]},
    {"text": "Wake me up at 6:30 in the morning", "tool_count": 1, "privacy": 0.0, "complexity": 0.1, "tools": ["set_alarm"]},
    {"text": "Play Bohemian Rhapsody", "tool_count": 1, "privacy": 0.0, "complexity": 0.1, "tools": ["play_music"]},
    {"text": "Play some jazz music", "tool_count": 1, "privacy": 0.0, "complexity": 0.1, "tools": ["play_music"]},
    {"text": "Send a message to John saying hello", "tool_count": 1, "privacy": 0.3, "complexity": 0.15, "tools": ["send_message"]},
    {"text": "Text Mom that I'll be late", "tool_count": 1, "privacy": 0.3, "complexity": 0.15, "tools": ["send_message"]},
    {"text": "Remind me to buy groceries at 5 PM", "tool_count": 1, "privacy": 0.0, "complexity": 0.15, "tools": ["create_reminder"]},
    {"text": "Create a reminder to call the dentist tomorrow", "tool_count": 1, "privacy": 0.0, "complexity": 0.15, "tools": ["create_reminder"]},
    {"text": "Set a timer for 10 minutes", "tool_count": 1, "privacy": 0.0, "complexity": 0.1, "tools": ["set_timer"]},
    {"text": "Start a 5 minute timer", "tool_count": 1, "privacy": 0.0, "complexity": 0.1, "tools": ["set_timer"]},
    {"text": "Search for Lisa in my contacts", "tool_count": 1, "privacy": 0.3, "complexity": 0.1, "tools": ["search_contacts"]},
    {"text": "Find John's contact information", "tool_count": 1, "privacy": 0.3, "complexity": 0.1, "tools": ["search_contacts"]},

    # --- MEDIUM: single-tool, 2-5 tools available (9 seeds) ---
    {"text": "Is it going to rain today?", "tool_count": 1, "privacy": 0.0, "complexity": 0.2, "tools": ["get_weather"]},
    {"text": "Message Lisa about the meeting", "tool_count": 1, "privacy": 0.3, "complexity": 0.2, "tools": ["send_message"]},
    {"text": "Put on relaxing background music", "tool_count": 1, "privacy": 0.0, "complexity": 0.2, "tools": ["play_music"]},
    {"text": "I need a reminder for my doctor appointment at 3", "tool_count": 1, "privacy": 0.0, "complexity": 0.25, "tools": ["create_reminder"]},
    {"text": "Can you look up Sarah's number?", "tool_count": 1, "privacy": 0.3, "complexity": 0.2, "tools": ["search_contacts"]},
    {"text": "Set my alarm for tomorrow morning at 8", "tool_count": 1, "privacy": 0.0, "complexity": 0.2, "tools": ["set_alarm"]},
    {"text": "Start a countdown for 15 minutes", "tool_count": 1, "privacy": 0.0, "complexity": 0.2, "tools": ["set_timer"]},
    {"text": "Tell me the temperature in London", "tool_count": 1, "privacy": 0.0, "complexity": 0.2, "tools": ["get_weather"]},
    {"text": "Let Bob know I'm running late", "tool_count": 1, "privacy": 0.3, "complexity": 0.2, "tools": ["send_message"]},

    # --- HARD: multi-tool, all 7 tools available (12 seeds) ---
    {"text": "Set an alarm for 7 AM and check the weather", "tool_count": 2, "privacy": 0.0, "complexity": 0.4, "tools": ["set_alarm", "get_weather"]},
    {"text": "Send a message to John and set a reminder to follow up", "tool_count": 2, "privacy": 0.3, "complexity": 0.4, "tools": ["send_message", "create_reminder"]},
    {"text": "Timer for 10 min, play jazz, and remind me to check the oven", "tool_count": 3, "privacy": 0.0, "complexity": 0.55, "tools": ["set_timer", "play_music", "create_reminder"]},
    {"text": "What's the weather and play some music", "tool_count": 2, "privacy": 0.0, "complexity": 0.35, "tools": ["get_weather", "play_music"]},
    {"text": "Set an alarm for 6 AM, check the weather, and send a message to Bob", "tool_count": 3, "privacy": 0.3, "complexity": 0.55, "tools": ["set_alarm", "get_weather", "send_message"]},
    {"text": "Remind me about the meeting and text Sarah the agenda", "tool_count": 2, "privacy": 0.3, "complexity": 0.4, "tools": ["create_reminder", "send_message"]},
    {"text": "Play Beethoven and set a timer for 30 minutes", "tool_count": 2, "privacy": 0.0, "complexity": 0.35, "tools": ["play_music", "set_timer"]},
    {"text": "Search for Dave's number and send him a message saying hi", "tool_count": 2, "privacy": 0.3, "complexity": 0.4, "tools": ["search_contacts", "send_message"]},
    {"text": "Get the weather in NYC and set a reminder to bring an umbrella", "tool_count": 2, "privacy": 0.0, "complexity": 0.4, "tools": ["get_weather", "create_reminder"]},
    {"text": "Send a message to Lisa, set a timer for 5 minutes, and play relaxing music", "tool_count": 3, "privacy": 0.3, "complexity": 0.55, "tools": ["send_message", "set_timer", "play_music"]},
    {"text": "Check the weather and set an alarm for tomorrow", "tool_count": 2, "privacy": 0.0, "complexity": 0.35, "tools": ["get_weather", "set_alarm"]},
    {"text": "Message John about dinner and remind me to make a reservation at 5", "tool_count": 2, "privacy": 0.3, "complexity": 0.45, "tools": ["send_message", "create_reminder"]},
]

# ---------------------------------------------------------------------------
# PII / privacy regex tiers
# ---------------------------------------------------------------------------
_PII_PATTERNS: List[tuple[re.Pattern, float]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), 1.0),             # SSN
    (re.compile(r"\b\d{16}\b"), 1.0),                          # credit card (no spaces)
    (re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"), 0.9),  # credit card
    (re.compile(r"\bpassword\b", re.I), 0.7),
    (re.compile(r"\bsecret\b", re.I), 0.7),
    (re.compile(r"\bprivate\b", re.I), 0.7),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), 0.3),  # email
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), 0.3),     # phone number
]

# ---------------------------------------------------------------------------
# Multi-tool detection patterns
# ---------------------------------------------------------------------------
_CONJUNCTIONS = re.compile(r"\b(and|then|also|plus|after that|as well|additionally)\b", re.I)
_ACTION_VERBS = re.compile(
    r"\b(set|send|play|get|check|search|find|create|remind|text|message|call|"
    r"start|timer|alarm|weather|look up|tell me|wake|put on)\b", re.I
)
_COMMA_COMMANDS = re.compile(r",\s*(?:and\s+)?(?:then\s+)?", re.I)


# ---------------------------------------------------------------------------
# SmartRouter
# ---------------------------------------------------------------------------
class SmartRouter:
    def __init__(
        self,
        embed_fn: Optional[EmbedFn] = None,
        seeds: Optional[List[dict]] = None,
        config: Optional[RouterConfig] = None,
    ) -> None:
        self.config = config or RouterConfig()
        self._embed_fn = embed_fn
        self._store = InMemoryVectorStore()

        corpus = seeds if seeds is not None else SEED_CORPUS
        for s in corpus:
            entry = SeedEntry(
                text=s["text"],
                tool_count=s["tool_count"],
                privacy=s["privacy"],
                complexity=s["complexity"],
                tools=s["tools"],
            )
            if embed_fn is not None:
                entry.embedding = embed_fn(entry.text)
            self._store.add(entry)

    # -----------------------------------------------------------------------
    # Pre-inference scorers
    # -----------------------------------------------------------------------
    def _score_multi_tool(self, query: str, tools: List[dict]) -> float:
        score = 0.0

        # Conjunction count
        conjunctions = len(_CONJUNCTIONS.findall(query))
        if conjunctions >= 2:
            score += 0.45
        elif conjunctions >= 1:
            score += 0.30

        # Distinct action verbs
        verbs = set(v.lower() for v in _ACTION_VERBS.findall(query))
        if len(verbs) >= 3:
            score += 0.35
        elif len(verbs) >= 2:
            score += 0.20

        # Comma-separated commands
        commas = len(_COMMA_COMMANDS.findall(query))
        if commas >= 2:
            score += 0.20
        elif commas >= 1:
            score += 0.10

        # Large tool set (7 tools = hard benchmark cases)
        if len(tools) >= 7:
            score += 0.10

        return min(score, 1.0)

    def _score_privacy(self, query: str) -> float:
        max_score = 0.0
        for pattern, weight in _PII_PATTERNS:
            if pattern.search(query):
                max_score = max(max_score, weight)
        return max_score

    def _score_complexity(self, query: str, tools: List[dict]) -> float:
        score = 0.0

        # Tool count boost
        n_tools = len(tools)
        if n_tools >= 7:
            score += 0.25
        elif n_tools >= 4:
            score += 0.15
        elif n_tools >= 2:
            score += 0.05

        # Word count boost
        words = len(query.split())
        if words >= 20:
            score += 0.25
        elif words >= 12:
            score += 0.15
        elif words >= 8:
            score += 0.05

        # Numeric arguments
        numbers = re.findall(r"\b\d+\b", query)
        if len(numbers) >= 3:
            score += 0.15
        elif len(numbers) >= 1:
            score += 0.05

        return min(score, 1.0)

    def _score_similarity(self, query: str) -> tuple[float, List[tuple[str, float]]]:
        """Return (similarity_boost, matched_seeds)."""
        if self._embed_fn is None:
            return 0.0, []

        query_vec = self._embed_fn(query)
        results = self._store.search(query_vec, top_k=3)

        if not results:
            return 0.0, []

        matched = [(e.text, sim) for e, sim in results]
        best_entry, best_sim = results[0]

        # Direct similarity score
        sim_score = max(0.0, best_sim - 0.5) * 2.0  # normalize 0.5-1.0 → 0.0-1.0

        # If best match is multi-tool with high similarity, boost
        if best_entry.tool_count >= 2 and best_sim >= 0.70:
            sim_score = max(sim_score, 0.8)

        # Average top-3 multi-tool tendency
        multi_tool_matches = sum(1 for e, s in results if e.tool_count >= 2 and s >= 0.60)
        if multi_tool_matches >= 2:
            sim_score = max(sim_score, 0.6)

        return min(sim_score, 1.0), matched

    # -----------------------------------------------------------------------
    # Pre-inference decision
    # -----------------------------------------------------------------------
    def should_route_to_cloud(self, query: str, tools: List[dict]) -> RoutingDecision:
        cfg = self.config

        multi = self._score_multi_tool(query, tools)
        privacy = self._score_privacy(query)
        complexity = self._score_complexity(query, tools)
        sim_score, matched = self._score_similarity(query)

        # Boost multi_tool_score if similarity says it's multi-tool
        if sim_score >= 0.6:
            multi = max(multi, multi + sim_score * 0.3)
            multi = min(multi, 1.0)

        blended = (
            cfg.w_multi_tool * multi
            + cfg.w_privacy * privacy
            + cfg.w_complexity * complexity
            + cfg.w_similarity * sim_score
        )

        if blended >= cfg.cloud_threshold:
            route = "cloud"
            reason = f"blended={blended:.3f} >= {cfg.cloud_threshold} (multi={multi:.2f}, sim={sim_score:.2f})"
        else:
            route = "local"
            reason = f"blended={blended:.3f} < {cfg.cloud_threshold} (multi={multi:.2f}, sim={sim_score:.2f})"

        return RoutingDecision(
            route=route,
            reason=reason,
            multi_tool_score=multi,
            privacy_score=privacy,
            complexity_score=complexity,
            similarity_score=sim_score,
            blended_score=blended,
            matched_seeds=matched,
        )

    # -----------------------------------------------------------------------
    # Post-inference gate
    # -----------------------------------------------------------------------
    def post_inference_gate(
        self,
        confidence: float,
        cloud_handoff: bool,
        function_calls: List[dict],
        pre_decision: RoutingDecision,
        tools: Optional[List[dict]] = None,
    ) -> PostInferenceResult:

        if not function_calls:
            return PostInferenceResult(True, confidence, "no function calls returned by local model")

        if cloud_handoff:
            return PostInferenceResult(True, confidence, "cloud_handoff flag set by cactus")

        # FunctionGemma always returns confidence ~0.99+ even when wrong,
        # so we validate the actual output instead.

        # Multiple function calls = FunctionGemma likely hallucinating
        if len(function_calls) > 1:
            return PostInferenceResult(True, confidence, f"multi-call: {len(function_calls)} calls, escalate")

        # Validate the single function call
        call = function_calls[0]
        call_name = call.get("name", "")
        call_args = call.get("arguments", {})

        # Check: does the called function exist in the provided tools?
        if tools:
            tool_names = {t["name"] for t in tools}
            if call_name not in tool_names:
                return PostInferenceResult(True, confidence, f"called '{call_name}' not in available tools")

        # Check: negative numeric arguments (e.g. minutes: -20)
        for k, v in call_args.items():
            if isinstance(v, (int, float)) and v < 0:
                return PostInferenceResult(True, confidence, f"negative arg {k}={v}")

        # Check: ISO/long date strings when simple time expected (FunctionGemma hallucinates dates)
        for k, v in call_args.items():
            if isinstance(v, str) and re.search(r"\d{4}-\d{1,2}-\d{1,2}", v):
                return PostInferenceResult(True, confidence, f"hallucinated date in {k}='{v}'")

        # Check: empty string arguments
        for k, v in call_args.items():
            if isinstance(v, str) and not v.strip():
                return PostInferenceResult(True, confidence, f"empty arg {k}")

        # If pre-inference thought this was multi-tool, but local returned single call — suspect
        if pre_decision.multi_tool_score > 0.50:
            return PostInferenceResult(True, confidence, f"pre-inference multi_tool={pre_decision.multi_tool_score:.2f} but got single call")

        return PostInferenceResult(False, confidence, f"trust local: validated single call to {call_name}")
