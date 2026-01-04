# Phase 1: Project Foundation

**Goal:** Establish project structure, dependencies, and core data models.

## Deliverables

### Project Setup
- Python 3.11+ package with `pyproject.toml`
- Dependencies: anthropic, pydantic, langfuse, rich, pytest, pytest-asyncio, ruff
- Async test support via `asyncio_mode = "auto"`

### Schemas (`src/schemas/`)
| Module | Contents |
|--------|----------|
| `core.py` | `ActionType`, `GameState`, `PlayerMemory`, `PlayerResponse`, `Event` |
| `actions.py` | SGR outputs: `SpeakingOutput`, `VotingOutput`, `NightKillOutput`, `InvestigationOutput`, `LastWordsOutput`, `DefenseOutput`, `BaseThinking` |
| `transcript.py` | `Speech`, `DefenseSpeech`, `DayRoundTranscript`, `CompressedRoundSummary`, `Transcript` |
| `persona.py` | `Persona`, `PersonaIdentity`, `VoiceAndBehavior`, `RoleGuidance` |
| `__init__.py` | Re-exports all public types |

### Configuration (`src/config.py`)
- Environment-backed settings via pydantic-settings
- API keys, model name, retry policy, paths
- Cached `get_settings()` accessor

### Tests
| File | Coverage |
|------|----------|
| `conftest.py` | Fixtures: sample_game_state, sample_persona, sample_memory, seven_personas |
| `test_schemas.py` | Schema validation, SGR output shapes, persona constraints |

## Files Created
```
src/__init__.py
src/config.py
src/schemas/__init__.py
src/schemas/core.py
src/schemas/actions.py
src/schemas/transcript.py
src/schemas/persona.py
src/storage/__init__.py
tests/conftest.py
tests/test_schemas.py
```
