# API Reference

## Overview

This document provides detailed API documentation for all classes and methods in the Freshdesk Spam Filter system.

## Core Classes

### `Config`

Configuration management class that handles environment variables and application settings.

**Location**: `config.py`

#### Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `FRESHDESK_DOMAIN` | `str` | `None` | Freshdesk subdomain (e.g., `yourcompany`) |
| `FRESHDESK_API_KEY` | `str` | `None` | Freshdesk API key for authentication |
| `OPENAI_API_KEY` | `str` | `None` | OpenAI API Key |
| `OPENAI_MODEL_NAME` | `str` | `gpt-3.5-turbo` | OpenAI model name to use |
| `SPAM_THRESHOLD` | `float` | `0.7` | Confidence threshold for initial spam detection |
| `AUTO_CLOSE_SPAM_THRESHOLD` | `float` | `0.75` | Confidence threshold to automatically close a ticket as spam |
| `AGENT_ID_TO_ASSIGN_SPAM` | `int` | `None` | (Optional via env) Agent ID to assign spam tickets to before closing |
| `CHECK_INTERVAL_MINUTES` | `int` | `5` | Minutes between processing cycles (local continuous mode) |
| `MAX_TICKETS_PER_BATCH` | `int` | `50` | Maximum tickets to process per batch (local continuous mode) |
| `PROCESS_NEW_TICKETS_ONLY` | `bool` | `True` | Whether to process only new tickets |
| `LOG_LEVEL` | `str` | `INFO` | Logging level |
| `DRY_RUN_MODE` | `bool` | `False` | If True, no actual changes are made to Freshdesk |
| `IS_LAMBDA_ENVIRONMENT` | `bool` | `False` | True if running in AWS Lambda environment |

#### Methods

##### `validate() -> bool`
Validates that all required configuration is present.

**Returns**: `True` if configuration is valid

**Raises**: `ValueError` if required fields are missing

**Example**:
```python
try:
    Config.validate()
    print("Configuration is valid")
except ValueError as e:
    print(f"Configuration error: {e}")
```

##### `get_freshdesk_url() -> str`
Constructs the base Freshdesk API URL.

**Returns**: Base API URL (e.g., `https://yourcompany.freshdesk.com/api/v2`)

**Raises**: `ValueError` if `FRESHDESK_DOMAIN` is not configured

---

### `FreshdeskClient`

Client for interacting with the Freshdesk API.

**Location**: `freshdesk_client.py`

#### Constructor

```python
FreshdeskClient()
```

Initializes the client with configuration from `Config` class.

#### Methods

##### `get_tickets(status: Optional[str] = None, limit: int = 50, only_new: bool = True) -> List[Dict]`

Fetches tickets from Freshdesk with optional filtering.

**Parameters**:
- `status` (Optional[str]): Filter by ticket status ('open', 'pending', 'resolved')
- `limit` (int): Maximum number of tickets to fetch (max 100)
- `only_new` (bool): If True, only fetch newly opened tickets (status 2)

**Returns**: List of ticket dictionaries

**Raises**: `requests.exceptions.RequestException` on API errors

**Example**:
```python
client = FreshdeskClient()
new_tickets = client.get_tickets(only_new=True, limit=10)
```

##### `get_ticket(ticket_id: int) -> Dict`

Fetches a specific ticket by ID. Attempts to get description, retries without if initial attempt fails.

**Parameters**:
- `ticket_id` (int): The ticket ID to fetch

**Returns**: Ticket dictionary

**Raises**: `requests.exceptions.RequestException` on API errors

##### `get_ticket_conversations(ticket_id: int) -> List[Dict]`

Fetches all conversations for a specific ticket.

**Parameters**:
- `ticket_id` (int): The ticket ID

**Returns**: List of conversation dictionaries

**Raises**: `requests.exceptions.RequestException` on API errors

##### `get_first_customer_message(ticket_id: int) -> Dict`

Extracts the first customer message from a ticket, ignoring agent responses.

**Parameters**:
- `ticket_id` (int): The ticket ID

**Returns**: Dictionary containing:
- `ticket_id` (int): The ticket ID
- `subject` (str): Ticket subject
- `description` (str): First customer message content
- `sender_email` (str): Sender identifier (requester_id)
- `created_at` (str): Message timestamp
- `conversation_id` (Optional[int]): Conversation ID if found

**Raises**: `Exception` on processing errors

##### `update_ticket(ticket_id: int, updates: Dict) -> Dict`

Updates a ticket with new information.

**Parameters**:
- `ticket_id` (int): The ticket ID to update
- `updates` (Dict): Dictionary of fields to update

**Returns**: Updated ticket dictionary

**Raises**: `requests.exceptions.RequestException` on API errors (logs detailed error from response)

##### `add_tag_to_ticket(ticket_id: int, tag: str) -> Dict`

Adds a specific tag to a ticket if it's not already present.

**Parameters**:
- `ticket_id` (int): The ticket ID
- `tag` (str): Tag to add

**Returns**: Updated ticket dictionary

**Raises**: `Exception` on processing errors

##### `mark_as_spam(ticket_id: int) -> Dict`

Marks a ticket as spam. Performs a sequence of operations:
1. Assigns to a pre-configured agent (Agent ID `80059226092` or from `Config.AGENT_ID_TO_ASSIGN_SPAM`).
2. Sets tags exclusively to `['Auto-Spam-Detected']`.
3. Sets status to 5 (Closed/Spam).

**Parameters**:
- `ticket_id` (int): The ticket ID to mark as spam

**Returns**: Updated ticket dictionary

**Raises**: `Exception` on processing errors

##### `add_note_to_ticket(ticket_id: int, note_body: str, private: bool = True) -> Dict`

Adds a note to a ticket.

**Parameters**:
- `ticket_id` (int): The ticket ID.
- `note_body` (str): The content of the note.
- `private` (bool): Whether the note should be private (default `True`).

**Returns**: The API response dictionary for the created note.

**Raises**: `requests.exceptions.RequestException` on API errors.

---

### `OpenAIClient`

Client for interacting with the OpenAI API for spam detection.

**Location**: `openai_client.py`

#### Constructor

```python
OpenAIClient()
```

Initializes the client with OpenAI API key and model from `Config`.

#### Methods

##### `analyze_spam(subject: str, description: str, sender_email: str = "", is_system_validated: bool = False) -> Tuple[bool, float, str]`

Analyzes ticket content for spam using the OpenAI API.

**Parameters**:
- `subject` (str): Ticket subject.
- `description` (str): Ticket description/content.
- `sender_email` (str): Sender's email address (optional).
- `is_system_validated` (bool): Flag indicating if the ticket contains a system validation phrase.

**Returns**: Tuple containing:
- `is_spam` (bool): Whether content is classified as spam by the AI.
- `confidence` (float): Confidence score (0.0-1.0) from the AI's response.
- `reasoning` (str): AI's explanation for the decision.

**Raises**: `Exception` on AI processing errors or if the API response is not in the expected JSON format.

**Example**:
```python
client = OpenAIClient()
is_spam, confidence, reasoning = client.analyze_spam(
    subject="Help with login",
    description="I can't access my account",
    sender_email="user@example.com",
    is_system_validated=False
)
```

---

### `SpamFilter`

Main spam filtering service that orchestrates the detection process.

**Location**: `spam_filter.py`

#### Constructor

```python
SpamFilter()
```

Initializes the spam filter with `FreshdeskClient` and `OpenAIClient` instances.

#### Methods

##### `process_tickets(limit: Optional[int] = None) -> Dict[str, int]`

Processes a batch of tickets for spam detection based on configuration (new or all open tickets).
Intended for local continuous execution.

**Parameters**:
- `limit` (Optional[int]): Maximum number of tickets to process in this batch.

**Returns**: Dictionary with processing statistics:
- `total_processed` (int): Number of tickets analyzed in this batch.
- `spam_detected` (int): Number of spam tickets found.
- `legitimate` (int): Number of legitimate tickets.
- `errors` (int): Number of processing errors in this batch.
- `skipped_already_processed` (int): Number of tickets skipped because they were already processed in this run cycle.

**Example**:
```python
spam_filter = SpamFilter()
stats = spam_filter.process_tickets(limit=10)
print(f"Processed {stats['total_processed']} tickets")
```

##### `process_single_ticket_data(ticket_data: Dict) -> Dict`

Processes a single ticket provided as a dictionary (e.g., from a Lambda event).

**Parameters**:
- `ticket_data` (Dict): Dictionary containing the ticket details (ID, subject, description, etc.).

**Returns**: Dictionary with analysis result for the single ticket, including `is_spam`, `confidence`, `reasoning`.

##### `analyze_ticket(ticket: Dict) -> Dict`

Analyzes a single ticket for spam. (Note: `analyze_first_customer_message` or direct call to `OpenAIClient` via `handle_spam_ticket` is typically used more directly now).

**Parameters**:
- `ticket` (Dict): Ticket dictionary from Freshdesk.

**Returns**: Analysis result dictionary.

##### `analyze_first_customer_message(message_data: Dict) -> Dict`

Analyzes the first customer message (extracted by `FreshdeskClient`) for spam.

**Parameters**:
- `message_data` (Dict): Dictionary containing details of the first customer message.

**Returns**: Analysis result dictionary.

##### `handle_spam_ticket(ticket_id: int, analysis_result: Dict)`

Internal method to handle a ticket identified as spam. It adds tags, notes, and potentially closes the ticket based on confidence scores and configuration. Checks for duplicate notes before adding a new one.

**Parameters**:
- `ticket_id` (int): The ID of the spam ticket.
- `analysis_result` (Dict): The result from `analyze_spam` containing confidence and reasoning.

##### `get_spam_statistics() -> Dict`

Fetches overall spam statistics from Freshdesk (e.g., total tickets, spam tagged tickets).

**Returns**: Dictionary with spam statistics or an error message.

## Error Handling

### Exception Types

All methods may raise the following exceptions:

- **`ValueError`**: Invalid configuration or parameters
- **`requests.exceptions.RequestException`**: HTTP/API communication errors
- **`ConnectionError`**: Network connectivity issues
- **`TimeoutError`**: Request timeout errors
- **`Exception`**: General processing errors

### Error Response Format

API methods return error information in the following format:

```python
{
    'error': str,           # Error message
    'ticket_id': int,       # Relevant ticket ID (if applicable)
    'timestamp': str,       # Error timestamp
    'component': str        # Component that generated the error
}
```

## Usage Examples

### Basic Usage

```python
from spam_filter import SpamFilter
from config import Config

# Validate configuration
Config.validate()

# Initialize and run spam filter
spam_filter = SpamFilter()
results = spam_filter.process_tickets()

print(f"Spam detected: {results['spam_detected']}")
```

### Custom Processing

```python
from freshdesk_client import FreshdeskClient
from ollama_client import OllamaClient

# Initialize clients
freshdesk = FreshdeskClient()
ollama = OllamaClient()

# Get specific ticket
ticket = freshdesk.get_ticket(12345)

# Analyze for spam
is_spam, confidence, reasoning = ollama.analyze_spam(
    subject=ticket['subject'],
    description=ticket['description'],
    sender_email=ticket.get('requester_email', '')
)

if is_spam and confidence > 0.8:
    freshdesk.mark_as_spam(ticket['id'])
```

### Batch Processing

```python
spam_filter = SpamFilter()

# Process in smaller batches
for batch_num in range(5):
    results = spam_filter.process_tickets(limit=10)
    print(f"Batch {batch_num + 1}: {results}")

    if results['errors'] > 0:
        print("Errors detected, stopping processing")
        break
```

## Rate Limiting

### Freshdesk API Limits
- **Rate Limit**: Varies by plan (see Freshdesk documentation)
- **Recommended**: 50-100 requests per minute
- **Headers**: Check `X-RateLimit-Remaining` in responses

### OLLAMA Limits
- **Concurrent Requests**: Limited by server resources
- **Model Loading**: First request may be slower
- **Memory**: Depends on model size

## Testing

### Unit Tests
```python
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_spam_filter.py

# Run with coverage
python -m pytest --cov=. tests/
```

### Integration Tests
```python
# Test with mock data
python test_ai_spam_detection.py

# Test edge cases
python test_edge_cases.py

# Test AI independence
python test_ai_independence.py
```
