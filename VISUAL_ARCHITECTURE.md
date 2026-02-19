# Visual Architecture & Flowcharts

This document contains comprehensive visual diagrams for the AI Model Manager MCP Server project.

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [Sequence Diagrams](#sequence-diagrams)
5. [Database Schema](#database-schema)
6. [Provider Integration Flow](#provider-integration-flow)

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "MCP Client Layer"
        A[Claude Desktop]
        B[Other MCP Clients]
    end
    
    subgraph "MCP Server Layer"
        C[MCP Server<br/>server.py]
        D[Tool Handlers]
        E[Resource Handlers]
    end
    
    subgraph "Core Components"
        F[Provider Manager]
        G[Database Layer]
        H[Configuration Manager]
    end
    
    subgraph "Provider Layer"
        I[Ollama Provider]
        J[OpenAI Provider]
        K[Anthropic Provider]
        L[Google Provider]
        M[Mistral Provider]
    end
    
    subgraph "External Services"
        N[Ollama Server<br/>Local]
        O[OpenAI API]
        P[Anthropic API]
        Q[Google API]
        R[Mistral API]
    end
    
    subgraph "Storage"
        S[(SQLite Database)]
        T[Config Files<br/>models.json]
        U[Environment<br/>.env]
    end
    
    A -->|stdio| C
    B -->|stdio| C
    C --> D
    C --> E
    D --> F
    E --> G
    F --> H
    F --> I
    F --> J
    F --> K
    F --> L
    F --> M
    I -->|HTTP| N
    J -->|HTTPS| O
    K -->|HTTPS| P
    L -->|HTTPS| Q
    M -->|HTTPS| R
    G --> S
    H --> T
    H --> U
    
    style C fill:#4A90E2
    style F fill:#50C878
    style G fill:#FFB347
    style S fill:#DDA0DD
```

---

## Component Architecture

```mermaid
graph LR
    subgraph "src/"
        A[server.py]
        
        subgraph "models/"
            B[base.py<br/>ModelProvider<br/>ModelInfo<br/>GenerationRequest]
        end
        
        subgraph "providers/"
            C[ollama.py]
            D[openai.py]
            E[anthropic.py]
            F[google.py]
            G[mistral.py]
        end
        
        subgraph "storage/"
            H[database.py<br/>SQLite Operations]
            I[config.py<br/>Configuration]
        end
        
        subgraph "routing/"
            J[Smart Routing<br/>Future]
        end
        
        subgraph "utils/"
            K[Utilities<br/>Future]
        end
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    A --> I
    C -.implements.-> B
    D -.implements.-> B
    E -.implements.-> B
    F -.implements.-> B
    G -.implements.-> B
    
    style A fill:#4A90E2
    style B fill:#50C878
    style H fill:#FFB347
    style I fill:#FFB347
```

---

## Data Flow Diagrams

### Generation Request Flow

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as MCP Server
    participant Handler as Tool Handler
    participant Provider as Model Provider
    participant API as External API
    participant DB as Database
    
    Client->>Server: generate tool call
    Server->>Handler: route to _handle_generate()
    Handler->>Handler: validate arguments
    Handler->>Handler: create GenerationRequest
    Handler->>Provider: provider.generate(request)
    Provider->>API: HTTP/HTTPS request
    API-->>Provider: response
    Provider->>Provider: calculate tokens & cost
    Provider-->>Handler: GenerationResponse
    Handler->>DB: log_usage()
    DB-->>Handler: success
    Handler-->>Server: TextContent with result
    Server-->>Client: MCP response
    
    Note over Provider,API: Latency measured here
    Note over Handler,DB: Cost tracking
```

### Model Comparison Flow

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as MCP Server
    participant Handler as Compare Handler
    participant P1 as Provider 1
    participant P2 as Provider 2
    participant P3 as Provider 3
    participant DB as Database
    
    Client->>Server: compare_models tool call
    Server->>Handler: route to _handle_compare_models()
    
    par Parallel Generation
        Handler->>P1: generate(request)
        Handler->>P2: generate(request)
        Handler->>P3: generate(request)
    end
    
    P1-->>Handler: response 1
    P2-->>Handler: response 2
    P3-->>Handler: response 3
    
    Handler->>Handler: aggregate results
    
    par Log Usage
        Handler->>DB: log_usage(model1)
        Handler->>DB: log_usage(model2)
        Handler->>DB: log_usage(model3)
    end
    
    Handler-->>Server: comparison results
    Server-->>Client: JSON response
```

### Health Check Flow

```mermaid
flowchart TD
    A[Health Check Request] --> B{For Each Provider}
    B --> C[Ollama]
    B --> D[OpenAI]
    B --> E[Anthropic]
    B --> F[Google]
    B --> G[Mistral]
    
    C --> C1{Available?}
    D --> D1{Available?}
    E --> E1{Available?}
    F --> F1{Available?}
    G --> G1{Available?}
    
    C1 -->|Yes| C2[Check Models]
    C1 -->|No| C3[Status: Unavailable]
    D1 -->|Yes| D2[Verify API Key]
    D1 -->|No| D3[Status: Unavailable]
    E1 -->|Yes| E2[Verify API Key]
    E1 -->|No| E3[Status: Unavailable]
    F1 -->|Yes| F2[Verify API Key]
    F1 -->|No| F3[Status: Unavailable]
    G1 -->|Yes| G2[Verify API Key]
    G1 -->|No| G3[Status: Unavailable]
    
    C2 --> H[Aggregate Status]
    C3 --> H
    D2 --> H
    D3 --> H
    E2 --> H
    E3 --> H
    F2 --> H
    F3 --> H
    G2 --> H
    G3 --> H
    
    H --> I[Return Health Report]
    
    style A fill:#4A90E2
    style H fill:#50C878
    style I fill:#FFB347
```

---

## Sequence Diagrams

### Server Initialization

```mermaid
sequenceDiagram
    participant Main as main()
    participant Server as AIModelManagerServer
    participant Config as Config
    participant DB as Database
    participant Providers as Providers
    
    Main->>Server: __init__()
    Server->>Config: load configuration
    Config->>Config: read .env
    Config->>Config: load models.json
    Config-->>Server: config ready
    
    Server->>DB: Database(path)
    DB-->>Server: db instance
    
    Main->>Server: initialize()
    Server->>DB: initialize()
    DB->>DB: create tables
    DB-->>Server: ready
    
    Server->>Server: _initialize_providers()
    
    alt Ollama Configured
        Server->>Providers: OllamaProvider(config)
        Providers-->>Server: provider ready
    end
    
    alt OpenAI Configured
        Server->>Providers: OpenAIProvider(config)
        Providers-->>Server: provider ready
    end
    
    alt Anthropic Configured
        Server->>Providers: AnthropicProvider(config)
        Providers-->>Server: provider ready
    end
    
    alt Google Configured
        Server->>Providers: GoogleProvider(config)
        Providers-->>Server: provider ready
    end
    
    alt Mistral Configured
        Server->>Providers: MistralProvider(config)
        Providers-->>Server: provider ready
    end
    
    Server-->>Main: initialized
    Main->>Server: run()
    Server->>Server: start stdio server
```

### List Models Operation

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as MCP Server
    participant Handler as List Models Handler
    participant P1 as Ollama Provider
    participant P2 as OpenAI Provider
    participant P3 as Anthropic Provider
    
    Client->>Server: list_models(provider="ollama")
    Server->>Handler: _handle_list_models()
    Handler->>Handler: check provider filter
    
    alt No Filter
        Handler->>P1: list_models()
        Handler->>P2: list_models()
        Handler->>P3: list_models()
        P1-->>Handler: [models]
        P2-->>Handler: [models]
        P3-->>Handler: [models]
    else Provider Filter
        Handler->>P1: list_models()
        P1-->>Handler: [models]
    end
    
    Handler->>Handler: apply capability filter
    Handler->>Handler: format response
    Handler-->>Server: JSON model list
    Server-->>Client: TextContent response
```

### Save Conversation Operation

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as MCP Server
    participant Handler as Save Handler
    participant DB as Database
    
    Client->>Server: save_conversation(title, model, messages)
    Server->>Handler: _handle_save_conversation()
    Handler->>Handler: generate UUID
    Handler->>Handler: validate messages
    Handler->>DB: save_conversation()
    DB->>DB: INSERT INTO conversations
    DB->>DB: serialize messages to JSON
    DB-->>Handler: conversation_id
    Handler-->>Server: success message
    Server-->>Client: "Conversation saved with ID: xxx"
```

---

## Database Schema

```mermaid
erDiagram
    USAGE_STATS {
        integer id PK
        text model
        text provider
        integer input_tokens
        integer output_tokens
        integer total_tokens
        real cost
        real latency_ms
        text timestamp
        text metadata
    }
    
    CONVERSATIONS {
        text id PK
        text title
        text model
        text provider
        text messages
        text created_at
        text updated_at
        text metadata
    }
    
    API_KEYS {
        text provider PK
        text api_key
        text created_at
        text updated_at
    }
    
    MODEL_PREFERENCES {
        text user_id PK
        text preferred_model
        text preferred_provider
        text settings
        text updated_at
    }
    
    USAGE_STATS ||--o{ CONVERSATIONS : "tracks"
```

---

## Provider Integration Flow

### Provider Class Hierarchy

```mermaid
classDiagram
    class ModelProvider {
        <<abstract>>
        +name: str
        +config: Dict
        +list_models()* List~ModelInfo~
        +get_model_info(model_name)* ModelInfo
        +generate(request)* GenerationResponse
        +generate_stream(request)* AsyncIterator
        +is_available()* bool
        +health_check()* Dict
        +calculate_cost() float
    }
    
    class OllamaProvider {
        +base_url: str
        +list_models() List~ModelInfo~
        +generate(request) GenerationResponse
        +is_available() bool
    }
    
    class OpenAIProvider {
        +api_key: str
        +client: OpenAI
        +list_models() List~ModelInfo~
        +generate(request) GenerationResponse
        +is_available() bool
    }
    
    class AnthropicProvider {
        +api_key: str
        +client: Anthropic
        +list_models() List~ModelInfo~
        +generate(request) GenerationResponse
        +is_available() bool
    }
    
    class GoogleProvider {
        +api_key: str
        +list_models() List~ModelInfo~
        +generate(request) GenerationResponse
        +is_available() bool
    }
    
    class MistralProvider {
        +api_key: str
        +client: MistralClient
        +list_models() List~ModelInfo~
        +generate(request) GenerationResponse
        +is_available() bool
    }
    
    ModelProvider <|-- OllamaProvider
    ModelProvider <|-- OpenAIProvider
    ModelProvider <|-- AnthropicProvider
    ModelProvider <|-- GoogleProvider
    ModelProvider <|-- MistralProvider
```

### Data Models

```mermaid
classDiagram
    class ModelInfo {
        +name: str
        +display_name: str
        +provider: str
        +context_length: int
        +capabilities: List~ModelCapability~
        +cost_per_1k_input_tokens: float
        +cost_per_1k_output_tokens: float
        +is_local: bool
        +metadata: Dict
    }
    
    class GenerationRequest {
        +model: str
        +prompt: Optional~str~
        +messages: Optional~List~
        +max_tokens: Optional~int~
        +temperature: float
        +top_p: float
        +stream: bool
        +system_prompt: Optional~str~
        +stop_sequences: Optional~List~
        +metadata: Dict
    }
    
    class GenerationResponse {
        +model: str
        +content: str
        +provider: str
        +input_tokens: int
        +output_tokens: int
        +total_tokens: int
        +cost: float
        +latency_ms: float
        +finish_reason: Optional~str~
        +metadata: Dict
    }
    
    class UsageStats {
        +model: str
        +provider: str
        +total_requests: int
        +total_input_tokens: int
        +total_output_tokens: int
        +total_cost: float
        +average_latency_ms: float
        +error_count: int
        +last_used: Optional~str~
    }
    
    class ModelCapability {
        <<enumeration>>
        CHAT
        COMPLETION
        VISION
        FUNCTION_CALLING
        CODE
    }
    
    ModelInfo --> ModelCapability
    GenerationResponse --> UsageStats : aggregates to
```

---

## MCP Tools & Resources Flow

```mermaid
graph TB
    subgraph "MCP Tools"
        T1[list_models]
        T2[get_model_info]
        T3[generate]
        T4[compare_models]
        T5[get_usage_stats]
        T6[save_conversation]
        T7[list_conversations]
        T8[health_check]
    end
    
    subgraph "MCP Resources"
        R1[stats://usage]
        R2[config://providers]
    end
    
    subgraph "Handlers"
        H1[_handle_list_models]
        H2[_handle_get_model_info]
        H3[_handle_generate]
        H4[_handle_compare_models]
        H5[_handle_get_usage_stats]
        H6[_handle_save_conversation]
        H7[_handle_list_conversations]
        H8[_handle_health_check]
    end
    
    subgraph "Backend Operations"
        B1[Provider.list_models]
        B2[Provider.get_model_info]
        B3[Provider.generate]
        B4[Database.log_usage]
        B5[Database.get_stats]
        B6[Database.save_conversation]
        B7[Database.list_conversations]
        B8[Provider.health_check]
    end
    
    T1 --> H1 --> B1
    T2 --> H2 --> B2
    T3 --> H3 --> B3
    T3 --> H3 --> B4
    T4 --> H4 --> B3
    T4 --> H4 --> B4
    T5 --> H5 --> B5
    T6 --> H6 --> B6
    T7 --> H7 --> B7
    T8 --> H8 --> B8
    
    R1 --> B5
    R2 --> B8
    
    style T3 fill:#4A90E2
    style T4 fill:#4A90E2
    style H3 fill:#50C878
    style H4 fill:#50C878
    style B3 fill:#FFB347
    style B4 fill:#FFB347
```

---

## Cost Tracking Flow

```mermaid
flowchart TD
    A[Generation Request] --> B[Provider.generate]
    B --> C{Is Local Model?}
    
    C -->|Yes Ollama| D[Cost = $0.00]
    C -->|No Cloud API| E[Get Model Info]
    
    E --> F[Calculate Input Cost]
    E --> G[Calculate Output Cost]
    
    F --> H[input_tokens / 1000 * cost_per_1k_input]
    G --> I[output_tokens / 1000 * cost_per_1k_output]
    
    H --> J[Total Cost = Input + Output]
    I --> J
    D --> J
    
    J --> K[Create GenerationResponse]
    K --> L{Track Costs Enabled?}
    
    L -->|Yes| M[Database.log_usage]
    L -->|No| N[Skip Logging]
    
    M --> O[Store in usage_stats table]
    N --> P[Return Response]
    O --> P
    
    style A fill:#4A90E2
    style J fill:#50C878
    style O fill:#FFB347
    style P fill:#DDA0DD
```

---

## Configuration Management

```mermaid
flowchart LR
    subgraph "Configuration Sources"
        A[.env file]
        B[models.json]
        C[Environment Variables]
    end
    
    subgraph "Config Class"
        D[Config Manager]
        E[Provider Configs]
        F[Model Definitions]
        G[Database Path]
    end
    
    subgraph "Consumers"
        H[Server Initialization]
        I[Provider Initialization]
        J[Database Setup]
        K[Cost Calculation]
    end
    
    A --> D
    B --> D
    C --> D
    
    D --> E
    D --> F
    D --> G
    
    E --> I
    F --> K
    G --> J
    D --> H
    
    style D fill:#4A90E2
    style E fill:#50C878
    style F fill:#50C878
    style G fill:#50C878
```

---

## Error Handling Flow

```mermaid
flowchart TD
    A[Tool Call] --> B{Validate Input}
    B -->|Invalid| C[Return Error Message]
    B -->|Valid| D{Provider Available?}
    
    D -->|No| E[Return Provider Not Found]
    D -->|Yes| F[Execute Provider Call]
    
    F --> G{API Call Success?}
    G -->|No| H{Retry?}
    G -->|Yes| I[Process Response]
    
    H -->|Yes| J[Exponential Backoff]
    H -->|No| K[Log Error]
    
    J --> F
    K --> L[Return Error Response]
    
    I --> M{Database Available?}
    M -->|Yes| N[Log Usage]
    M -->|No| O[Skip Logging]
    
    N --> P[Return Success]
    O --> P
    
    style A fill:#4A90E2
    style F fill:#50C878
    style K fill:#FF6B6B
    style P fill:#51CF66
```

---

## Future Enhancements Architecture

```mermaid
graph TB
    subgraph "Current Architecture"
        A[MCP Server]
        B[Provider Manager]
        C[Database]
    end
    
    subgraph "Smart Routing Future"
        D[Task Analyzer]
        E[Cost Optimizer]
        F[Performance Tracker]
        G[Load Balancer]
    end
    
    subgraph "Advanced Features Future"
        H[Fine-tuning Manager]
        I[Batch Processor]
        J[Streaming Aggregator]
        K[Real-time Dashboard]
    end
    
    subgraph "Scalability Future"
        L[Multi-instance Support]
        M[Distributed Cache]
        N[Message Queue]
        O[Horizontal Scaling]
    end
    
    A --> D
    B --> D
    D --> E
    D --> F
    D --> G
    
    A --> H
    A --> I
    A --> J
    A --> K
    
    B --> L
    C --> M
    A --> N
    N --> O
    
    style D fill:#FFD93D
    style E fill:#FFD93D
    style H fill:#6BCF7F
    style L fill:#A8DADC
```

---

## Summary

This visual architecture documentation provides:

1. **System Architecture**: High-level overview of all components and their interactions
2. **Component Architecture**: Detailed view of the codebase structure
3. **Data Flow Diagrams**: How data moves through the system
4. **Sequence Diagrams**: Step-by-step operation flows
5. **Database Schema**: Data persistence structure
6. **Provider Integration**: How different AI providers are integrated
7. **Cost Tracking**: How costs are calculated and logged
8. **Configuration Management**: How settings are managed
9. **Error Handling**: How errors are caught and handled
10. **Future Enhancements**: Planned architectural improvements

All diagrams use Mermaid syntax and can be rendered in GitHub, VS Code, or any Mermaid-compatible viewer.