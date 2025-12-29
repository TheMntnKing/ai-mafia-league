# Phase 2 Implementation Summary

This is a human-readable snapshot of Phase 2 as implemented, including the
original provider layer plus the review-time fixes.

## Provider Base (protocol + retry)
The base layer in `src/providers/base.py` establishes the contract for LLM
providers and the retry utility:
- `PlayerProvider` defines `act(action_type, context)` as the standard API.
- `retry_with_backoff` implements async exponential backoff retries.
- Provider exceptions are centralized (`ProviderError`, `InvalidResponseError`).

### Changes Made During Review
- Added the spec-named `RetryExhausted` exception and kept the old
  `RetryExhaustedError` as a legacy alias.
- Updated the provider contract to state that providers return validated
  structured output.

## Anthropic Provider
`src/providers/anthropic.py` implements the only Phase 2 provider:
- Uses `AsyncAnthropic` with tool_use to enforce structured output.
- Builds per-action tool schemas from Pydantic models.
- Adds Langfuse tracing when available (with a no-op fallback if not installed).
- Emits generation spans with usage and cost details when model pricing is known.

### Changes Made During Review
- Tool outputs are now validated against the action schema before returning.
  Invalid shapes raise `InvalidResponseError` instead of slipping through.
- Langfuse traces are recorded as generation spans and include token usage;
  cost is computed for known models (e.g., `claude-3-5-haiku-20241022`).

## Tests
`tests/test_providers.py` covers:
- Retry behavior (success, retry, exhaustion, and exception filtering).
- Provider tool schema generation for key actions.
- Anthropic provider happy-path parsing and missing tool_use errors.

### Changes Made During Review
- Added tests for invalid schema responses (must raise `InvalidResponseError`).
- Added tests for retry on `APIConnectionError` and exhaustion behavior.
