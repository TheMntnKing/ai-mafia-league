# Phase 2: LLM Provider Layer

**Goal:** Anthropic provider with structured output and observability.

## Deliverables

### Provider Base (`src/providers/base.py`)
- `PlayerProvider` protocol: `act(action_type, context) -> dict`
- `retry_with_backoff` decorator: async exponential backoff, configurable exceptions
- Exceptions: `ProviderError`, `RetryExhausted`, `InvalidResponseError`

### Anthropic Provider (`src/providers/anthropic.py`)
- `AnthropicProvider` implementing `PlayerProvider`
- Uses tool_use to enforce structured output (schema from Pydantic models)
- Validates responses against action schema before returning
- Retries on `APIError` and `APIConnectionError` (max 3 attempts)
- Langfuse integration: `@observe` decorator, usage/cost tracking (optional, graceful fallback)

### Tests (`tests/test_providers.py`)
| Test Area | Coverage |
|-----------|----------|
| Retry decorator | Success first try, success after retry, exhaustion, exception filtering |
| Tool schema | Correct schema generation for SPEAK, VOTE, LAST_WORDS |
| Provider | Returns tool output, calls API correctly, missing tool_use error, invalid schema error |
| Retry integration | Retries on API error, exhausts after repeated failures |
| Observability | Langfuse receives usage details |

## Files Created
```
src/providers/__init__.py
src/providers/base.py
src/providers/anthropic.py
tests/test_providers.py
```

## Design Notes
- Tool_use pattern for structured output: define single tool per action type, force Claude to use it via `tool_choice`
- This ensures reliable JSON output matching the schema without parsing issues
