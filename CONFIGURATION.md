# Configuration Guide

## Overview

The Freshdesk Spam Filter uses environment variables for configuration, stored in a `.env` file. This approach ensures sensitive information like API keys are kept secure and separate from the codebase.

## Quick Setup

1. **Copy the example configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the configuration:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Validate configuration:**
   ```bash
   python test_setup.py
   ```

## Configuration File Structure

The `.env` file contains all configuration options organized by category:

```env
# Freshdesk Configuration
FRESHDESK_DOMAIN=your-domain.freshdesk.com
FRESHDESK_API_KEY=your_api_key_here

# OLLAMA Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Spam Filter Configuration
SPAM_THRESHOLD=0.7
CHECK_INTERVAL_MINUTES=5
MAX_TICKETS_PER_BATCH=50
PROCESS_NEW_TICKETS_ONLY=true

# Logging Configuration
LOG_LEVEL=INFO
```

## Required Configuration

### Freshdesk Settings

#### FRESHDESK_DOMAIN
- **Required**: Yes
- **Type**: String
- **Format**: `your-domain.freshdesk.com` or `https://your-domain.freshdesk.com`
- **Description**: Your Freshdesk domain URL
- **Example**: `company.freshdesk.com`

**How to find your domain:**
1. Log into your Freshdesk portal
2. Look at the URL in your browser
3. Use the domain part (e.g., `company.freshdesk.com`)

#### FRESHDESK_API_KEY
- **Required**: Yes
- **Type**: String (64 characters)
- **Description**: Your Freshdesk API key for authentication
- **Security**: Keep this secret and never commit to version control

**How to get your API key:**
1. Log into your Freshdesk portal
2. Click your profile picture (top right)
3. Go to "Profile Settings"
4. Find "Your API Key" in the right sidebar
5. Copy the key (it looks like: `abcdef1234567890abcdef1234567890abcdef12`)

## Optional Configuration

### OLLAMA Settings

#### OLLAMA_HOST
- **Required**: No
- **Type**: URL
- **Default**: `http://localhost:11434`
- **Description**: OLLAMA server URL
- **Examples**:
  - Local: `http://localhost:11434`
  - Remote: `http://192.168.1.100:11434`
  - Custom port: `http://localhost:8080`

#### OLLAMA_MODEL
- **Required**: No
- **Type**: String
- **Default**: `llama3.2`
- **Description**: AI model name to use for spam detection
- **Recommended Options**:
  - `llama3.2` - Best balance of speed and accuracy
  - `llama3.2:8b` - Higher accuracy, slower processing
  - `mistral` - Fast processing, good accuracy
  - `phi3` - Lightweight, resource-efficient

**Model Selection Guide:**
- **Production**: `llama3.2`
- **High Accuracy**: `llama3.2:8b`
- **Speed Priority**: `mistral`
- **Low Resources**: `phi3`

### Spam Filter Settings

#### SPAM_THRESHOLD
- **Required**: No
- **Type**: Float (0.0 - 1.0)
- **Default**: `0.7`
- **Description**: Confidence threshold for spam detection
- **Recommendations**:
  - `0.6` - More sensitive (catches more spam, may have false positives)
  - `0.7` - Balanced (recommended for most use cases)
  - `0.8` - Conservative (fewer false positives, may miss some spam)
  - `0.9` - Very conservative (high confidence only)

#### CHECK_INTERVAL_MINUTES
- **Required**: No
- **Type**: Integer (1-60)
- **Default**: `5`
- **Description**: Minutes between processing cycles
- **Considerations**:
  - Lower values = More responsive but higher API usage
  - Higher values = Less API usage but slower response
  - Freshdesk API rate limits may apply

#### MAX_TICKETS_PER_BATCH
- **Required**: No
- **Type**: Integer (1-100)
- **Default**: `50`
- **Description**: Maximum tickets to process in one batch
- **Limitations**: Freshdesk API maximum is 100 per request

#### PROCESS_NEW_TICKETS_ONLY
- **Required**: No
- **Type**: Boolean
- **Default**: `true`
- **Description**: Whether to process only newly opened tickets
- **Options**:
  - `true` - Only process new tickets (status 2)
  - `false` - Process all open tickets

### Logging Settings

#### LOG_LEVEL
- **Required**: No
- **Type**: String
- **Default**: `INFO`
- **Description**: Logging verbosity level
- **Options**:
  - `DEBUG` - Very detailed logging (for development)
  - `INFO` - Standard logging (recommended)
  - `WARNING` - Only warnings and errors
  - `ERROR` - Only errors
  - `CRITICAL` - Only critical errors

## Environment-Specific Configuration

### Development Environment

```env
# Development settings
FRESHDESK_DOMAIN=test-company.freshdesk.com
FRESHDESK_API_KEY=test_api_key_here
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
SPAM_THRESHOLD=0.6
CHECK_INTERVAL_MINUTES=1
MAX_TICKETS_PER_BATCH=10
LOG_LEVEL=DEBUG
```

### Production Environment

```env
# Production settings
FRESHDESK_DOMAIN=company.freshdesk.com
FRESHDESK_API_KEY=production_api_key_here
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
SPAM_THRESHOLD=0.7
CHECK_INTERVAL_MINUTES=5
MAX_TICKETS_PER_BATCH=50
LOG_LEVEL=INFO
```

### High-Volume Environment

```env
# High-volume settings
FRESHDESK_DOMAIN=company.freshdesk.com
FRESHDESK_API_KEY=production_api_key_here
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral
SPAM_THRESHOLD=0.8
CHECK_INTERVAL_MINUTES=2
MAX_TICKETS_PER_BATCH=100
LOG_LEVEL=WARNING
```

## Configuration Validation

### Automatic Validation

The application automatically validates configuration on startup:

```bash
python main.py
```

### Manual Validation

Use the test script to validate configuration:

```bash
python test_setup.py
```

### Common Validation Errors

1. **Missing FRESHDESK_DOMAIN**:
   ```
   Configuration Error: Missing required configuration: FRESHDESK_DOMAIN
   ```
   **Solution**: Add your Freshdesk domain to the `.env` file

2. **Missing FRESHDESK_API_KEY**:
   ```
   Configuration Error: Missing required configuration: FRESHDESK_API_KEY
   ```
   **Solution**: Add your Freshdesk API key to the `.env` file

3. **Invalid SPAM_THRESHOLD**:
   ```
   ValueError: SPAM_THRESHOLD must be between 0.0 and 1.0
   ```
   **Solution**: Set SPAM_THRESHOLD to a value between 0.0 and 1.0

## Security Best Practices

### File Permissions

Set appropriate permissions for the `.env` file:

```bash
# Make .env readable only by owner
chmod 600 .env
```

### Environment Variables

For production deployments, consider using system environment variables instead of `.env` files:

```bash
export FRESHDESK_DOMAIN=company.freshdesk.com
export FRESHDESK_API_KEY=your_api_key_here
python main.py
```

### API Key Security

- Never commit `.env` files to version control
- Use different API keys for development and production
- Regularly rotate API keys
- Monitor API key usage in Freshdesk

## Troubleshooting Configuration

### Testing Connectivity

```bash
# Test Freshdesk connection
python -c "from freshdesk_client import FreshdeskClient; client = FreshdeskClient(); print('Freshdesk OK')"

# Test OLLAMA connection
python -c "from ollama_client import OllamaClient; client = OllamaClient(); print('OLLAMA OK')"
```

### Configuration Debugging

Enable debug logging to see configuration values:

```env
LOG_LEVEL=DEBUG
```

Then check the logs for configuration details (sensitive values are masked).

## Advanced Configuration

### Custom Configuration Files

You can specify a custom configuration file:

```bash
# Use custom .env file
cp .env.production .env.custom
python main.py  # Will use .env.custom if .env doesn't exist
```

### Runtime Configuration Changes

Some settings can be overridden at runtime:

```python
from config import Config

# Override spam threshold
Config.SPAM_THRESHOLD = 0.8

# Override check interval
Config.CHECK_INTERVAL_MINUTES = 10
```

### Multiple Environment Support

For managing multiple environments:

```bash
# Development
cp .env.example .env.dev

# Staging
cp .env.example .env.staging

# Production
cp .env.example .env.prod

# Use specific environment
ln -sf .env.prod .env
```
