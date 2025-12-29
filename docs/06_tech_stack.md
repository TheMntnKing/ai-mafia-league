# Tech Stack

## Core

- **Language:** Python 3.11+
- **LLM Providers:** Claude Haiku (primary, version configurable), Gemini Flash 3.0, Qwen 3
- **Storage:** SQLite + JSON files
- **Observability:** Langfuse

## LLM Providers

| Provider | Model | Pricing | Structured Output |
|----------|-------|---------|-------------------|
| Anthropic | Claude Haiku (configurable) | $1/$5 per M tokens | tool_use or JSON mode |
| Google | Gemini Flash 3.0 | Competitive | response_schema |
| Qwen | Qwen 3 | Free (local) | JSON mode |

Thin wrapper over provider SDKs. No LangChain/LangGraph.

## Schema-Guided Reasoning (SGR)

Single LLM call per action. Schema field order forces reasoning flow: observe → analyze → strategize → decide → output.

Action-specific schemas: `SpeakingOutput`, `VotingOutput`, `NightKillOutput`, `InvestigationOutput`, `LastWordsOutput`, `DefenseOutput`.

See [schemas.py](schemas.py) for full definitions.

## Storage

**SQLite:** Personas, games, participants, tournaments. See [database.sql](database.sql).

**JSON logs:** Complete game records in `logs/`. Schema versioned. Event types: `phase_start`, `speech`, `vote`, `night_kill`, `investigation`, `last_words`, `defense`, `game_end`.

## Observability

Langfuse for tracing, cost tracking, debugging. Decorator-based:

```python
@observe(name="player_act")
async def player_act(...): ...

@observe(name="game_run")
async def run_game(...): ...
```

## Project Structure

```
/agent_mafia
├── /docs              # Specs
├── /src
│   ├── /engine        # Game loop, rules
│   ├── /players       # Player agents
│   ├── /providers     # LLM clients
│   ├── /personas      # Persona definitions
│   ├── /schemas       # Pydantic schemas
│   └── /storage       # SQLite, JSON
├── /logs              # Game logs
├── /tests
└── /data              # SQLite DB
```

## Token Budget

Target: 15-20k tokens per call. Typical: ~7-8k.

- Fixed context: ~1500
- Current round speeches: ~2100
- Previous round: ~2100
- Compressed older rounds: ~500-1000
- Memory/beliefs: ~1000

## Cost Estimates

Per game (7 players, 4-5 rounds):

| Metric | Estimate |
|--------|----------|
| LLM calls | 50-80 |
| Input tokens | 30-50k |
| Output tokens | 10-20k |
| **Cost (Haiku)** | **$0.20-0.80** |

## Dependencies

```
anthropic
google-generativeai
openai
pydantic
aiosqlite
langfuse
pytest
pytest-asyncio
rich
```
