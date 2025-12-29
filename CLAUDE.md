# AI Mafia Agent League

LLM agents play competitive Mafia. See `/docs` for game rules and system design.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run a game (when implemented)
python -m src.engine.run
```

## Tech Stack

- **Python**: 3.11+
- **LLM Providers**: anthropic, google-generativeai, openai (thin wrappers, no LangChain)
- **Schemas**: pydantic
- **Storage**: aiosqlite + JSON files
- **Observability**: langfuse
- **Testing**: pytest, pytest-asyncio

## Code Style

**Linting and formatting with ruff:**

```bash
ruff check .          # Lint
ruff check . --fix    # Lint and auto-fix
ruff format .         # Format
```

**ruff config** (in `pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
```

## Coding Principles

### Simplicity
- No premature abstractions - write the straightforward thing first
- Explicit over clever - readable code beats compact code
- Minimal dependencies - only add what's truly needed
- Delete unused code - no commented-out blocks or dead imports

### Type Safety
- Type hints on all function signatures
- Pydantic models for structured data (schemas, configs, API responses)
- Avoid `Any` - be specific about types
- Mutable defaults: use `Field(default_factory=list)` not `= []`

### Testability
- Pure functions where possible - input in, output out, no side effects
- Injectable dependencies - pass LLM clients, don't import globals
- Mockable boundaries - LLM calls behind interfaces for testing

### Async
- asyncio native - no anyio/trio unless truly needed
- `async def` for all LLM calls and I/O operations
- Use `asyncio.gather()` for parallel operations

### Error Handling
- LLM calls: retry with exponential backoff, max 3 attempts
- After retries exhausted: raise or apply sensible default
- Log all errors with context (player, phase, action type)
- Never silently swallow exceptions

## Project Structure

```
/src
├── /engine        # Game loop, rules, state management
├── /players       # Player agent logic
├── /providers     # LLM client wrappers
├── /personas      # Persona definitions
├── /schemas       # Pydantic models
└── /storage       # Database, JSON logs
/tests             # pytest tests
/docs              # Specifications
/logs              # Game output logs
/data              # SQLite database
```

## Testing

```bash
pytest                           # Run all tests
pytest -v                        # Verbose output
pytest tests/test_engine.py      # Single file
pytest -k "test_voting"          # By name pattern
pytest --tb=short                # Shorter tracebacks
```

**Patterns:**
- Mock LLM responses - never call real APIs in tests
- Use fixtures for game state, player instances, mock providers
- Test file naming: `test_*.py`
- Test function naming: `test_<what>_<condition>_<expected>`

**Example fixture:**
```python
@pytest.fixture
def game_state():
    return GameState(
        phase="day_1",
        round_number=1,
        living_players=["P1", "P2", "P3"],
        dead_players=[],
        nominated_players=[]
    )
```

## Key Patterns

### Schema-Guided Reasoning (SGR)
Single LLM call per action. Schema field order forces reasoning: observe → analyze → strategize → decide → output. See `src/schemas/` for definitions.

### Player State
Players define their memory/beliefs each turn. Engine stores it between calls and passes it back. LLMs are stateless; engine manages continuity.

### Event Log
Runtime: builds player context (filtered public view). Persistence: saved to JSON with private reasoning for viewers.

## Git Workflow

**Branch naming:**
- `feat/<description>` - new features
- `fix/<description>` - bug fixes
- `refactor/<description>` - code restructuring

**Commit messages:**
- Start with verb: Add, Fix, Update, Remove, Refactor
- Keep first line under 72 chars
- Reference issue if applicable: `Fix voting logic (#12)`
