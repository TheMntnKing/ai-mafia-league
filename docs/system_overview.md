# System Overview

Core components, data flow, and storage model for the game engine.

## Core Components

```mermaid
graph TB
    GR[GameRunner] --> GSM[GameStateManager]
    GR --> PH[Phases]
    PH --> EL[EventLog]
    PH --> TM[TranscriptManager]
    PH --> VR[VoteResolver]
    PH --> CB[ContextBuilder]
    CB --> PA[PlayerAgent]
    PA --> PR[Provider]
    GR --> JSON[JSON Logs]
```

## Game Loop (Phases)

- Night Zero: Mafia coordination only (no kill)
- Day: speeches -> nominations -> vote -> optional revote -> last words
- Night: Mafia kill coordination -> Detective investigation -> kill applied
- Win check after each phase

## Player Turn Data Flow

```mermaid
sequenceDiagram
    participant GR as GameRunner
    participant CB as ContextBuilder
    participant PA as PlayerAgent
    participant PR as Provider
    participant LLM as LLM API

    GR->>CB: Build context (state + transcript + events + memory + persona + role)
    CB->>PA: Context + action_type
    PA->>PR: Act(action_type, context)
    PR->>LLM: Invoke model (tool_use)
    LLM-->>PR: Structured output
    PR-->>PA: Parsed output
    PA-->>GR: PlayerResponse (output + updated memory)
```

## Transcript Window

```mermaid
flowchart TB
    subgraph Window["2-Round Window"]
        CR[Current Round<br/>Full Detail]
        PR[Previous Round<br/>Full Detail]
    end

    subgraph Compressed["Older Rounds"]
        R1[Round N-2<br/>Compressed]
        R2[Round N-3<br/>Compressed]
        R3[...]
    end

    TM[TranscriptManager] --> Window
    TM --> Compressed
    Window --> CB[ContextBuilder]
    Compressed --> CB
```

## Context Visibility

- Players only receive public events (private fields filtered).
- Full events (including private fields) are written to JSON logs for review.
