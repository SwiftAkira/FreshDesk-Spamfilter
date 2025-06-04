# System Architecture

## Overview

The Freshdesk Spam Filter is a modular, AI-powered system designed to automatically detect and handle spam tickets in Freshdesk using local OLLAMA models. The architecture follows a clean separation of concerns with distinct layers for API integration, AI processing, and business logic.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Freshdesk Spam Filter                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    Main     │  │   Config    │  │    Logging &        │  │
│  │ Application │  │ Management  │  │   Monitoring        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Spam Filter Engine                         │  │
│  │  • Ticket Processing Logic                              │  │
│  │  • Spam Detection Orchestration                        │  │
│  │  • Action Handling                                     │  │
│  └─────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │   Freshdesk Client  │  │        OLLAMA Client            │  │
│  │  • API Integration  │  │  • AI Model Communication      │  │
│  │  • Ticket Fetching  │  │  • Spam Analysis               │  │
│  │  • Action Execution │  │  • Confidence Scoring          │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │   Freshdesk API     │  │        OLLAMA Server            │  │
│  │   (External)        │  │        (Local)                  │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Core Components

#### Main Application (`main.py`)
- **Purpose**: Application entry point and orchestration
- **Responsibilities**:
  - Command-line interface handling
  - Configuration validation
  - Scheduling and continuous operation
  - User interface and reporting
- **Dependencies**: All other components

#### Configuration Management (`config.py`)
- **Purpose**: Centralized configuration handling
- **Responsibilities**:
  - Environment variable loading
  - Configuration validation
  - Default value management
  - Type conversion and validation
- **Dependencies**: `python-dotenv`

#### Spam Filter Engine (`spam_filter.py`)
- **Purpose**: Core business logic for spam detection
- **Responsibilities**:
  - Ticket processing orchestration
  - Spam detection workflow
  - Action decision making
  - Statistics tracking
- **Dependencies**: `freshdesk_client`, `ollama_client`, `config`

### 2. Integration Components

#### Freshdesk Client (`freshdesk_client.py`)
- **Purpose**: Freshdesk API integration layer
- **Responsibilities**:
  - HTTP API communication
  - Ticket fetching and filtering
  - Conversation extraction
  - Ticket updates and tagging
- **Dependencies**: `requests`, `config`

#### OLLAMA Client (`ollama_client.py`)
- **Purpose**: AI model integration layer
- **Responsibilities**:
  - OLLAMA server communication
  - Prompt engineering
  - Response parsing
  - Error handling
- **Dependencies**: `ollama`, `config`

## Data Flow

### 1. Ticket Processing Flow

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Scheduler │───▶│  Spam Filter    │───▶│  Freshdesk      │
│             │    │  Engine         │    │  Client         │
└─────────────┘    └─────────────────┘    └─────────────────┘
                            │                       │
                            ▼                       ▼
                   ┌─────────────────┐    ┌─────────────────┐
                   │  OLLAMA Client  │    │  Freshdesk API  │
                   └─────────────────┘    └─────────────────┘
                            │                       │
                            ▼                       ▼
                   ┌─────────────────┐    ┌─────────────────┐
                   │  OLLAMA Server  │    │  New Tickets    │
                   └─────────────────┘    └─────────────────┘
```

### 2. Detailed Processing Sequence

1. **Ticket Fetching**:
   ```
   Scheduler → SpamFilter.process_tickets()
   SpamFilter → FreshdeskClient.get_tickets(only_new=True)
   FreshdeskClient → Freshdesk API (/api/v2/tickets)
   ```

2. **Message Extraction**:
   ```
   SpamFilter → FreshdeskClient.get_first_customer_message()
   FreshdeskClient → Freshdesk API (/api/v2/tickets/{id}/conversations)
   FreshdeskClient → Filter for first customer message
   ```

3. **Spam Analysis**:
   ```
   SpamFilter → OllamaClient.analyze_spam()
   OllamaClient → OLLAMA Server (chat completion)
   OllamaClient → Parse JSON response
   ```

4. **Action Execution**:
   ```
   SpamFilter → FreshdeskClient.add_tag_to_ticket()
   SpamFilter → FreshdeskClient.mark_as_spam() (if high confidence)
   FreshdeskClient → Freshdesk API (PUT /api/v2/tickets/{id})
   ```

## Security Architecture

### 1. Authentication & Authorization
- **Freshdesk**: API key-based authentication
- **OLLAMA**: Local server (no authentication required)
- **Credentials**: Stored in environment variables only

### 2. Data Privacy
- **Local Processing**: All AI analysis happens locally via OLLAMA
- **No External Data Sharing**: Ticket content never leaves your infrastructure
- **Minimal Data Retention**: No persistent storage of ticket content

### 3. Security Best Practices
- Environment variable configuration
- Input validation and sanitization
- Error handling without data exposure
- Secure HTTP communication (HTTPS only for Freshdesk)

## Scalability Considerations

### 1. Performance Characteristics
- **Throughput**: ~10-50 tickets per minute (depending on AI model)
- **Memory Usage**: ~1-4GB (depending on OLLAMA model)
- **CPU Usage**: Moderate (AI inference is primary load)

### 2. Scaling Strategies
- **Horizontal**: Multiple instances with different Freshdesk domains
- **Vertical**: Larger OLLAMA models for better accuracy
- **Batch Processing**: Configurable batch sizes for optimal performance

### 3. Bottlenecks
- **OLLAMA Inference**: AI model processing time
- **Freshdesk API**: Rate limits (see API documentation)
- **Network Latency**: API call overhead

## Error Handling Strategy

### 1. Error Categories
- **Configuration Errors**: Missing or invalid settings
- **Network Errors**: API connectivity issues
- **AI Errors**: OLLAMA server problems
- **Business Logic Errors**: Unexpected data formats

### 2. Recovery Mechanisms
- **Retry Logic**: Automatic retries for transient failures
- **Graceful Degradation**: Continue processing other tickets on single failures
- **Circuit Breaker**: Stop processing on repeated failures
- **Logging**: Comprehensive error logging for debugging

## Monitoring & Observability

### 1. Metrics
- Tickets processed per hour
- Spam detection accuracy
- Processing time per ticket
- Error rates by component

### 2. Logging
- Structured logging with levels
- Request/response logging for debugging
- Performance metrics
- Security events

### 3. Health Checks
- OLLAMA server connectivity
- Freshdesk API accessibility
- Configuration validation
- Model availability

## Extension Points

### 1. New AI Models
- Implement `OllamaClient` interface
- Add model-specific configuration
- Update prompt engineering

### 2. Additional Actions
- Extend `SpamFilter.handle_spam_ticket()`
- Add new action types
- Implement custom workflows

### 3. Multiple Platforms
- Create new client classes (e.g., `ZendeskClient`)
- Implement common interface
- Add platform-specific configuration

## Technology Stack

### Core Technologies
- **Python 3.8+**: Main programming language
- **OLLAMA**: Local AI model server
- **Freshdesk API v2**: Ticket management platform

### Key Dependencies
- **requests**: HTTP client for API communication
- **ollama**: OLLAMA Python client
- **python-dotenv**: Environment variable management
- **colorama**: Terminal color output
- **schedule**: Task scheduling

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking
- **flake8**: Linting
