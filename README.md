<img src="assets/banner.png" alt="SecureClaw Banner" style="border-radius: 30px; width: 100%;">

# SecureClaw — Privacy-First Hybrid AI Agent

**Private AI inference, by default.**

SecureClaw is a multi-platform AI agent that combines on-device FunctionGemma inference with Gemini cloud fallback, adding a **privacy-first confidential layer** that detects sensitive data and forces local execution when PII is present. Users always retain override control across web, mobile, and Telegram interfaces.

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interfaces                       │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ React Web│  │ React Native │  │  Telegram Bot      │  │
│  │ (SecureClaw│ │ Mobile App   │  │  (python-telegram) │  │
│  │  + Canvas │  │ (Expo)       │  │                    │  │
│  │  Dots BG) │  │              │  │                    │  │
│  └─────┬─────┘  └──────┬───────┘  └────────┬──────────┘  │
│        │               │                   │              │
│        ▼               ▼                   ▼              │
│  ┌─────────────────────────────────────────────────┐     │
│  │           FastAPI / Flask Backend               │     │
│  │  REST + WebSocket endpoints                     │     │
│  └──────────────────────┬──────────────────────────┘     │
│                         │                                 │
│  ┌──────────────────────▼──────────────────────────┐     │
│  │         Phase 0: Privacy Layer                   │     │
│  │  Regex PII detection (email, SSN, CC, phone,    │     │
│  │  passwords, health terms, financial data)        │     │
│  │  → Risk: LOW / MEDIUM / HIGH                     │     │
│  │  → HIGH/MEDIUM → force local execution           │     │
│  └──────────────────────┬──────────────────────────┘     │
│                         │                                 │
│  ┌──────────────────────▼──────────────────────────┐     │
│  │         SmartRouter (Two-Phase Hybrid)           │     │
│  │                                                   │     │
│  │  Phase 1: Pre-inference heuristics               │     │
│  │  • Multi-tool detection (keyword + embedding)    │     │
│  │  • Query complexity scoring                       │     │
│  │  • Semantic similarity to known-hard queries      │     │
│  │  • Blended score → route to local or cloud       │     │
│  │                                                   │     │
│  │  Phase 2: Post-inference validation              │     │
│  │  • Schema validation (types, required params)    │     │
│  │  • Argument sanity checks (ranges, formats)      │     │
│  │  • Query-output consistency (time/value match)   │     │
│  │  • High-confidence trust (≥0.90 bypasses         │     │
│  │    multi-tool escalation)                         │     │
│  │  • Retry once before cloud fallback              │     │
│  └──────────┬───────────────────┬──────────────────┘     │
│             │                   │                         │
│    ┌────────▼────────┐ ┌───────▼─────────┐               │
│    │  FunctionGemma  │ │  Gemini Cloud   │               │
│    │  (on-device)    │ │  (2.5/2.0 Flash)│               │
│    │  270M params    │ │  REST API       │               │
│    │  ~1-2s latency  │ │  ~2-4s latency  │               │
│    │  Private ✓      │ │  Higher accuracy│               │
│    └────────┬────────┘ └───────┬─────────┘               │
│             └─────────┬────────┘                         │
│                       ▼                                   │
│  ┌─────────────────────────────────────────────────┐     │
│  │            Skill Execution Layer                 │     │
│  │  14 registered skills with real OS integration:  │     │
│  │  • set_alarm → macOS Reminders + notification   │     │
│  │  • get_weather → wttr.in live data              │     │
│  │  • web_browse → HTTP fetch + HTML extraction    │     │
│  │  • file_read/write → sandboxed workspace        │     │
│  │  • calendar_add/list/delete → local JSON store  │     │
│  │  • send_message, play_music, set_timer, etc.    │     │
│  └─────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## Rubric 1: Hybrid Routing Algorithm

**SmartRouter** — a two-phase routing system inlined in `main.py`:

### Phase 1: Pre-Inference Heuristics
- **Multi-tool detection**: Keyword patterns (`"and"`, `"then"`, `"also"`) combined with semantic embedding similarity to known multi-tool queries using `cactus_embed` + cosine similarity.
- **Complexity scoring**: Counts conjunctions, tool-keyword matches, and query length to estimate if FunctionGemma can handle it.
- **Similarity scoring**: Vector store of seed queries (known-hard examples) compared via embedding distance.
- **Blended decision**: Weighted combination (55% multi-tool, 20% similarity, 25% complexity) against a 0.55 threshold.

### Phase 2: Post-Inference Validation
- **Schema validation**: Checks function name exists in tool set, required params present, types match.
- **Argument sanity**: Rejects negative values, out-of-range hours/minutes, hallucinated dates, empty strings.
- **Query-output consistency**: Parses expected values from the query (e.g., "7am" → hour=7, minute=0) and compares with model output. Catches FunctionGemma errors where values are valid but wrong.
- **High-confidence trust**: When FunctionGemma returns ≥90% confidence with valid output, trusts it even if multi-tool heuristics flagged the query — prevents unnecessary cloud escalation.
- **Retry before fallback**: One retry on validation failure before escalating to Gemini.

### Privacy-Aware Routing (Phase 0)
- Regex-based PII scanner detects email, phone, SSN, credit card (with Luhn check), IP addresses, passwords, health/financial terms.
- Risk levels: LOW (no PII) → auto routing, MEDIUM/HIGH → forces local execution regardless of confidence.
- User can override via UI toggle (Auto / Local / Cloud).

---

## Rubric 2: End-to-End Product

SecureClaw executes function calls to solve **real-world problems** across three platforms:

### Web UI (`web/`)
- React + TailwindCSS + Vite
- **Interactive canvas dots background** that reacts to cursor (dots enlarge and brighten) and pulses orange during loading (center-outward ripple)
- "Secure**Claw**" branding with black/orange theme matching mobile app
- Privacy badges (Private / Caution / Sensitive), routing indicators (on-device / cloud), latency display
- Tools bottom-sheet modal for selecting active skills
- Routing override toggle (Auto / Local / Cloud)
- WebSocket real-time chat with REST fallback

### Mobile App (`mobile/`)
- React Native + Expo
- Same black/orange design language, interactive dots background (touch-reactive)
- Two-step flow: **Analysis** (shows confidence, recommendation, local vs cloud choice) → **Execute** (runs selected mode)
- Cloud provider selection (Gemini / OpenClaw)
- Confidence threshold slider
- Tool selection settings modal

### Telegram Bot (`agent/telegram_bot.py`)
- Commands: `/start`, `/skills`, `/local`, `/cloud`, `/auto`, `/privacy`
- Privacy badges and routing indicators in responses
- Per-user routing override state

### Real OS Integration
- **set_alarm**: Creates a Reminder in macOS Reminders app with alert + shows native notification with sound
- **get_weather**: Fetches live weather data from wttr.in
- **web_browse**: HTTP fetch with HTML-to-text extraction and summarization
- **file_read/write/list**: Sandboxed file operations in agent workspace
- **calendar**: Local JSON-backed calendar with add/list/delete

### Backend (`agent/server.py`)
- FastAPI with REST (`/api/chat`, `/api/skills`, `/api/privacy`) and WebSocket (`/ws`) endpoints
- Flask backend (`app/routes.py`) for mobile app compatibility (`/api/analyze`, `/api/execute`)
- Privacy layer integrated as Phase 0 in the routing pipeline
- Skill registry with 14 auto-registered tools

---

## Rubric 3: Voice-to-Action

The architecture is designed for low-latency voice integration:

- **FunctionGemma on-device inference** completes in ~1-2 seconds, enabling near-real-time voice-to-action pipelines when combined with `cactus_transcribe`.
- **Privacy layer runs in <1ms** (pure regex), adding zero perceptible latency to the voice pipeline.
- **Skill execution is immediate** — alarm, timer, and reminder skills trigger OS-level actions (AppleScript) without network round-trips.
- The mobile app's touch-reactive dots background provides visual feedback during processing, and the web UI's orange pulse animation indicates active inference — both designed for voice interaction UX where visual loading state matters.

---

## Project Structure

```
secureclaw/
├── main.py                    # Hybrid router (generate_hybrid) — leaderboard submission
├── benchmark.py               # Objective scoring
├── submit.py                  # Leaderboard submission
├── smart_router.py            # SmartRouter standalone reference
├── server.py                  # Flask entry point for mobile backend
├── run_agent.sh               # Run scripts (server/telegram/dev/build)
├── agent/
│   ├── __init__.py
│   ├── privacy.py             # Regex PII detector + risk scoring
│   ├── server.py              # FastAPI backend (web UI + API)
│   ├── telegram_bot.py        # Telegram bot
│   ├── requirements.txt
│   └── skills/
│       ├── __init__.py        # Skill base class + registry
│       ├── alarm_timer.py     # macOS alarm + timer (AppleScript)
│       ├── browse.py          # Web browsing + HTML extraction
│       ├── calendar_mgr.py    # Calendar CRUD (local JSON)
│       ├── contacts.py        # Contact search
│       ├── files.py           # Sandboxed file I/O
│       ├── messaging.py       # Message sending
│       ├── reminders.py       # Reminders + music playback
│       └── weather.py         # Live weather (wttr.in)
├── app/
│   ├── __init__.py            # Flask app factory
│   ├── routes.py              # Mobile API (/api/analyze, /api/execute)
│   ├── static/                # Flask static assets
│   └── templates/             # Flask HTML templates
├── mobile/
│   ├── App.tsx                # React Native entry point
│   ├── package.json
│   └── src/
│       ├── api.ts             # Backend API client
│       ├── theme.ts           # Black/orange design tokens
│       ├── types.ts           # TypeScript interfaces
│       └── components/
│           ├── AnalysisCard.tsx
│           ├── DotsBackground.tsx
│           ├── Header.tsx
│           ├── InputBar.tsx
│           ├── LoadingDots.tsx
│           ├── ResultCard.tsx
│           └── ToolsModal.tsx
└── web/
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── App.tsx            # Main app with SecureClaw branding
        ├── main.tsx
        ├── index.css          # Black/orange theme CSS
        ├── hooks/useChat.ts   # WebSocket + REST chat hook
        └── components/
            ├── ChatPanel.tsx
            ├── DotsBackground.tsx  # Canvas interactive dots
            ├── OverrideToggle.tsx
            ├── PrivacyBadge.tsx
            ├── RoutingIndicator.tsx
            └── SkillPanel.tsx
```

---

## Quick Start

### Prerequisites
- macOS with Cactus SDK installed (`cactus build --python`)
- FunctionGemma weights downloaded (`cactus download google/functiongemma-270m-it --reconvert`)
- Gemini API key (`export GEMINI_API_KEY="your-key"`)

### Web UI
```bash
cd web && npm install && npm run build
cd .. && pip install -r agent/requirements.txt
./run_agent.sh server
# Open http://localhost:8000
```

### Mobile App
```bash
pip install flask
GEMINI_API_KEY="your-key" python server.py --port 5001
# In another terminal:
cd mobile && npm install && npx expo start
```

### Telegram Bot
```bash
export TELEGRAM_BOT_TOKEN="your-token"
./run_agent.sh telegram
```

### Leaderboard Submission
```bash
python submit.py --team "YourTeamName" --location "YourCity"
```

---

## Team

Built at the Google DeepMind × Cactus Compute Hackathon.
