# DeepMemory LLM - Visual Architecture Diagrams

This document contains interactive Mermaid diagrams that visualize the system architecture.

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Next.js Frontend]
        Chat[Chat Interface]
        Folders[Folder Manager]
        Personas[Persona Cards]
        UI --> Chat
        UI --> Folders
        UI --> Personas
    end

    subgraph "API Layer"
        FastAPI[FastAPI Server]
        Chat -.HTTP/WebSocket.-> FastAPI
        Folders -.HTTP.-> FastAPI
        Personas -.HTTP.-> FastAPI
    end

    subgraph "Agent Layer"
        Librarian[Librarian Agent<br/>Context Retrieval]
        Strategist[Strategist Agent<br/>Response Synthesis]
        Profiler[Profiler Agent<br/>Persona Management]
        Validator[Validator Agent<br/>Conflict Detection]
        
        FastAPI --> Librarian
        Librarian --> Strategist
        Profiler --> Strategist
        Validator -.validates.-> Librarian
    end

    subgraph "Learning Layer"
        Learning[Learning Loop]
        PostTurn[Post-Turn Extraction]
        Reflection[Reflection Events]
        Compression[Background Compression]
        
        Learning --> PostTurn
        Learning --> Reflection
        Learning --> Compression
        Strategist -.triggers.-> Learning
    end

    subgraph "Data Layer"
        Postgres[(PostgreSQL<br/>+pgvector)]
        Pinecone[(Pinecone<br/>Vector Store)]
        Neo4j[(Neo4j<br/>Knowledge Graph)]
        
        Librarian <--> Pinecone
        Librarian <--> Neo4j
        Librarian <--> Postgres
        Profiler <--> Postgres
        Validator <--> Postgres
        Learning <--> Postgres
        Learning <--> Pinecone
        Learning <--> Neo4j
    end

    subgraph "AI Models"
        GeminiPro[Gemini 3 Pro<br/>2M token context]
        GeminiFlash[Gemini 3 Flash<br/>Fast extraction]
        Llama[Llama BGE<br/>1024-dim embeddings]
        
        Librarian --> GeminiPro
        Strategist --> GeminiPro
        Profiler --> GeminiFlash
        Learning --> GeminiFlash
        Librarian --> Llama
        Learning --> Llama
    end

    style Librarian fill:#e1f5ff
    style Strategist fill:#fff9e1
    style Profiler fill:#ffe1f5
    style Validator fill:#f5e1ff
    style Learning fill:#e1ffe1
    style GeminiPro fill:#ffd4d4
    style GeminiFlash fill:#ffd4d4
    style Llama fill:#ffd4d4
```

## 2. Query Processing Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant FastAPI
    participant Librarian
    participant Profiler
    participant Strategist
    participant Learning
    participant Pinecone
    participant Neo4j
    participant Postgres
    participant Gemini

    User->>Frontend: Ask question
    Frontend->>FastAPI: POST /api/chat
    
    par Parallel Context Gathering
        FastAPI->>Librarian: Prepare context
        Librarian->>Gemini: Extract entities
        Gemini-->>Librarian: ["Entity1", "Entity2"]
        
        Librarian->>Pinecone: Multi-vector search
        Pinecone-->>Librarian: Top-100 chunks
        
        Librarian->>Neo4j: Graph traversal
        Neo4j-->>Librarian: Related nodes
        
    and Get Personas
        FastAPI->>Profiler: Get relevant profiles
        Profiler->>Postgres: Query personas
        Postgres-->>Profiler: Persona data
    end
    
    Librarian->>Gemini: Generate context brief
    Gemini-->>Librarian: Synthesized context (20k tokens)
    Librarian-->>FastAPI: Context brief + citations
    Profiler-->>FastAPI: Persona profiles
    
    FastAPI->>Strategist: Generate response
    Note over Strategist: Input: Query + Context + Personas
    Strategist->>Gemini: Generate with thinking mode
    Gemini-->>Strategist: Strategic response
    Strategist-->>FastAPI: Final response
    
    FastAPI-->>Frontend: Stream response
    Frontend-->>User: Display answer
    
    Note over FastAPI,Learning: Background processing starts
    FastAPI->>Learning: Post-turn extraction (async)
    Learning->>Gemini: Extract facts/entities
    Gemini-->>Learning: Extracted data
    Learning->>Postgres: Store insights
    Learning->>Neo4j: Update graph
    Learning->>Pinecone: Update vectors
```

## 3. Memory Hierarchy

```mermaid
graph LR
    subgraph "Tier 1: Active Memory"
        T1[Current Conversation<br/>~100k tokens<br/>Last 20-30 turns<br/>Latency: 0ms]
    end
    
    subgraph "Tier 2: Cached Context"
        T2[Vertex AI Cache<br/>~1M tokens<br/>Active projects<br/>Latency: 50ms]
    end
    
    subgraph "Tier 3: Infinite Storage"
        T3A[Pinecone Vectors<br/>Unlimited<br/>Semantic search]
        T3B[Neo4j Graph<br/>Unlimited<br/>Relationship traversal]
        T3C[PostgreSQL<br/>Unlimited<br/>Structured data]
        T3[Tier 3<br/>Latency: 100-300ms]
        T3 --> T3A
        T3 --> T3B
        T3 --> T3C
    end
    
    subgraph "Tier 4: Compressed Archives"
        T4A[L1: Session Summaries<br/>50k → 5k tokens]
        T4B[L2: Project Summaries<br/>500k → 50k tokens]
        T4C[L3: Identity Summary<br/>5M → 200k tokens]
        T4[Tier 4<br/>10M+ functional<br/>Latency: 200-500ms]
        T4 --> T4A
        T4 --> T4B
        T4 --> T4C
    end
    
    Query((User Query)) --> T1
    T1 -.insufficient.-> T2
    T2 -.retrieve deeper.-> T3
    T3 -.contextual summary.-> T4
    
    T4 -.compressed context.-> Response
    T3 -.detailed facts.-> Response
    T2 -.recent work.-> Response
    T1 -.immediate context.-> Response
    
    Response((Strategic<br/>Answer))
    
    style T1 fill:#d4edda
    style T2 fill:#d1ecf1
    style T3 fill:#fff3cd
    style T4 fill:#f8d7da
    style Query fill:#6c757d,color:#fff
    style Response fill:#28a745,color:#fff
```

## 4. Multi-Dimensional Vector Search

```mermaid
graph TB
    Query[User Query:<br/>"Handle conflict with Jordy"]
    
    subgraph "Embedding Generation"
        E1[Semantic Embedding<br/>Raw query]
        E2[Sentiment Embedding<br/>Emotion + dynamics]
        E3[Strategic Embedding<br/>Goals + decisions]
        E4[Temporal Embedding<br/>Evolution over time]
    end
    
    Query --> E1
    Query --> E2
    Query --> E3
    Query --> E4
    
    subgraph "Pinecone Namespaces"
        NS1[semantic namespace]
        NS2[sentiment namespace]
        NS3[strategic namespace]
        NS4[temporal namespace]
    end
    
    E1 -.1024-dim vector.-> NS1
    E2 -.1024-dim vector.-> NS2
    E3 -.1024-dim vector.-> NS3
    E4 -.1024-dim vector.-> NS4
    
    subgraph "Search Results"
        R1[Top-25 chunks<br/>0.85+ similarity]
        R2[Top-25 chunks<br/>0.82+ similarity]
        R3[Top-25 chunks<br/>0.80+ similarity]
        R4[Top-25 chunks<br/>0.78+ similarity]
    end
    
    NS1 --> R1
    NS2 --> R2
    NS3 --> R3
    NS4 --> R4
    
    Fusion[Reciprocal Rank Fusion<br/>Weight: 0.35, 0.25, 0.25, 0.15]
    R1 --> Fusion
    R2 --> Fusion
    R3 --> Fusion
    R4 --> Fusion
    
    Final[Final Ranked List<br/>Top-100 chunks<br/>~200k tokens]
    Fusion --> Final
    
    style Query fill:#007bff,color:#fff
    style Fusion fill:#ffc107
    style Final fill:#28a745,color:#fff
```

## 5. Knowledge Graph Structure

```mermaid
graph LR
    subgraph "Person Nodes"
        Thomas[Thomas<br/>Person]
        Ella[Ella<br/>Person]
        Jordy[Jordy<br/>Person]
        Sarah[Sarah<br/>Person]
    end
    
    subgraph "Project Nodes"
        P1[Mobile App<br/>Project]
        P2[E-commerce<br/>Project]
    end
    
    subgraph "Concept Nodes"
        C1[Quality<br/>Concept]
        C2[Speed<br/>Concept]
        C3[Innovation<br/>Concept]
        C4[Security<br/>Concept]
    end
    
    subgraph "Event Nodes"
        Ev1[Q4 Deadline Crisis<br/>Event]
    end
    
    subgraph "Decision Nodes"
        D1[Extended Timeline<br/>Decision]
    end
    
    Thomas -->|KNOWS| Ella
    Thomas -->|KNOWS| Jordy
    Ella -->|KNOWS| Sarah
    
    Thomas -->|WORKS_ON| P1
    Thomas -->|WORKS_ON| P2
    Jordy -->|WORKS_ON| P1
    
    Ella -->|VALUES| C3
    Ella -->|VALUES| C4
    Jordy -->|VALUES| C1
    Sarah -->|VALUES| C1
    
    Jordy -->|RELATES_TO| Ev1
    Ev1 -->|CAUSES| D1
    
    C1 -->|CONTRADICTS| C2
    
    style Thomas fill:#007bff,color:#fff
    style Ella fill:#e83e8c,color:#fff
    style Jordy fill:#fd7e14,color:#fff
    style Sarah fill:#6f42c1,color:#fff
    style P1 fill:#20c997
    style P2 fill:#20c997
    style C1 fill:#ffc107
    style C2 fill:#ffc107
    style C3 fill:#ffc107
    style C4 fill:#ffc107
    style Ev1 fill:#dc3545,color:#fff
    style D1 fill:#17a2b8
```

## 6. Learning Loop Cycle

```mermaid
stateDiagram-v2
    [*] --> UserQuery
    UserQuery --> AgentProcessing
    
    state AgentProcessing {
        [*] --> Librarian
        Librarian --> Strategist
        Strategist --> Response
    }
    
    AgentProcessing --> ResponseDelivered
    
    state ResponseDelivered {
        [*] --> UserSees
    }
    
    ResponseDelivered --> PostTurnExtraction
    
    state PostTurnExtraction {
        [*] --> ExtractFacts
        ExtractFacts --> ExtractEntities
        ExtractEntities --> AnalyzeSentiment
        AnalyzeSentiment --> UpdateGraph
        UpdateGraph --> UpdateVectors
        UpdateVectors --> DetectConflicts
    }
    
    PostTurnExtraction --> CheckReflectionTrigger
    
    state CheckReflectionTrigger <<choice>>
    CheckReflectionTrigger --> ReflectionEvent: Every 5 turns
    CheckReflectionTrigger --> WaitNextQuery: Continue
    
    state ReflectionEvent {
        [*] --> AnalyzeSession
        AnalyzeSession --> GenerateSummary
        GenerateSummary --> UpdateL1Summary
        UpdateL1Summary --> UpdatePersonas
    }
    
    ReflectionEvent --> WaitNextQuery
    WaitNextQuery --> UserQuery
    
    state BackgroundCompression {
        [*] --> ScanOldConversations
        ScanOldConversations --> CompressL1toL2
        CompressL1toL2 --> CompressL2toL3
        CompressL2toL3 --> ArchiveOriginals
    }
    
    BackgroundCompression --> [*]
    
    note right of PostTurnExtraction
        Runs asynchronously
        ~1-2 seconds
        Updates knowledge base
    end note
    
    note right of ReflectionEvent
        Triggered every 5 turns
        ~5 seconds
        Generates session insights
    end note
    
    note right of BackgroundCompression
        Scheduled (daily/weekly)
        Compresses old data
        Frees up active memory
    end note
```

## 7. Data Ingestion Pipeline

```mermaid
flowchart TD
    Start([User Uploads File]) --> Detect{Detect Source Type}
    
    Detect -->|conversations.json| ChatGPT[ChatGPT Parser]
    Detect -->|Google Takeout| Gemini[Gemini Parser]
    Detect -->|Markdown/Text| Manual[Manual Parser]
    
    ChatGPT --> Parse[Parse Conversations]
    Gemini --> Parse
    Manual --> Parse
    
    Parse --> Coreference[Coreference Resolution]
    
    Coreference --> Pass1[PASS 1:<br/>Identify all entities<br/>Gemini Flash]
    Pass1 --> Pass2[PASS 2:<br/>Resolve pronouns<br/>3-message context]
    Pass2 --> Augment[Create dual storage:<br/>1. Original text<br/>2. Resolved text]
    
    Augment --> Extract[Extract Metadata]
    
    Extract --> Metadata{Metadata Extraction}
    Metadata -->|Entities| Entities[People, places,<br/>projects]
    Metadata -->|Topics| Topics[Tags, categories]
    Metadata -->|Sentiment| Sentiment[Emotion, tone]
    Metadata -->|Importance| Importance[Score 1-10]
    
    Entities --> BuildGraph[Build Knowledge Graph]
    Topics --> BuildGraph
    Sentiment --> Embeddings
    Importance --> Embeddings
    
    BuildGraph --> Neo4j[(Neo4j)]
    
    Embeddings[Generate Embeddings] --> Multi{Multi-Dimensional}
    Multi -->|Semantic| Sem[Semantic embedding<br/>RESOLVED text]
    Multi -->|Sentiment| Sent[Sentiment embedding]
    Multi -->|Strategic| Strat[Strategic embedding]
    Multi -->|Temporal| Temp[Temporal embedding]
    
    Sem --> Pinecone[(Pinecone)]
    Sent --> Pinecone
    Strat --> Pinecone
    Temp --> Pinecone
    
    BuildGraph --> Store[Store in PostgreSQL]
    Embeddings --> Store
    Augment --> Store
    
    Store --> Postgres[(PostgreSQL<br/>content + resolved_content)]
    
    Postgres --> Report[Generate Ingestion Report]
    Neo4j --> Report
    Pinecone --> Report
    
    Report --> End([Complete])
    
    style Start fill:#28a745,color:#fff
    style End fill:#28a745,color:#fff
    style Detect fill:#ffc107
    style Metadata fill:#ffc107
    style Multi fill:#ffc107
    style Report fill:#17a2b8
    style Coreference fill:#e1f5ff
    style Pass1 fill:#e1f5ff
    style Pass2 fill:#e1f5ff
    style Augment fill:#e1f5ff
```

## 7b. Coreference Resolution Detail

```mermaid
sequenceDiagram
    participant Msg as Message
    participant CR as CoreferenceResolver
    participant GF as Gemini Flash
    participant DB as Database
    
    Note over Msg,DB: Conversation: "She loves it. She told me yesterday."
    
    Msg->>CR: resolve_conversation(messages)
    
    CR->>GF: PASS 1: Identify entities
    Note over GF: Full conversation scan
    GF-->>CR: {"people": ["Ella", "Thomas"]}
    
    loop For each message
        CR->>GF: PASS 2: Resolve pronouns
        Note over GF: Context: 3 messages before/after<br/>Entities: ["Ella", "Thomas"]<br/>Message: "She loves it"
        GF-->>CR: {"pronoun": "She", "refers_to": "Ella",<br/>"confidence": 0.95}
        
        CR->>CR: Check confidence
        
        alt Confidence >= 0.5
            CR->>CR: Replace pronoun
            Note over CR: "She" → "Ella"
        else Low confidence
            CR->>CR: Keep original + flag
            Note over CR: Log warning
        end
    end
    
    CR->>DB: Store both versions
    Note over DB: content: "She loves it"<br/>resolved_content: "Ella loves it"
    
    CR-->>Msg: Resolved messages
```

## 8. Agent Collaboration Flow

```mermaid
graph TB
    subgraph "Input"
        UserQuery[User Query]
        History[Conversation History]
    end
    
    UserQuery --> Router{Query Router}
    History --> Router
    
    Router -->|Complex query| FullPipeline[Full Agent Pipeline]
    Router -->|Simple query| FastPath[Fast Path<br/>Direct to Gemini]
    
    FastPath --> QuickResponse[Quick Response]
    
    FullPipeline --> Librarian
    
    subgraph Librarian[Librarian Agent]
        L1[Extract entities]
        L2[Vector search:<br/>4 namespaces]
        L3[Graph traversal:<br/>depth=3]
        L4[Hybrid ranking]
        L5[Generate context brief<br/>~20k tokens]
        
        L1 --> L2
        L1 --> L3
        L2 --> L4
        L3 --> L4
        L4 --> L5
    end
    
    L5 --> Validator
    
    subgraph Validator[Validator Agent]
        V1[Check contradictions]
        V2[Flag conflicts]
        V3[Verify sources]
        
        V1 --> V2
        V2 --> V3
    end
    
    V3 --> Profiler
    
    subgraph Profiler[Profiler Agent]
        P1[Identify mentioned people]
        P2[Load persona profiles]
        P3[Enrich with psychology]
        
        P1 --> P2
        P2 --> P3
    end
    
    L5 --> Strategist
    P3 --> Strategist
    
    subgraph Strategist[Strategist Agent]
        S1[Receive:<br/>• Context brief<br/>• Personas<br/>• History]
        S2[Gemini Pro<br/>Thinking Mode: HIGH]
        S3[Synthesize response]
        S4[Add citations]
        S5[Format output]
        
        S1 --> S2
        S2 --> S3
        S3 --> S4
        S4 --> S5
    end
    
    S5 --> Response[Strategic Response<br/>with sources]
    QuickResponse --> Output
    Response --> Output
    
    Output[Output to User]
    
    Response -.trigger.-> Learning
    
    subgraph Learning[Learning Loop - Async]
        Learn1[Extract new facts]
        Learn2[Update personas]
        Learn3[Update graph]
        Learn4[Update vectors]
        Learn5[Check for reflection]
        
        Learn1 --> Learn2
        Learn2 --> Learn3
        Learn3 --> Learn4
        Learn4 --> Learn5
    end
    
    Learn5 -.continuous improvement.-> Database[(Knowledge Base)]
    
    style UserQuery fill:#007bff,color:#fff
    style Router fill:#ffc107
    style Output fill:#28a745,color:#fff
    style Database fill:#6c757d,color:#fff
    style Learning fill:#e1ffe1
```

## 9. Context Window Utilization

```mermaid
gantt
    title Context Window Usage Per Query (Gemini 3 Pro: 2M tokens)
    dateFormat X
    axisFormat %s

    section User Input
    Query + History          :a1, 0, 10000
    
    section Librarian Processing
    Retrieved chunks         :a2, 0, 200000
    Thinking prompt          :a3, 200000, 205000
    Context brief generation :a4, 205000, 215000
    
    section Context Brief Output
    Context brief            :a5, 0, 20000
    
    section Profiler Processing
    Persona query            :a6, 0, 15000
    Profile data             :a7, 15000, 20000
    
    section Strategist Processing
    Full input assembly      :a8, 0, 37500
    Thinking mode            :a9, 37500, 47500
    Response generation      :a10, 47500, 52500
    
    section Final Output
    User response            :a11, 0, 5000
```

## 10. Performance Breakdown

```mermaid
pie title Query Processing Time Distribution (Total: ~7s)
    "Entity Extraction (Gemini Flash)" : 500
    "Embedding Generation (Llama)" : 100
    "Vector Search (Pinecone)" : 200
    "Graph Traversal (Neo4j)" : 150
    "Context Brief (Gemini Pro)" : 3000
    "Persona Retrieval (PostgreSQL)" : 50
    "Strategic Response (Gemini Pro)" : 4000
```

---

## Usage Instructions

1. **Viewing Diagrams**: These Mermaid diagrams can be rendered in:
   - GitHub (automatic rendering)
   - VS Code with [Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid)
   - [Mermaid Live Editor](https://mermaid.live/)

2. **Editing**: Copy any diagram code block to customize for presentations or documentation.

3. **Export**: Use Mermaid Live Editor to export as PNG/SVG for presentations.

## Diagram Summary

- **Diagram 1**: Overall system architecture with all components
- **Diagram 2**: Sequential query processing flow with timing
- **Diagram 3**: Memory hierarchy showing four tiers
- **Diagram 4**: Multi-dimensional vector search strategy
- **Diagram 5**: Knowledge graph structure example
- **Diagram 6**: Learning loop state machine
- **Diagram 7**: Data ingestion pipeline flow
- **Diagram 8**: Agent collaboration and workflow
- **Diagram 9**: Context window utilization chart
- **Diagram 10**: Performance time breakdown

These diagrams complement the detailed analysis in `ARCHITECTURE_ANALYSIS.md`.
