# Phase 1 and Phase 2 Quick Checks

These are lightweight integration/manual checks you can run to sanity‑check
Phase 1 and Phase 2 behavior. They are intentionally short and safe to run
locally. Phase 2 includes an optional live API call (network required).

## Phase 1 (Schemas + Storage)

1) Run unit tests for schemas and database:
```bash
pytest tests/test_schemas.py tests/test_database.py
```

2) Minimal manual DB smoke test:
```bash
python - <<'PY'
import asyncio
from src.schemas import Persona, PersonaIdentity, VoiceAndBehavior
from src.storage.database import Database

async def main():
    db = Database("data/mafia.db")
    await db.connect()
    await db.initialize_schema()

    persona = Persona(
        identity=PersonaIdentity(
            name="Manual Check",
            background="A quick manual check persona.",
            core_traits=["analytical", "cautious", "curious"],
        ),
        voice_and_behavior=VoiceAndBehavior(
            speech_style="Concise",
            reasoning_style="Logical",
            accusation_style="Evidence-based",
            defense_style="Calm",
            trust_disposition="neutral",
            risk_tolerance="moderate",
        ),
    )

    persona_id = await db.create_persona(persona)
    fetched = await db.get_persona(persona_id)
    print("created:", persona_id)
    print("fetched:", fetched.identity.name if fetched else None)

    await db.update_persona_stats(persona_id, games_played_delta=1, wins_delta=1)
    await db.record_game("manual_game_1", "town", 2, "logs/manual_game_1.json")
    await db.record_game_player("manual_game_1", persona_id, "town", "survived")
    print("games:", [g["id"] for g in await db.list_games()])

    await db.delete_game("manual_game_1")
    await db.close()

asyncio.run(main())
PY
```

## Phase 2 (Providers)

1) Run provider unit tests:
```bash
pytest tests/test_providers.py
```

2) Optional live API call (requires network access + valid key):
```bash
python - <<'PY'
import asyncio
import os
from src.providers import AnthropicProvider
from src.schemas import ActionType

async def main():
    key = os.environ["ANTHROPIC_API_KEY"]
    provider = AnthropicProvider(api_key=key)
    context = (
        "You are Player 1. You have been eliminated. "
        "Provide last words in one short paragraph."
    )
    result = await provider.act(ActionType.LAST_WORDS, context)
    print(result)

asyncio.run(main())
PY
```

Notes:
- The live call will incur API cost and requires network access.
- If you use Langfuse, confirm traces appear after the live call.
- If cost shows as zero, confirm the model is included in the provider pricing
  map and that Langfuse is receiving input/output usage details.
