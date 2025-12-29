# Architecture

Visual overview of system components and their interactions.

## High-Level Components

```mermaid
graph TB
    subgraph Engine["Game Engine"]
        GR[GameRunner]
        GSM[GameStateManager]
        EL[EventLog]
        TM[TranscriptManager]
        CB[ContextBuilder]
        VR[VoteResolver]
        PH[Phases]
    end

    subgraph Players["Player Agents"]
        PA1[PlayerAgent 1]
        PA2[PlayerAgent 2]
        PA7[PlayerAgent ...]
    end

    subgraph Providers["LLM Providers"]
        AP[AnthropicProvider]
        GP["GeminiProvider (future)"]
    end

    subgraph Storage["Storage"]
        DB[(SQLite)]
        JSON[JSON Logs]
    end

    subgraph Schemas["Schemas"]
        PS[Persona]
        SGR[SGR Outputs]
        TR[Transcripts]
        EV[Events]
    end

    GR --> GSM
    GR --> PH
    PH --> PA1
    PH --> PA2
    PH --> PA7
    PA1 --> AP
    PA2 --> AP
    PA7 --> GP

    GSM --> EL
    EL --> TM
    TM --> CB
    CB --> PA1
    CB --> PA2
    CB --> PA7

    PH --> VR

    GR --> JSON
    GR --> DB

    PS --> PA1
    SGR --> AP
    TR --> CB
    EV --> EL
```

## Game Flow Sequence

```mermaid
sequenceDiagram
    participant GR as GameRunner
    participant GSM as GameStateManager
    participant CB as ContextBuilder
    participant PA as PlayerAgent
    participant PR as Provider
    participant LLM as LLM API

    Note over GR: Game Start
    GR->>GSM: Initialize (assign roles)

    loop Each Phase
        GR->>GSM: Get current state
        GR->>CB: Build context for player
        CB->>PA: Pass context + transcript + memory
        PA->>PR: Request action
        PR->>LLM: Prompt with SGR schema
        LLM-->>PR: Structured response
        PR-->>PA: Parsed output + updated memory
        PA-->>GR: Action result
        GR->>GSM: Update state
    end

    Note over GR: Game End
    GR->>GR: Save JSON log
```

## Data Flow: Player Turn

```mermaid
flowchart LR
    subgraph Input["Raw Inputs"]
        GS[GameState]
        TR[Transcript]
        MEM[Memory + Beliefs]
        PER[Persona]
        ROLE[Role + Private Info]
    end

    subgraph Engine["Game Engine"]
        CB[ContextBuilder]
    end

    subgraph Agent["PlayerAgent"]
        PA[Agent]
    end

    subgraph Provider["LLM Provider"]
        PR[Provider]
        PROMPT[Build Prompt]
        PARSE[Parse Response]
    end

    subgraph Output["Response Output"]
        SGR[Action Output - SGR]
        UMEM[Updated Memory]
        ACT[Action - speech/vote/target]
    end

    GS --> CB
    TR --> CB
    MEM --> CB
    PER --> CB
    ROLE --> CB

    CB --> PA
    PA --> PR
    PR --> PROMPT
    PROMPT --> LLM[(LLM API)]
    LLM --> PARSE
    PARSE --> SGR
    PARSE --> UMEM
    SGR --> UMEM
    SGR --> ACT
```

## Schema Relationships

```mermaid
classDiagram
    class Persona {
        identity: PersonaIdentity
        voice_and_behavior: VoiceAndBehavior
        role_guidance: RoleGuidance?
        relationships: dict
    }

    class PersonaIdentity {
        name: str
        background: str
        core_traits: list
    }

    class VoiceAndBehavior {
        speech_style: str
        reasoning_style: str
        accusation_style: str
        defense_style: str
        trust_disposition: str
        risk_tolerance: str
        signature_phrases: list
        quirks: list
    }

    class RoleGuidance {
        town: str
        mafia: str
        detective: str
    }

    class PlayerMemory {
        facts: dict
        beliefs: dict
    }

    class GameState {
        phase: str
        round_number: int
        living_players: list
        dead_players: list
        nominated_players: list
    }

    class BaseThinking {
        new_events: list
        notable_changes: list
        suspicion_updates: dict
        pattern_notes: list
        current_goal: str
        reasoning: str
    }

    class SpeakingOutput {
        information_to_share: list
        information_to_hide: list
        speech: str
        nomination: str
    }

    class VotingOutput {
        vote_reasoning: str
        vote: str
    }

    Persona *-- PersonaIdentity
    Persona *-- VoiceAndBehavior
    Persona *-- RoleGuidance

    SpeakingOutput --|> BaseThinking
    VotingOutput --|> BaseThinking
```

## Database ERD (SQLite)

```mermaid
erDiagram
    PERSONAS ||--o{ GAME_PLAYERS : participates
    GAMES ||--o{ GAME_PLAYERS : includes
    TOURNAMENTS ||--o{ GAMES : schedules
    TOURNAMENTS ||--o{ PERSONA_MEMORIES : has
    PERSONAS ||--o{ PERSONA_MEMORIES : remembers
    PERSONAS ||--o{ PERSONA_MEMORIES : is_opponent

    PERSONAS {
        text id PK
        text name
        text definition
        int games_played
        int wins
    }

    GAMES {
        text id PK
        text tournament_id FK
        datetime timestamp
        text winner
        int rounds
        text log_file
    }

    GAME_PLAYERS {
        text game_id PK, FK
        text persona_id PK, FK
        text role
        text outcome
    }

    TOURNAMENTS {
        text id PK
        text name
        text status
        text roster
        int games_total
        text standings
    }

    PERSONA_MEMORIES {
        text tournament_id PK, FK
        text persona_id PK, FK
        text opponent_id PK, FK
        text memory
        int games_together
        datetime last_updated
    }
```

## Transcript Window

```mermaid
flowchart TB
    subgraph Window["2-Round Window"]
        CR[Current Round<br/>DayRoundTranscript<br/>Full Detail]
        PR[Previous Round<br/>DayRoundTranscript<br/>Full Detail]
    end

    subgraph Compressed["Older Rounds"]
        R1[Round N-2<br/>CompressedRoundSummary]
        R2[Round N-3<br/>CompressedRoundSummary]
        R3[...]
    end

    TM[TranscriptManager] --> Window
    TM --> Compressed

    Window --> CB[ContextBuilder]
    Compressed --> CB
    CB --> PA[PlayerAgent]
```

## Engine Phases

```mermaid
stateDiagram-v2
    [*] --> NightZero: Game Start

    NightZero --> Day1: Mafia Coordination

    Day1 --> Night1: Discussion + Vote

    Night1 --> Day2: Kill + Investigation
    Day2 --> Night2: Discussion + Vote

    Night2 --> Day3: Kill + Investigation
    Day3 --> Night3: Discussion + Vote

    Night3 --> [*]: Check Win Condition
    Day2 --> [*]: Town Wins (both Mafia dead)
    Day3 --> [*]: Mafia Wins (Mafia >= Town)

    note right of NightZero: No kill, Mafia strategize
    note right of Day1: No death announcement
    note right of Night1: 2-round Mafia coordination
```

## File Structure

```mermaid
graph TB
    subgraph src["/src"]
        subgraph schemas["/schemas"]
            core[core.py]
            actions[actions.py]
            transcript[transcript.py]
            persona[persona.py]
        end

        subgraph providers["/providers"]
            base[base.py]
            anthropic[anthropic.py]
        end

        subgraph engine["/engine"]
            state[state.py]
            events[events.py]
            trans[transcript.py]
            context[context.py]
            voting[voting.py]
            phases[phases.py]
            game[game.py]
            run[run.py]
        end

        subgraph players["/players"]
            agent[agent.py]
            pactions[actions.py]
        end

        subgraph personas["/personas"]
            initial[initial.py]
        end

        subgraph storage["/storage"]
            database[database.py]
            json_logs[json_logs.py]
        end
    end
```
