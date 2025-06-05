# Freshdesk Spam Filter with OpenAI Integration

An intelligent spam filtering system for Freshdesk that uses the OpenAI API to automatically detect and handle spam tickets.

## Features

- 🤖 **AI-Powered Detection**: Uses OpenAI API for intelligent spam analysis
- 🔄 **Automatic Processing**: Continuously monitors and processes new tickets
- 🏷️ **Smart Tagging**: Automatically tags spam tickets for easy identification
- ⚙️ **Configurable Thresholds**: Adjustable confidence levels for spam detection
- 📊 **Detailed Logging**: Comprehensive logging and statistics
- 🔒 **Secure**: API keys managed via .env file. Ticket data is sent to the OpenAI API for analysis.
- 🎯 **Conservative Approach**: Designed to minimize false positives

## Prerequisites

1. **Freshdesk Account** with API access
2. **OpenAI API Key**
3. **Python 3.8+**

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application:**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your configuration
   nano .env
   ```

## Configuration

Edit the `.env` file with your settings:

```env
# Freshdesk Configuration
FRESHDESK_DOMAIN=your-subdomain # e.g., yourcompany if your URL is yourcompany.freshdesk.com
FRESHDESK_API_KEY=your_freshdesk_api_key_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_NAME=gpt-3.5-turbo # Or your preferred model

# Spam Filter Configuration
SPAM_THRESHOLD=0.7
AUTO_CLOSE_SPAM_THRESHOLD=0.75
CHECK_INTERVAL_MINUTES=5
MAX_TICKETS_PER_BATCH=50
PROCESS_NEW_TICKETS_ONLY=true
AGENT_ID_TO_ASSIGN_SPAM=your_agent_id_for_spam # If applicable

# Logging
LOG_LEVEL=INFO
```

### Configuration Options

- **FRESHDESK_DOMAIN**: Your Freshdesk subdomain (e.g., `yourcompany` if URL is `yourcompany.freshdesk.com`)
- **FRESHDESK_API_KEY**: Your Freshdesk API key (found in Profile Settings)
- **OPENAI_API_KEY**: Your OpenAI API key.
- **OPENAI_MODEL_NAME**: The OpenAI model to use (e.g., `gpt-3.5-turbo`, `gpt-4`, `gpt-4.1-nano`).
- **SPAM_THRESHOLD**: Confidence threshold for initial spam detection (0.0-1.0).
- **AUTO_CLOSE_SPAM_THRESHOLD**: Confidence threshold to automatically close a ticket as spam (0.0-1.0).
- **CHECK_INTERVAL_MINUTES**: How often to check for new tickets (in continuous mode).
- **MAX_TICKETS_PER_BATCH**: Maximum tickets to process in one batch (in continuous mode).
- **PROCESS_NEW_TICKETS_ONLY**: Set to `true` to only process new tickets, `false` to process all open tickets.
- **AGENT_ID_TO_ASSIGN_SPAM**: (Optional) The numerical ID of the agent to assign spam tickets to before closing.
- **LOG_LEVEL**: Logging level (e.g., `INFO`, `DEBUG`).

## Getting Your Freshdesk API Key

1. Log in to your Freshdesk portal
2. Click on your profile picture (top right)
3. Go to "Profile Settings"
4. Your API key is shown in the right sidebar under "Your API Key"

## Getting Your OpenAI API Key

1. Go to [https://platform.openai.com/](https://platform.openai.com/)
2. Sign up or log in.
3. Navigate to the API keys section in your account settings to create and copy your API key.

## Usage

### Run Continuously (Recommended for local execution)
```bash
python main.py
```
This will monitor Freshdesk continuously and process new tickets automatically based on `CHECK_INTERVAL_MINUTES`.

### Run Once (for a single ticket test)
```bash
python main.py --once
```
This will process one current ticket and exit.

### Run in Test Mode (Dry Run)
```bash
python main.py --test
```
This runs the continuous cycle but does not make any actual changes to Freshdesk (e.g., no tagging, no closing, no notes added). It logs what it *would* do.
Combine with `--once` for a single dry run: `python main.py --once --test`

### Show Help
```bash
python main.py --help
```

## How It Works

1. **New Ticket Monitoring**: The system fetches new tickets from Freshdesk (or all open tickets, depending on configuration).
2. **First Message Extraction**: Extracts the first customer message from the ticket details.
3. **AI Analysis**: The ticket subject, description, and sender email are sent to the OpenAI API for analysis against a spam detection prompt.
4. **Spam Detection**: The OpenAI API provides a confidence score and reasoning for spam classification.
5. **Automatic Actions**: Based on confidence levels:
   - **High confidence (≥ `AUTO_CLOSE_SPAM_THRESHOLD`)**: Ticket is assigned to a designated agent (if `AGENT_ID_TO_ASSIGN_SPAM` is set), tagged `Auto-Spam-Detected`, a private note with AI analysis is added, and the ticket is closed.
   - **Medium confidence (≥ `SPAM_THRESHOLD` but < `AUTO_CLOSE_SPAM_THRESHOLD`)**: Ticket is tagged `Auto-Spam-Detected` and a private note is added. It is not automatically closed, allowing for manual review.
   - **Low confidence**: No action taken.

### What Gets Analyzed

✅ **Processed:**
- New tickets (status 2 = Open by default, or all open if configured).
- First customer message content (if available, otherwise ticket description).
- Original ticket subject.
- Sender email (if available).

❌ **Ignored (by default for new tickets):**
- Agent responses and replies within existing conversations.
- Private notes between agents (unless part of the initial description).
- Already processed tickets within the same run cycle.
- Tickets in pending/resolved/closed status (unless `PROCESS_NEW_TICKETS_ONLY` is `false`).

## Spam Detection Criteria (Inferred by AI)

The OpenAI model analyzes tickets based on a prompt that guides it to look for common spam characteristics, such as:

- Promotional/marketing content without clear user opt-in.
- Suspicious links or attachments.
- Generic/template-like language inconsistent with genuine support requests.
- Irrelevant content for the typical support queries of the helpdesk.
- Unusual sender patterns or email addresses.
- Phishing attempts or requests for sensitive information.
- Indicators of malicious content.

## Output Example

```
╔══════════════════════════════════════════════════════════════╗
║                    FRESHDESK SPAM FILTER                     ║
║                   with OpenAI Integration                    ║
╚══════════════════════════════════════════════════════════════╝

Configuration:
  • Freshdesk Domain: your-subdomain.freshdesk.com
  • OpenAI Model: gpt-3.5-turbo
  • Spam Threshold: 0.7
  • Auto-Close Threshold: 0.75
  • Check Interval: 5 minutes
  • Max Tickets/Batch: 50
  • Process New Tickets Only: true

Spam Detection Results:
  • Total Processed: 15
  • Spam Detected: 3
  • Legitimate: 12
  • Errors: 0

⚠️  3 spam ticket(s) detected and handled!
```

## Logging

The application creates detailed logs in `spam_filter.log` including:
- Ticket processing details
- Spam detection results from OpenAI (including reasoning)
- API interactions with Freshdesk and OpenAI
- Error messages

## Troubleshooting

### Common Issues

1. **"Missing required configuration"**
   - Ensure all required fields in `.env` are set (e.g., `FRESHDESK_DOMAIN`, `FRESHDESK_API_KEY`, `OPENAI_API_KEY`).
   - Check that your Freshdesk domain (subdomain part only) and API keys are correct.

2. **"Error fetching tickets from Freshdesk" or OpenAI API errors**
   - Verify your Freshdesk domain and API key / OpenAI API key.
   - Check your internet connection.
   - Ensure your Freshdesk account has API access and your OpenAI account has sufficient credits/quota.

3. **High false positive rate or poor detection**
   - Adjust the `SPAM_THRESHOLD` or `AUTO_CLOSE_SPAM_THRESHOLD` values in `.env`.
   - Consider trying a different OpenAI model specified in `OPENAI_MODEL_NAME`.
   - Review the AI's reasoning in the logs to understand its decisions.
   - The prompt sent to OpenAI (in `openai_client.py`) can be tuned for better performance if needed.

## Security Considerations

- API keys are stored locally in the `.env` file. Ensure this file is secured and **not committed to version control** (it should be in your `.gitignore`).
- Ticket data (subject, description, sender email) is sent to the OpenAI API for analysis. Review OpenAI's data usage and privacy policies.

## Lambda Deployment

This application is designed to be deployable to AWS Lambda for event-driven, real-time spam filtering.

Key components for Lambda deployment:
- `lambda_function.py`: Contains the `lambda_handler` for AWS Lambda.
- `spam_filter.py` includes `process_single_ticket_data` for handling individual ticket events.
- Configuration is loaded from Lambda environment variables.

**High-Level Lambda Deployment Steps:**

1.  **Package Application**: Create a ZIP file containing your code and dependencies (installed via `pip install -r requirements.txt -t ./package`).
2.  **IAM Role**: Create an IAM role for Lambda with permissions for `AWSLambdaBasicExecutionRole`.
3.  **Lambda Function**: Create the Lambda function in AWS, upload the ZIP, set the handler to `lambda_function.lambda_handler`, and configure environment variables (for API keys, thresholds, etc.).
4.  **API Gateway**: Set up an API Gateway endpoint (e.g., POST method) that triggers your Lambda function.
5.  **Freshdesk Webhook**: Configure a webhook in Freshdesk (e.g., on ticket creation) to send ticket data to your API Gateway endpoint.

## Testing Procedures

### Running Tests

The project includes test suites to validate functionality:

```bash
# Ensure you have test-specific dependencies if any (e.g., pytest, mock)
# Activate your virtual environment: source venv/bin/activate

python test_ai_spam_detection.py    # Test AI spam detection with realistic examples
python test_edge_cases.py           # Test edge cases and ambiguous content
python test_ai_independence.py      # Verify AI makes content-based decisions (may need OLLAMA for older tests)
python test_new_tickets_only.py     # Verify only new tickets are processed
python test_setup.py                # Validate configuration and connectivity
```
Note: Some older tests like `test_ai_independence.py` might have been written with OLLAMA in mind and may need updates or to be run with a compatible local setup if OLLAMA was a core part of their original design.

## Developer Setup

### Prerequisites for Development

1. **Python 3.8+** with pip
2. **Git** for version control
3. **OLLAMA** for local AI models
4. **Code Editor** with Python support (VS Code recommended)

### Development Installation

```bash
# Clone the repository
git clone <repository-url>
cd freshdesk-spam-filter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if available)
pip install pytest black mypy flake8

# Copy environment template
cp .env.example .env

# Configure your development environment
nano .env
```

### Development Workflow

1. **Setup**: Follow development installation steps
2. **Configuration**: Configure `.env` with test credentials
3. **Testing**: Run test suite to validate setup
4. **Development**: Make changes following coding standards
5. **Testing**: Run tests to validate changes
6. **Documentation**: Update documentation as needed

### Code Quality Standards

- **Type Hints**: All functions should include type hints
- **Docstrings**: All classes and methods must have docstrings
- **Logging**: Use structured logging for debugging
- **Error Handling**: Implement proper exception handling
- **Testing**: Write tests for new functionality

## Integration Patterns

### Custom Freshdesk Integration

```python
from freshdesk_client import FreshdeskClient
from spam_filter import SpamFilter

# Custom ticket processing
def process_specific_tickets():
    client = FreshdeskClient()
    spam_filter = SpamFilter()

    # Get tickets with custom filters
    tickets = client.get_tickets(status='open', limit=100)

    for ticket in tickets:
        result = spam_filter.analyze_ticket(ticket)
        if result['is_spam']:
            print(f"Spam detected: {ticket['id']}")
```

### Custom AI Model Integration

```python
from ollama_client import OllamaClient

# Use different model
class CustomOllamaClient(OllamaClient):
    def __init__(self, model_name='custom-model'):
        super().__init__()
        self.model = model_name
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

- Development setup and workflow
- Coding standards and style guide
- Testing requirements
- Pull request process
- Issue reporting guidelines

## Documentation

- **[Architecture](ARCHITECTURE.md)** - System design and component interactions
- **[API Reference](API_REFERENCE.md)** - Detailed API documentation
- **[Configuration](CONFIGURATION.md)** - Complete configuration guide
- **[Deployment](DEPLOYMENT.md)** - Deployment instructions and best practices
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## License

This project is open source. Please check the license file for details.
