# Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Freshdesk Spam Filter. The primary recommended deployment method for production is AWS Lambda for an event-driven, scalable solution. Local deployment is also covered for development, testing, or smaller-scale continuous operation.

## Prerequisites

### System Requirements (for Local Deployment)

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Network**: Internet access for Freshdesk API and OpenAI API.

### Required Services/Accounts

1. **Freshdesk Account** with API access.
2. **OpenAI API Key** and account with sufficient quota/credits.
3. **Python Environment** with pip (for local deployment).
4. **AWS Account** (for Lambda deployment).

## Part 1: Local Deployment (for Development/Testing or Continuous Polling)

This setup runs the `main.py` script on a local machine or server, continuously polling Freshdesk for new tickets.

### 1. System Preparation (Example for Ubuntu/Debian)

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip (if not already installed)
sudo apt install python3 python3-pip python3-venv git -y
```

### 2. Application Setup

```bash
# Clone the repository
# git clone https://github.com/SwiftAkira/FreshDesk-Spamfilter.git # Replace with your repo URL if different
# cd FreshDesk-Spamfilter

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure application
cp .env.example .env
nano .env  # Edit with your Freshdesk & OpenAI API keys and other settings (see CONFIGURATION.md)
```

### 3. Validation and Running Locally

```bash
# Ensure .env is correctly configured

# Run a single test cycle (Dry Run - no changes to Freshdesk)
python main.py --once --test

# Run a single test cycle (Live - will make changes)
# python main.py --once 

# Start continuous monitoring (polls Freshdesk based on CHECK_INTERVAL_MINUTES)
python main.py
```

### Example Local `.env` Configuration:
```env
FRESHDESK_DOMAIN=your-subdomain
FRESHDESK_API_KEY=your_freshdesk_key
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL_NAME=gpt-3.5-turbo
SPAM_THRESHOLD=0.7
AUTO_CLOSE_SPAM_THRESHOLD=0.75
CHECK_INTERVAL_MINUTES=5
AGENT_ID_TO_ASSIGN_SPAM=your_agent_id # Optional
LOG_LEVEL=INFO
```

### Service Management for Local Continuous Run (Optional - Systemd Example)

For running the local polling script as a persistent service on Linux:

```bash
# Create service file
sudo nano /etc/systemd/system/freshdesk-spam-filter.service
```

**Service Configuration (Example):**
Adjust `User`, `Group`, `WorkingDirectory`, `Environment`, and `ExecStart` path as needed.
```ini
[Unit]
Description=Freshdesk Spam Filter (Local Polling)
After=network.target

[Service]
Type=simple
User=your_user # Replace with the user that should run the script
Group=your_group # Replace with the group for the user
WorkingDirectory=/path/to/your/FreshDesk-Spamfilter # Replace with actual path
Environment="PATH=/path/to/your/FreshDesk-Spamfilter/venv/bin" # Path to venv
ExecStart=/path/to/your/FreshDesk-Spamfilter/venv/bin/python main.py
Restart=always
RestartSec=30
StandardOutput=append:/var/log/freshdesk-spam-filter.log
StandardError=append:/var/log/freshdesk-spam-filter.error.log

[Install]
WantedBy=multi-user.target
```

**Service Management Commands:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable freshdesk-spam-filter

# Start service immediately
sudo systemctl start freshdesk-spam-filter

# Check status
sudo systemctl status freshdesk-spam-filter

# View logs (if configured as above)
# sudo journalctl -u freshdesk-spam-filter -f
# tail -f /var/log/freshdesk-spam-filter.log
```

## Part 2: AWS Lambda Deployment (Recommended for Production - Event-Driven)

This method uses AWS Lambda for serverless, event-driven processing of new Freshdesk tickets in real-time.

### 1. Create a Deployment Package (ZIP file)

This package will contain your Python scripts and their dependencies.

```bash
# Ensure your virtual environment is active: source venv/bin/activate
# Ensure requirements.txt is up-to-date: pip freeze > requirements.txt

# Create a directory for the package contents
mkdir package_lambda

# Install dependencies into this directory
pip install -r requirements.txt -t ./package_lambda

# Navigate into the package directory
cd package_lambda

# Zip the dependencies
zip -r ../deployment_package.zip .

# Go back to the project root
cd ..

# Add your script files to the zip
zip -g deployment_package.zip lambda_function.py config.py spam_filter.py openai_client.py freshdesk_client.py

# Clean up the temporary package directory (optional)
# rm -rf package_lambda
```
This creates `deployment_package.zip` in your project root.

### 2. Create an IAM Role for the Lambda Function

- In the AWS IAM console, create a new role.
- **Trusted entity type**: AWS service
- **Use case**: Lambda
- **Permissions policies**: Attach `AWSLambdaBasicExecutionRole` (allows writing logs to CloudWatch).
- **Role name**: e.g., `FreshdeskSpamFilterLambdaRole`.

### 3. Create the Lambda Function in AWS

- Go to the AWS Lambda console and click "Create function".
- Choose "Author from scratch".
- **Function name**: e.g., `FreshdeskSpamFilter`
- **Runtime**: Select a Python version (e.g., Python 3.9, 3.10, 3.11 - matching your `requirements.txt`).
- **Architecture**: e.g., `x86_64`.
- **Permissions**: Choose "Use an existing role" and select the IAM role created above.
- Click "Create function".

### 4. Configure the Lambda Function

- **Code source**: Upload the `deployment_package.zip` file.
- **Runtime settings** > **Handler**: Set to `lambda_function.lambda_handler`.
- **Configuration** > **Environment variables**: Add key-value pairs for all settings required by `config.py`. Example:
    - `FRESHDESK_DOMAIN`: `your-subdomain`
    - `FRESHDESK_API_KEY`: `your_freshdesk_api_key` (consider AWS Secrets Manager for production)
    - `OPENAI_API_KEY`: `your_openai_api_key` (consider AWS Secrets Manager for production)
    - `OPENAI_MODEL_NAME`: `gpt-3.5-turbo` (or your preferred model)
    - `SPAM_THRESHOLD`: `0.7`
    - `AUTO_CLOSE_SPAM_THRESHOLD`: `0.75`
    - `AGENT_ID_TO_ASSIGN_SPAM`: `your_agent_id` (the ID for agent "Ria No" e.g. `80059226092`)
    - `LOG_LEVEL`: `INFO`
    - `PROCESS_NEW_TICKETS_ONLY`: `true` (usually the case for webhook-triggered Lambdas)
- **Configuration** > **General configuration**:
    - **Memory**: Start with 256MB or 512MB. Monitor and adjust as needed.
    - **Timeout**: Set an appropriate value (e.g., 30 seconds to 1 minute) to accommodate API calls.

### 5. Set up API Gateway

- In the AWS API Gateway console, choose "Build" under **REST API** (not HTTP API).
- **Protocol**: REST
- **Create new API**: New API
- **API name**: e.g., `FreshdeskSpamWebhookAPI`
- Click "Create API".
- In the "Resources" tree, select "/" (root), then **Actions** > **Create Resource**.
    - **Resource Name**: e.g., `newticketwebhook`
    - **Resource Path**: `/newticketwebhook` (or your preferred path)
    - Click "Create Resource".
- With the new resource selected (e.g., `/newticketwebhook`), **Actions** > **Create Method**.
    - Choose `POST` from the dropdown and click the checkmark.
    - **Integration type**: Lambda Function
    - **Use Lambda Proxy integration**: Check this box.
    - **Lambda Region**: Select the region where your Lambda function is.
    - **Lambda Function**: Start typing your Lambda function's name and select it.
    - Click "Save". Grant permission for API Gateway to invoke your Lambda function.
- **Actions** > **Deploy API**.
    - **Deployment stage**: Select "[New Stage]".
    - **Stage name**: e.g., `prod` or `v1`.
    - Click "Deploy".
- Note the **Invoke URL** displayed. It will look like `https://<api-id>.execute-api.<region>.amazonaws.com/<stage_name>/newticketwebhook`.

### 6. Configure Freshdesk Webhook

- In your Freshdesk portal: **Admin** > **Workflows** > **Automations**.
- Go to the **Ticket Creation** tab and click "New Rule".
- **Rule Name**: e.g., `Trigger Spam Filter Lambda`
- **Execute order**: Choose conditions for when this rule should run (e.g., "Source is Email" or for all new tickets).
- **Perform these actions**:
    - Choose **Trigger Webhook**.
    - **Request Type**: `POST`
    - **Callback URL**: Paste the **Invoke URL** from API Gateway here.
    - **Encoding**: `JSON`
    - **Content**: Select **Advanced**. Freshdesk will send the ticket payload. Ensure your `lambda_function.py` is set up to parse this (the `event` object in the handler). Typically, Freshdesk sends a JSON payload where the ticket data is nested. Your current `lambda_function.py` expects the ticket data directly in `event['body']` which then needs to be JSON parsed, and then the actual ticket might be inside a key like `'freshdesk_webhook'`. You may need to adjust `lambda_function.py` based on the exact payload Freshdesk sends or use Freshdesk's placeholder options to structure the JSON sent.
      Example of what Freshdesk might send (you need to check their docs or test):
      ```json
      {
        "freshdesk_webhook": {
          "ticket_id":"[ticket.id]",
          "ticket_subject":"[ticket.subject]",
          // ... other ticket fields using Freshdesk placeholders ...
        }
      }
      ```
      Your Lambda would then need to access `json.loads(event['body'])['freshdesk_webhook']`.
- Save and activate the rule.

### 7. Testing Lambda Deployment

- Create a new ticket in Freshdesk that matches your webhook rule conditions.
- Check AWS CloudWatch Logs for your Lambda function to see its execution logs, spam analysis results, and any errors.
- Verify actions (notes, tags, status changes) in Freshdesk.

## Docker Deployment (Alternative for Local/Server)

A basic Dockerfile for running the Python application (not OLLAMA). This assumes the application uses OpenAI and doesn't need OLLAMA within the container.

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose any port if your app runs a web service (not typical for this script unless for a local webhook receiver)
# EXPOSE 5000 

# Command to run the application (using local continuous mode as an example)
# Ensure .env file is mounted or environment variables are passed at runtime
CMD ["python", "main.py"]
```

**Build and Run Docker (Example):**
```bash
# Build the image
docker build -t freshdesk-spam-filter .

# Run the container, mounting a .env file
docker run -it --rm --env-file .env freshdesk-spam-filter

# Or pass environment variables directly
# docker run -it --rm -e FRESHDESK_DOMAIN=... -e FRESHDESK_API_KEY=... -e OPENAI_API_KEY=... freshdesk-spam-filter
```

This Docker setup is for the polling-based `main.py`. For a Lambda-like event-driven approach with Docker, you would typically use services like AWS Fargate with an event source or a custom webhook receiver within the Docker container.
