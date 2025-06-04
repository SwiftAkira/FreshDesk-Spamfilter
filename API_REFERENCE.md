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
| `FRESHDESK_DOMAIN` | `str` | `None` | Freshdesk domain (e.g., company.freshdesk.com) |
| `FRESHDESK_API_KEY` | `str` | `None` | Freshdesk API key for authentication |
| `OLLAMA_HOST` | `str` | `http://localhost:11434` | OLLAMA server URL |
| `OLLAMA_MODEL` | `str` | `llama3.2` | AI model name to use |
| `SPAM_THRESHOLD` | `float` | `0.7` | Confidence threshold for spam detection |
| `CHECK_INTERVAL_MINUTES` | `int` | `5` | Minutes between processing cycles |
| `MAX_TICKETS_PER_BATCH` | `int` | `50` | Maximum tickets to process per batch |
| `PROCESS_NEW_TICKETS_ONLY` | `bool` | `True` | Whether to process only new tickets |
| `LOG_LEVEL` | `str` | `INFO` | Logging level |

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

**Returns**: Base API URL (e.g., `https://company.freshdesk.com/api/v2`)

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

Fetches a specific ticket by ID.

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
- `sender_email` (str): Sender identifier
- `created_at` (str): Message timestamp
- `conversation_id` (Optional[int]): Conversation ID if found

**Raises**: `Exception` on processing errors

##### `update_ticket(ticket_id: int, updates: Dict) -> Dict`

Updates a ticket with new information.

**Parameters**:
- `ticket_id` (int): The ticket ID to update
- `updates` (Dict): Dictionary of fields to update

**Returns**: Updated ticket dictionary

**Raises**: `requests.exceptions.RequestException` on API errors

##### `add_tag_to_ticket(ticket_id: int, tag: str) -> Dict`

Adds a tag to a ticket.

**Parameters**:
- `ticket_id` (int): The ticket ID
- `tag` (str): Tag to add

**Returns**: Updated ticket dictionary

**Raises**: `Exception` on processing errors

##### `mark_as_spam(ticket_id: int) -> Dict`

Marks a ticket as spam by updating status and adding tags.

**Parameters**:
- `ticket_id` (int): The ticket ID to mark as spam

**Returns**: Updated ticket dictionary

**Raises**: `Exception` on processing errors

---

### `OllamaClient`

Client for interacting with OLLAMA AI models for spam detection.

**Location**: `ollama_client.py`

#### Constructor

```python
OllamaClient()
```

Initializes the client and tests connection to OLLAMA server.

#### Methods

##### `analyze_spam(subject: str, description: str, sender_email: str = "") -> Tuple[bool, float, str]`

Analyzes ticket content for spam using AI.

**Parameters**:
- `subject` (str): Ticket subject
- `description` (str): Ticket description/content
- `sender_email` (str): Sender's email address (optional)

**Returns**: Tuple containing:
- `is_spam` (bool): Whether content is classified as spam
- `confidence` (float): Confidence score (0.0-1.0)
- `reasoning` (str): AI's explanation for the decision

**Raises**: `Exception` on AI processing errors

**Example**:
```python
client = OllamaClient()
is_spam, confidence, reasoning = client.analyze_spam(
    subject="Help with login",
    description="I can't access my account",
    sender_email="user@example.com"
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

Initializes the spam filter with Freshdesk and OLLAMA clients.

#### Methods

##### `process_tickets(limit: Optional[int] = None) -> Dict[str, int]`

Processes tickets for spam detection.

**Parameters**:
- `limit` (Optional[int]): Maximum number of tickets to process

**Returns**: Dictionary with processing statistics:
- `total_processed` (int): Number of tickets analyzed
- `spam_detected` (int): Number of spam tickets found
- `legitimate` (int): Number of legitimate tickets
- `errors` (int): Number of processing errors
- `skipped_already_processed` (int): Number of already processed tickets

**Example**:
```python
spam_filter = SpamFilter()
stats = spam_filter.process_tickets(limit=10)
print(f"Processed {stats['total_processed']} tickets")
```

##### `analyze_ticket(ticket: Dict) -> Dict`

Analyzes a single ticket for spam (legacy method).

**Parameters**:
- `ticket` (Dict): Ticket dictionary from Freshdesk

**Returns**: Analysis result dictionary

##### `analyze_first_customer_message(message_data: Dict) -> Dict`

Analyzes the first customer message for spam.

**Parameters**:
- `message_data` (Dict): First customer message data

**Returns**: Analysis result dictionary containing:
- `ticket_id` (int): The ticket ID
- `is_spam` (bool): Whether message is spam
- `confidence` (float): Confidence score
- `reasoning` (str): AI's reasoning
- `subject` (str): Ticket subject
- `message_type` (str): Type of message analyzed

##### `handle_spam_ticket(ticket_id: int, analysis_result: Dict) -> None`

Handles a ticket that has been identified as spam.

**Parameters**:
- `ticket_id` (int): The ticket ID
- `analysis_result` (Dict): The spam analysis result

**Actions Performed**:
- Adds 'auto-spam-detected' tag
- For high confidence (≥0.9): Marks ticket as spam and closes it
- For medium confidence: Adds 'needs-spam-review' tag

##### `get_spam_statistics() -> Dict`

Gets statistics about spam detection.

**Returns**: Dictionary with statistics:
- `total_tickets_checked` (int): Total tickets in system
- `spam_tagged_tickets` (int): Tickets tagged as spam
- `auto_detected_spam` (int): Auto-detected spam tickets
- `processed_this_session` (int): Tickets processed in current session

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
