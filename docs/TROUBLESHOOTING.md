# Troubleshooting Guide

## Overview

This guide helps you diagnose and resolve common issues with the Freshdesk Spam Filter system, focusing on OpenAI integration and AWS Lambda deployment.

## Quick Diagnostics

### 1. Check Local Configuration & Basic Connectivity (for Local Runs)

If running locally (not via Lambda), use `test_setup.py` for initial checks:

```bash
python test_setup.py
```

This script (or its equivalent checks within `config.py` loading) typically verifies:
- Presence of required configuration variables in `.env` (e.g., `FRESHDESK_DOMAIN`, `FRESHDESK_API_KEY`, `OPENAI_API_KEY`).
- Basic Freshdesk API connectivity by attempting to construct the URL.

*Note: Direct OpenAI API connectivity tests might not be part of `test_setup.py` to avoid unnecessary API calls.*

### 2. Analyze Logs

**For Local Runs:**
Check the application logs (e.g., `spam_filter.log` if configured, or console output):

```bash
# View recent logs
tail -f spam_filter.log

# Search for errors
grep -i "error" spam_filter.log

# Search for specific ticket issues
grep "Ticket ID: [ticket_id]" spam_filter.log # Replace [ticket_id]
```

**For AWS Lambda Runs:**
The primary source of logs is **AWS CloudWatch Logs**.
1.  Navigate to the CloudWatch console.
2.  Go to "Log groups".
3.  Find the log group for your Lambda function (usually `/aws/lambda/your-function-name`).
4.  Examine the latest log streams for errors or unexpected behavior.
5.  API Gateway also has logging options that can be enabled in CloudWatch.

## Configuration Issues (Local `.env` or Lambda Environment Variables)

### Missing Required Configuration
**Error Example (from `config.py` validation):**
```
ValueError: Missing required configuration: FRESHDESK_DOMAIN, OPENAI_API_KEY
```
**Cause:** Required environment variables are not set.
**Solution:**
1.  **Local:**
    *   Check if `.env` file exists and is in the project root.
    *   If missing, copy from `.env.example`: `cp .env.example .env`
    *   Edit `.env` and add all required values (see `CONFIGURATION.md`).
2.  **AWS Lambda:**
    *   Go to your Lambda function in the AWS console.
    *   Navigate to **Configuration > Environment variables**.
    *   Ensure all required keys (e.g., `FRESHDESK_DOMAIN`, `FRESHDESK_API_KEY`, `OPENAI_API_KEY`, `OPENAI_MODEL_NAME`, `AGENT_ID_TO_ASSIGN_SPAM`) are present and correctly spelled.

### Invalid Freshdesk Domain (`FRESHDESK_DOMAIN`)
**Symptom:** Errors like `404 Client Error: Not Found` when Freshdesk API is called, or connection errors.
**Cause:** Incorrect Freshdesk domain format.
**Solution:**
1.  Ensure `FRESHDESK_DOMAIN` in your configuration is **only the subdomain**.
    *   Correct: `yourcompany` (if your URL is `https://yourcompany.freshdesk.com`)
    *   Incorrect: `yourcompany.freshdesk.com`, `https://yourcompany.freshdesk.com`
2.  Test accessibility (replace `yourcompany` with your actual subdomain):
    ```bash
    curl -I https://yourcompany.freshdesk.com/api/v2/tickets # (Add -u "API_KEY:X" for auth test)
    ```

### Invalid Freshdesk API Key (`FRESHDESK_API_KEY`)
**Symptom:** `401 Client Error: Unauthorized` from Freshdesk API.
**Cause:** Incorrect or expired API key.
**Solution:**
1.  Verify the API key in your Freshdesk portal (Profile Settings > Your API Key).
2.  Update the `FRESHDESK_API_KEY` in your `.env` file or Lambda environment variables.
3.  Test API key (replace placeholders):
    ```bash
    curl -u "YOUR_API_KEY:X" https://your-subdomain.freshdesk.com/api/v2/tickets
    ```

## OpenAI API Issues

### Missing `OPENAI_API_KEY`
**Symptom:** Application fails to initialize `OpenAIClient`, or errors indicating a missing API key during analysis.
**Cause:** `OPENAI_API_KEY` environment variable is not set.
**Solution:**
1.  Ensure `OPENAI_API_KEY` is set in your `.env` file (local) or Lambda environment variables.
2.  Refer to `CONFIGURATION.md` for instructions on obtaining an OpenAI API key.

### Invalid `OPENAI_API_KEY`
**Symptom:** `openai.error.AuthenticationError` (or similar, like a 401 HTTP error from OpenAI) during spam analysis.
**Cause:** The API key is incorrect, revoked, or not authorized for the requested model/usage.
**Solution:**
1.  Double-check the API key for typos.
2.  Ensure the key is active in your OpenAI account dashboard.
3.  Verify your OpenAI account has a valid payment method and sufficient credits/quota.

### Invalid `OPENAI_MODEL_NAME` or Model Not Accessible
**Symptom:** Errors from OpenAI like "The model `your-model-name` does not exist" (404-like error) or "You do not have access to this model".
**Cause:** The specified `OPENAI_MODEL_NAME` is incorrect or your API key doesn't have permission to use it.
**Solution:**
1.  Verify the `OPENAI_MODEL_NAME` in your configuration against the list of available models in the OpenAI documentation for your account tier.
2.  Ensure your account/organization has access to the specified model (e.g., some newer models might have specific access requirements).

### OpenAI API Rate Limits Exceeded
**Symptom:** `openai.error.RateLimitError` (or similar, like a 429 HTTP error from OpenAI).
**Cause:** Your application is making too many requests to the OpenAI API too quickly, exceeding your account's rate limits.
**Solution:**
1.  Check your OpenAI account's usage limits and current usage.
2.  **For local polling script:** Consider increasing `CHECK_INTERVAL_MINUTES` or reducing `MAX_TICKETS_PER_BATCH` in `config.py` if processing many tickets rapidly.
3.  **For Lambda:** Rate limits are usually per minute/day. If legitimate, high traffic is expected, you might need to request a rate limit increase from OpenAI.
4.  The `openai` Python library has some built-in retry logic, but persistent issues indicate the limits are being hit consistently.

### OpenAI API General Errors (5xx, Content Policy, etc.)
**Symptom:** Various errors from OpenAI, including 500-range server errors, or errors related to content violating OpenAI's usage policies.
**Solution:**
1.  Check the OpenAI status page ([https://status.openai.com/](https://status.openai.com/)) for any ongoing incidents.
2.  If it's a content policy error, review the data being sent to the `analyze_spam` function (subject, description).
3.  For persistent 5xx errors, try again later or check OpenAI help resources.

### Insufficient Quota / Billing Issues (OpenAI)
**Symptom:** API calls fail, potentially with errors related to billing or quota.
**Cause:** Your OpenAI account may have run out of pre-paid credits, or there might be an issue with your payment method.
**Solution:**
1.  Log in to your OpenAI account.
2.  Check your current balance, usage, and billing status.
3.  Ensure your payment method is up to date.

## Freshdesk API Issues

### Rate Limiting (`429 Too Many Requests`)
**Symptom:** `429 Client Error: Too Many Requests` from Freshdesk API.
**Cause:** Exceeded Freshdesk API rate limits. (Refer to Freshdesk documentation for current limits).
**Solution:**
1.  **Local Polling Script:**
    *   Increase `CHECK_INTERVAL_MINUTES` in `.env` or Lambda environment variables.
    *   Reduce `MAX_TICKETS_PER_BATCH`.
2.  **General:** Review your Freshdesk API usage. The application attempts to be efficient, but very high ticket volumes might hit limits.

### Marking Ticket as Spam Fails (e.g., 400 Bad Request)
**Symptom:** Errors logged when `mark_as_spam` is called in `freshdesk_client.py`. The log should contain details from Freshdesk's response.
**Cause & Solution:**
1.  **Invalid `AGENT_ID_TO_ASSIGN_SPAM`**: If the configured agent ID is incorrect or the agent doesn't have permissions, assignment will fail. Verify the agent ID.
2.  **Tagging Issues**: Unlikely with the current "Auto-Spam-Detected" tag, but custom tag issues could arise if modified.
3.  **Status Transition Not Allowed**: Freshdesk might have workflows or rules preventing the status change (e.g., from current status to Closed/Spam).
4.  **Simultaneous Updates**: The code now separates agent assignment, tag updates, and status updates into distinct API calls to avoid issues with simultaneous updates. If errors persist, check the detailed error response from Freshdesk logged by the application.
5.  **Permissions**: Ensure the API key used has permissions to assign tickets, update tags, and change ticket status.

### INFO Log: "Retrying get_ticket ... without include=description"
**Symptom:** You see an `INFO` level log message: `Failed to get ticket ... with include=description. Status: 400. Retrying without include=description.`
**Cause:** Some Freshdesk instances/configurations might not support or allow the `include=description` parameter on the `/api/v2/tickets/{id}` endpoint for certain tickets or users.
**Solution:** This is not an error that stops the application. The system automatically retries without this parameter to fetch the basic ticket details and then separately fetches conversations if needed. This log is for informational purposes.

## AWS Lambda & API Gateway Issues

### Debugging with CloudWatch Logs
**This is your primary tool!**
- **Lambda Logs**: `/aws/lambda/your-function-name`
- **API Gateway Logs**: Can be enabled. Go to API Gateway > Your API > Stages > Your Stage > Logs/Tracing. Enable CloudWatch Logs and set log level to INFO or ERROR. This will create a new log group.

### Lambda Function Timeout
**Symptom:** Lambda execution times out (check CloudWatch Logs for "Task timed out after X seconds").
**Solution:**
1.  Increase Lambda function timeout: **Lambda Console > Your Function > Configuration > General configuration > Timeout**.
2.  Optimize code:
    *   Ensure API calls to Freshdesk and OpenAI are efficient.
    *   The current design processes one ticket per invocation, which is usually fast enough.
3.  Increase Lambda memory (can sometimes improve CPU performance and thus speed).

### Lambda IAM Permissions Issues
**Symptom:** Errors in CloudWatch Logs like "permission denied" when trying to write logs or access other AWS services.
**Solution:**
1.  Go to **IAM Console > Roles > your-lambda-role**.
2.  Ensure the role has the `AWSLambdaBasicExecutionRole` policy (or equivalent permissions) attached for CloudWatch logging: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`.
3.  If your Lambda needs to access other AWS services (e.g., Secrets Manager), add the necessary permissions to its IAM role.

### Lambda Configuration Errors (Environment Variables)
**Symptom:** Function fails with errors related to missing configuration (e.g., `ValueError` from `config.py`).
**Solution:**
1.  Go to **Lambda Console > Your Function > Configuration > Environment variables**.
2.  Verify all required variables are present, correctly spelled, and have the correct values.

### Lambda Deployment Package Issues
**Symptom:**
    *   Error uploading ZIP: "Unable to import module 'lambda_function': No module named 'lambda_function'"
    *   "Unable to import module 'lambda_function': No module named 'your_dependency'" (e.g., `openai`, `requests`).
**Solution:**
1.  Ensure your `deployment_package.zip` is structured correctly:
    *   Python files (`lambda_function.py`, `config.py`, etc.) should be at the **root** of the ZIP.
    *   Dependencies (like `openai`, `requests` folders) should also be at the **root** of the ZIP (installed via `pip install -r requirements.txt -t .` inside a temporary packaging folder, then zipping the contents of that folder).
2.  Ensure `requirements.txt` includes all necessary packages.
3.  Handler in Lambda configuration must be `lambda_function.lambda_handler`.

### API Gateway Issues
**Symptom:** Freshdesk webhook calls result in errors (e.g., 403 Forbidden, 500 Internal Server Error, 502 Bad Gateway from API Gateway URL).
**Solution:**
1.  **Check API Gateway CloudWatch Logs** (if enabled).
2.  **Integration Type:** Ensure the POST method for your resource (e.g., `/newticketwebhook`) is configured with "Lambda Function" as the integration type and **"Use Lambda Proxy integration" is CHECKED**.
3.  **Permissions:** API Gateway needs permission to invoke your Lambda function. This is usually set up automatically when creating the integration, but can be checked/fixed.
4.  **Deployment:** After any changes to API Gateway, you **must redeploy the API** (Actions > Deploy API > select stage).
5.  **Invoke URL:** Ensure the URL configured in Freshdesk webhook matches the API Gateway Invoke URL for the correct stage.

### Freshdesk Webhook Not Triggering Lambda / Payload Issues
**Symptom:** New tickets in Freshdesk do not result in Lambda invocations, or Lambda fails to parse the incoming event.
**Solution:**
1.  **Freshdesk Webhook Configuration:**
    *   **Callback URL**: Double-check it matches the API Gateway Invoke URL.
    *   **Request Type**: Must be `POST`.
    *   **Encoding**: `JSON`.
    *   **Enabled**: Ensure the automation rule is active.
    *   **Conditions**: Verify the conditions for the rule in Freshdesk are met by the test tickets.
2.  **Payload Parsing in `lambda_function.py`:**
    *   Freshdesk sends a JSON payload. The `lambda_handler` in `lambda_function.py` expects this in `event['body']`.
    *   The `event['body']` is a JSON string and needs to be parsed: `data = json.loads(event['body'])`.
    *   Freshdesk might wrap the actual ticket data within a key (e.g., `data['freshdesk_webhook']` or similar). You **must inspect the actual payload** received by Lambda (e.g., by logging `event` or `event['body']` in CloudWatch) to ensure your parsing logic (`lambda_function.py`) correctly extracts the ticket ID, subject, description, etc.
    *   Refer to Freshdesk Webhook documentation for the exact payload structure or use placeholders in Freshdesk to send only what you need.

## General Python & Environment Issues

### Module Not Found Errors (Local)
**Symptom:** `ModuleNotFoundError: No module named 'some_package'` when running `python main.py` or other scripts.
**Cause:** Dependencies are not installed, or you are not in the correct virtual environment.
**Solution:**
1.  Ensure your Python virtual environment (`venv`) is activated:
    ```bash
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate   # Windows
    ```
2.  Install/reinstall dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Incorrect Python Version
**Symptom:** Syntax errors or behavior incompatible with Python 3.8+.
**Cause:** Using an older Python version.
**Solution:**
1.  Check Python version: `python --version` or `python3 --version`.
2.  Ensure you are using Python 3.8 or newer. Use `python3` explicitly if `python` points to an older version.

---

If issues persist, gather detailed logs, error messages, and configuration details when seeking further assistance.
