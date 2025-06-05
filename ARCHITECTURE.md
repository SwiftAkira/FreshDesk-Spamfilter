# System Architecture

## Overview

The Freshdesk Spam Filter is a modular, AI-powered system designed to automatically detect and handle spam tickets in Freshdesk using the OpenAI API. The architecture follows a clean separation of concerns with distinct layers for API integration, AI processing, and business logic.

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
│  │   Freshdesk Client  │  │        OpenAI Client            │  │
│  │  • API Integration  │  │  • OpenAI API Communication    │  │
│  │  • Ticket Fetching  │  │  • Spam Analysis               │  │
│  │  • Action Execution │  │  • Confidence Scoring          │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │   Freshdesk API     │  │        OpenAI API               │  │
│  │   (External)        │  │        (External)               │  │
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
  - Scheduling and continuous operation (for local execution)
  - Lambda handler (`lambda_function.py`) for AWS deployment
  - User interface and reporting (for local execution)
- **Dependencies**: All other components

#### Configuration Management (`config.py`)
- **Purpose**: Centralized configuration handling
- **Responsibilities**:
  - Environment variable loading (from `.env` locally or Lambda environment)
  - Configuration validation
  - Default value management
  - Type conversion and validation
- **Dependencies**: `python-dotenv`

#### Spam Filter Engine (`spam_filter.py`)
- **Purpose**: Core business logic for spam detection
- **Responsibilities**:
  - Ticket processing orchestration (batch for local, single for Lambda)
  - Spam detection workflow
  - Action decision making
  - Statistics tracking
- **Dependencies**: `freshdesk_client`, `openai_client`, `config`

### 2. Integration Components

#### Freshdesk Client (`freshdesk_client.py`)
- **Purpose**: Freshdesk API integration layer
- **Responsibilities**:
  - HTTP API communication
  - Ticket fetching and filtering
  - Conversation extraction
  - Ticket updates, tagging, and note addition
- **Dependencies**: `requests`, `config`

#### OpenAI Client (`openai_client.py`)
- **Purpose**: OpenAI API integration layer
- **Responsibilities**:
  - OpenAI API communication
  - Prompt engineering for spam detection
  - Response parsing (expecting JSON for spam score and reasoning)
  - Error handling for API calls
- **Dependencies**: `openai`, `config`

## Data Flow

### 1. Ticket Processing Flow (Conceptual - varies for local vs Lambda)

```
External Trigger (Freshdesk Webhook for Lambda / Scheduler for Local)
           │
           ▼
┌─────────────────┐    ┌─────────────────┐
│  Main/Lambda    │───▶│  Spam Filter    │
│  Handler        │    │  Engine         │
└─────────────────┘    └─────────────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ Freshdesk Client│    │ OpenAI Client   │
└─────────────────┘    └─────────────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ Freshdesk API   │    │ OpenAI API      │
└─────────────────┘    └─────────────────┘
```

### 2. Detailed Processing Sequence (Illustrative for a single ticket)

1. **Ticket Ingestion**:
   - **Lambda**: API Gateway receives Freshdesk webhook data, triggers `lambda_function.lambda_handler`.
   - **Local**: `Scheduler` triggers `SpamFilter.process_tickets()`.
   - `SpamFilter` receives/fetches ticket data.

2. **Message Extraction** (if applicable, for context):
   ```
   SpamFilter → FreshdeskClient.get_first_customer_message() (or uses provided description)
   FreshdeskClient → Freshdesk API (if full details needed)
   ```

3. **Spam Analysis**:
   ```
   SpamFilter → OpenAIClient.analyze_spam(subject, description, sender_email, is_system_validated)
   OpenAIClient → OpenAI API (chat completion with spam detection prompt)
   OpenAIClient → Parse JSON response (is_spam, confidence, reasoning)
   ```

4. **Action Execution**:
   ```
   SpamFilter determines action based on confidence and thresholds.
   SpamFilter → FreshdeskClient.add_note_to_ticket()
   SpamFilter → FreshdeskClient.mark_as_spam() (assign agent, set tags, set status)
   FreshdeskClient → Freshdesk API (POST for notes, PUT for ticket updates)
   ```

## Security Architecture

### 1. Authentication & Authorization
- **Freshdesk**: API key-based authentication.
- **OpenAI**: API key-based authentication.
- **Credentials**: Stored in environment variables (`.env` locally, Lambda environment variables in AWS).

### 2. Data Privacy
- **OpenAI API**: Ticket subject, description, and sender email are sent to the OpenAI API for analysis. Review OpenAI's data usage and privacy policies.
- **Minimal Data Retention**: The application itself does not persistently store ticket content beyond processing.

### 3. Security Best Practices
- Environment variable configuration for secrets.
- Input validation (primarily on configuration).
- Error handling without sensitive data exposure in logs.
- Secure HTTP communication (HTTPS) for all external API calls.

## Scalability Considerations

### 1. Performance Characteristics (OpenAI API dependent)
- **Throughput**: Dependent on OpenAI API response times and rate limits for the chosen model.
- **Memory Usage**: Primarily for Python application logic; AI model memory is managed by OpenAI.
- **CPU Usage**: Low for the application itself; primary computation is offloaded to OpenAI.

### 2. Scaling Strategies
- **Lambda**: AWS Lambda scales automatically based on incoming request volume (webhook triggers).
- **OpenAI Model Selection**: Choose different OpenAI models based on cost, speed, and accuracy requirements.
- **Batch Processing (Local)**: Configurable batch sizes for local execution.

### 3. Bottlenecks
- **OpenAI API**: Latency, rate limits, or availability issues.
- **Freshdesk API**: Rate limits (see API documentation).
- **Network Latency**: API call overhead for both services.

## Error Handling Strategy

### 1. Error Categories
- **Configuration Errors**: Missing or invalid settings.
- **Network Errors**: API connectivity issues to Freshdesk or OpenAI.
- **AI Errors**: OpenAI API errors (e.g., authentication, rate limits, model issues, invalid responses).
- **Business Logic Errors**: Unexpected data formats or workflow issues.

### 2. Recovery Mechanisms
- **Retry Logic**: Implemented for some API calls (e.g., initial Freshdesk ticket fetch).
- **Graceful Degradation**: Continue processing other tickets on single failures (in batch mode).
- **Logging**: Comprehensive error logging for debugging, including API error responses where available.

## Monitoring & Observability (Primarily via AWS CloudWatch for Lambda)

### 1. Metrics
- Lambda invocations, duration, error rates.
- API Gateway metrics (requests, latency, errors).
- Custom metrics can be added (e.g., spam detected count).

### 2. Logging
- Structured logging with levels, output to AWS CloudWatch Logs.
- Request/response logging for debugging critical API interactions.
- Performance metrics from Lambda.

### 3. Health Checks (Conceptual)
- OpenAI API accessibility (indirectly checked on each call).
- Freshdesk API accessibility (indirectly checked on each call).
- Configuration validation at startup/invocation.

## Extension Points

### 1. New AI Providers/Models
- Create a new client class similar to `OpenAIClient` implementing a common analysis interface.
- Update `SpamFilter` to use the new client.
- Add model-specific configuration.
- Adapt prompt engineering as needed.

### 2. Additional Actions
- Extend `SpamFilter.handle_spam_ticket()` or add new methods.
- Add new action types (e.g., sending notifications, escalating).
- Implement custom workflows.

### 3. Multiple Ticketing Platforms
- Create new client classes (e.g., `ZendeskClient`) for the target platform's API.
- Implement a common interface for ticket operations.
- Add platform-specific configuration.

## Technology Stack

### Core Technologies
- **Python 3.8+**: Main programming language.
- **OpenAI API**: Cloud-based AI service for spam analysis.
- **Freshdesk API v2**: Ticket management platform.
- **AWS Lambda & API Gateway** (for deployed version).

### Key Dependencies
- **requests**: HTTP client for Freshdesk API communication.
- **openai**: OpenAI Python client.
- **python-dotenv**: Environment variable management (for local execution).
- **colorama**: Terminal color output (for local execution).
- **schedule**: Task scheduling (for local continuous mode).

### Development Tools
- **pytest**: Testing framework.
- **Git & GitHub**: Version control.
- Standard Python linters/formatters (e.g., Black, Flake8).
