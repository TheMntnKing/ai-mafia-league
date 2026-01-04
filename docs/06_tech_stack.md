# Tech Stack

## Core

- **Language:** Python 3.11+
- **LLM Providers:** Claude Haiku (primary, version configurable), Gemini Flash 3.0, Qwen 3
- **Storage:** JSON files
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

See `src/schemas/actions.py` for action schema definitions.

## Storage

**JSON logs:** Complete game records in `logs/`. Schema versioned. Event types:
`phase_start`, `speech`, `vote_round`, `elimination`, `night_kill`, `investigation`,
`last_words`, `defense`, `game_end`.

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
│   └── /storage       # JSON logs
├── /logs              # Game logs
├── /tests
```

## Token Budget

Target: 15-20k tokens per call. Typical: ~7-8k.

- Fixed context: ~1500
- Current round speeches: ~2100
- Previous round: ~2100
- Compressed older rounds: ~500-1000
- Memory/beliefs: ~1000

## Cost Estimates

Per game (10 players, 6-8 rounds):

| Metric | Estimate |
|--------|----------|
| LLM calls | 80-120 |
| Input tokens | 50-90k |
| Output tokens | 15-30k |
| **Cost (Haiku)** | **$0.40-1.50** |

## Dependencies

```
anthropic
google-generativeai
openai
pydantic
langfuse
pytest
pytest-asyncio
rich
```
