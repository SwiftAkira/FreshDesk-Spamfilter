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

3. **Ensure your `.env` file has the correct values.** The application will validate required fields on startup.

## Configuration File Structure

The `.env` file contains all configuration options organized by category:

```env
# Freshdesk Configuration
FRESHDESK_DOMAIN=your-subdomain # e.g., yourcompany if your URL is yourcompany.freshdesk.com
FRESHDESK_API_KEY=your_freshdesk_api_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL_NAME=gpt-3.5-turbo # Or your preferred model

# Spam Filter Configuration
SPAM_THRESHOLD=0.7
AUTO_CLOSE_SPAM_THRESHOLD=0.75
CHECK_INTERVAL_MINUTES=5
MAX_TICKETS_PER_BATCH=50
PROCESS_NEW_TICKETS_ONLY=true
AGENT_ID_TO_ASSIGN_SPAM=your_agent_id_for_spam # Optional: Agent ID to assign spam tickets to

# Logging Configuration
LOG_LEVEL=INFO
```

## Required Configuration

### Freshdesk Settings

#### FRESHDESK_DOMAIN
- **Required**: Yes
- **Type**: String
- **Format**: `your-subdomain` (e.g., `yourcompany` for `yourcompany.freshdesk.com`)
- **Description**: Your Freshdesk subdomain. The system will construct the full URL.
- **Example**: `mycompany`

**How to find your domain:**
1. Log into your Freshdesk portal
2. Look at the URL in your browser (e.g., `https://mycompany.freshdesk.com`)
3. Use only the subdomain part (e.g., `mycompany`)

#### FRESHDESK_API_KEY
- **Required**: Yes
- **Type**: String
- **Description**: Your Freshdesk API key for authentication
- **Security**: Keep this secret and never commit to version control (ensure `.env` is in `.gitignore`).

**How to get your API key:**
1. Log into your Freshdesk portal
2. Click your profile picture (top right)
3. Go to "Profile Settings"
4. Find "Your API Key" in the right sidebar

### OpenAI Settings

#### OPENAI_API_KEY
- **Required**: Yes
- **Type**: String
- **Description**: Your OpenAI API Key for accessing the AI models.
- **Security**: Keep this secret and never commit to version control.

**How to get your OpenAI API key:**
1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign up or log in.
3. Create a new secret key.

## Optional Configuration

### OpenAI Settings (Continued)

#### OPENAI_MODEL_NAME
- **Required**: No
- **Type**: String
- **Default**: `gpt-3.5-turbo`
- **Description**: The OpenAI model name to use for spam detection.
- **Examples**:
  - `gpt-3.5-turbo` (cost-effective, fast)
  - `gpt-4` (higher accuracy, more expensive)
  - `gpt-4-turbo-preview`
  - `gpt-4.1-nano` (if available and suitable)

**Model Selection Guide:**
- Consider the trade-offs between cost, speed, and accuracy for your use case.
- Refer to OpenAI documentation for the latest models and their capabilities.

### Spam Filter Settings

#### SPAM_THRESHOLD
- **Required**: No
- **Type**: Float (0.0 - 1.0)
- **Default**: `0.7`
- **Description**: Confidence threshold for initially classifying a ticket as potential spam (e.g., for tagging and noting, but not necessarily closing).
- **Recommendations**:
  - `0.6` - More sensitive (catches more potential spam, may have more false positives for review)
  - `0.7` - Balanced
  - `0.8` - Conservative

#### AUTO_CLOSE_SPAM_THRESHOLD
- **Required**: No
- **Type**: Float (0.0 - 1.0)
- **Default**: `0.75`
- **Description**: Confidence threshold to automatically close a ticket as spam. Must be >= `SPAM_THRESHOLD` if both are used effectively.
- **Recommendations**:
  - `0.75` - A reasonable starting point for auto-closing.
  - `0.9` - Very conservative, only close if AI is highly confident.

#### AGENT_ID_TO_ASSIGN_SPAM
- **Required**: No
- **Type**: Integer
- **Default**: `None` (If not set, spam tickets marked for closure might not be assigned, or might use a system default. Currently, agent ID `80059226092` is hardcoded in `freshdesk_client.py` if this is not set, which should ideally be removed in favor of this config).
- **Description**: The numerical ID of the Freshdesk agent to assign spam tickets to before closing them. This can help with workflows and reporting.

#### CHECK_INTERVAL_MINUTES
- **Required**: No
- **Type**: Integer (e.g., 1-60)
- **Default**: `5`
- **Description**: Minutes between processing cycles when running in local continuous mode.
- **Considerations**:
  - Lower values = More responsive but higher API usage.
  - Higher values = Less API usage but slower response.
  - Not applicable for Lambda deployment (which is event-driven).

#### MAX_TICKETS_PER_BATCH
- **Required**: No
- **Type**: Integer (1-100)
- **Default**: `50`
- **Description**: Maximum tickets to process in one batch (local continuous mode).
- **Limitations**: Freshdesk API maximum is 100 per request for some ticket list endpoints.

#### PROCESS_NEW_TICKETS_ONLY
- **Required**: No
- **Type**: Boolean (`true` or `false`)
- **Default**: `true`
- **Description**: Whether to process only newly opened tickets (status 2).
- **Options**:
  - `true` - Only process new tickets.
  - `false` - Process all open tickets (use with caution, could process many tickets).

### Logging Settings

#### LOG_LEVEL
- **Required**: No
- **Type**: String
- **Default**: `INFO`
- **Description**: Logging verbosity level.
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

## Environment-Specific Configuration Examples

These are illustrative. Adjust based on your needs.

### Development Environment

```env
# Development settings
FRESHDESK_DOMAIN=your-dev-subdomain
FRESHDESK_API_KEY=dev_freshdesk_api_key
OPENAI_API_KEY=dev_openai_api_key
OPENAI_MODEL_NAME=gpt-3.5-turbo
SPAM_THRESHOLD=0.6
AUTO_CLOSE_SPAM_THRESHOLD=0.7
CHECK_INTERVAL_MINUTES=1
MAX_TICKETS_PER_BATCH=10
AGENT_ID_TO_ASSIGN_SPAM=your_test_agent_id
LOG_LEVEL=DEBUG
PROCESS_NEW_TICKETS_ONLY=true
```

### Production Environment (for local continuous run)

```env
# Production settings for local run
FRESHDESK_DOMAIN=your-prod-subdomain
FRESHDESK_API_KEY=prod_freshdesk_api_key
OPENAI_API_KEY=prod_openai_api_key
OPENAI_MODEL_NAME=gpt-4 # Or a preferred production model
SPAM_THRESHOLD=0.7
AUTO_CLOSE_SPAM_THRESHOLD=0.85
CHECK_INTERVAL_MINUTES=5
MAX_TICKETS_PER_BATCH=50
AGENT_ID_TO_ASSIGN_SPAM=your_spam_handling_agent_id
LOG_LEVEL=INFO
PROCESS_NEW_TICKETS_ONLY=true
```

### Lambda Environment (Set these in AWS Lambda Environment Variables)

```env
# For Lambda, these would be set in the Lambda console, not a .env file
FRESHDESK_DOMAIN=your-prod-subdomain
FRESHDESK_API_KEY=prod_freshdesk_api_key_from_secrets_manager_or_env
OPENAI_API_KEY=prod_openai_api_key_from_secrets_manager_or_env
OPENAI_MODEL_NAME=gpt-4
SPAM_THRESHOLD=0.7
AUTO_CLOSE_SPAM_THRESHOLD=0.85
AGENT_ID_TO_ASSIGN_SPAM=your_spam_handling_agent_id
LOG_LEVEL=INFO
PROCESS_NEW_TICKETS_ONLY=true # This might be implicitly true due to event-driven nature
# CHECK_INTERVAL_MINUTES and MAX_TICKETS_PER_BATCH are not typically used by Lambda event processing.
```

## Configuration Validation

### Automatic Validation

The application automatically validates required configuration on startup (e.g., `FRESHDESK_DOMAIN`, `FRESHDESK_API_KEY`, `OPENAI_API_KEY`).

```bash
python main.py # For local run
```
If running via Lambda, validation occurs at the start of each invocation.

### Common Validation Errors

1.  **Missing `FRESHDESK_DOMAIN` / `FRESHDESK_API_KEY` / `OPENAI_API_KEY`**:
    ```
    ValueError: Missing required configuration: FRESHDESK_DOMAIN, OPENAI_API_KEY
    ```
    **Solution**: Ensure these variables are correctly set in your `.env` file (for local) or Lambda environment variables.

2.  **Invalid `SPAM_THRESHOLD` or `AUTO_CLOSE_SPAM_THRESHOLD`**:
    The application expects these to be convertible to floats. Incorrect values might lead to runtime errors or unexpected behavior.
    **Solution**: Ensure these are valid numbers (e.g., `0.7`).

## Security Best Practices

### File Permissions for `.env`

If using a `.env` file for local development, set appropriate permissions:

```bash
# Make .env readable only by owner
chmod 600 .env
```
Ensure `.env` is listed in your `.gitignore` file and is **never committed to version control**.

For AWS Lambda, use AWS Secrets Manager or encrypted environment variables for managing sensitive data like API keys for better security.
