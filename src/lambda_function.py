import json
import logging
import os

# Assuming other project files (config, spam_filter, etc.) are in the same directory or in PYTHONPATH
from .config import Config
from .spam_filter import SpamFilter
from .main import setup_logging # Re-use logging setup from main.py if suitable

# Initialize logger for Lambda
# If reusing setup_logging, it might need adjustment for Lambda's specific logging context
# For now, a simple logger setup:
logger = logging.getLogger()
log_level_str = os.environ.get('LOG_LEVEL', Config.LOG_LEVEL) # Get from Lambda env var or config default
logger.setLevel(getattr(logging, log_level_str.upper(), logging.INFO))

# Manually load Lambda environment variables into Config class attributes
# This is because Lambda uses os.environ directly, not .env files.
# We do this once when the Lambda container initializes.

def load_config_from_env():
    """Load configuration from Lambda environment variables into Config object for consistency."""
    Config.FRESHDESK_DOMAIN = os.environ.get('FRESHDESK_DOMAIN', Config.FRESHDESK_DOMAIN)
    Config.FRESHDESK_API_KEY = os.environ.get('FRESHDESK_API_KEY', Config.FRESHDESK_API_KEY)
    Config.SPAM_THRESHOLD = float(os.environ.get('SPAM_THRESHOLD', str(Config.SPAM_THRESHOLD)))
    Config.AUTO_CLOSE_SPAM_THRESHOLD = float(os.environ.get('AUTO_CLOSE_SPAM_THRESHOLD', str(Config.AUTO_CLOSE_SPAM_THRESHOLD)))
    Config.PROCESS_NEW_TICKETS_ONLY = os.environ.get('PROCESS_NEW_TICKETS_ONLY', str(Config.PROCESS_NEW_TICKETS_ONLY)).lower() == 'true'
    Config.DRY_RUN_MODE = os.environ.get('DRY_RUN_MODE', str(Config.DRY_RUN_MODE)).lower() == 'true'
    
    Config.OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', Config.OPENAI_API_KEY)
    Config.OPENAI_MODEL_NAME = os.environ.get('OPENAI_MODEL_NAME', Config.OPENAI_MODEL_NAME)
    Config.AGENT_ID_TO_ASSIGN_SPAM = os.environ.get('AGENT_ID_TO_ASSIGN_SPAM', Config.AGENT_ID_TO_ASSIGN_SPAM)
    if Config.AGENT_ID_TO_ASSIGN_SPAM and isinstance(Config.AGENT_ID_TO_ASSIGN_SPAM, str) and Config.AGENT_ID_TO_ASSIGN_SPAM.isdigit():
        Config.AGENT_ID_TO_ASSIGN_SPAM = int(Config.AGENT_ID_TO_ASSIGN_SPAM)
    elif Config.AGENT_ID_TO_ASSIGN_SPAM == 'None' or Config.AGENT_ID_TO_ASSIGN_SPAM == '': # Handle string 'None' or empty string
        Config.AGENT_ID_TO_ASSIGN_SPAM = None

    # IS_LAMBDA_ENVIRONMENT is already set correctly in config.py

    # Perform validation after attempting to load from environment
    try:
        Config.validate()
        logger.info("Configuration loaded and validated successfully for Lambda.")
    except ValueError as e:
        logger.error(f"CRITICAL: Missing or invalid configuration in Lambda environment: {e}")
        # This is a critical error; the Lambda function might not operate correctly.
        # Consider raising an exception to halt initialization if essential configs are missing.
        raise e

# Load configuration when the Lambda container initializes (cold start)
load_config_from_env()

# Initialize SpamFilter once during cold start if it doesn't rely on event-specific data for init
# This can save initialization time on subsequent invocations.
try:
    spam_filter_instance = SpamFilter()
    logger.info("SpamFilter instance initialized globally for Lambda.")
except Exception as e:
    logger.error(f"CRITICAL: Failed to initialize SpamFilter globally: {e}. This may affect Lambda operation.")
    spam_filter_instance = None # Ensure it's defined, even if None

def lambda_handler(event, context):
    """
    AWS Lambda handler function.

    Args:
        event (dict): Event data passed to the function (e.g., from API Gateway).
                      Expected to be a Freshdesk webhook payload for 'Ticket Created'.
        context (object): Lambda context object (providing runtime info).

    Returns:
        dict: Response object for API Gateway (statusCode, body).
    """
    logger.info(f"Lambda function invoked. Event: {json.dumps(event)}")

    if not spam_filter_instance:
        logger.error("SpamFilter instance not available. Aborting processing.")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'SpamFilter not initialized'})
        }

    # Extract ticket data from the Freshdesk webhook payload
    # The exact structure of 'event' depends on how Freshdesk sends webhook data
    # and how API Gateway forwards it.
    # We expect the Freshdesk ticket object to be in event['body'] if API Gateway is used with standard integration.
    # And event['body'] would be a JSON string that needs parsing.

    try:
        if isinstance(event.get('body'), str):
            freshdesk_webhook_payload = json.loads(event['body'])
        else:
            freshdesk_webhook_payload = event.get('body') # If body is already a dict

        if not freshdesk_webhook_payload or 'ticket' not in freshdesk_webhook_payload:
            logger.error("Invalid or missing Freshdesk ticket data in webhook payload.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid Freshdesk ticket data in payload'})
            }
        
        ticket_data = freshdesk_webhook_payload['ticket']
        ticket_id = ticket_data.get('id')

        if not ticket_id:
            logger.error("Ticket ID not found in webhook payload.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Ticket ID missing in payload'})
            }

        logger.info(f"Processing ticket ID: {ticket_id} from webhook event.")

        # Use the SpamFilter instance to process this single ticket
        # We need a method in SpamFilter that can take ticket data directly
        analysis_result = spam_filter_instance.process_single_ticket_data(ticket_data)

        logger.info(f"Processing complete for ticket ID: {ticket_id}. Result: {analysis_result}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Ticket processed successfully',
                'ticket_id': ticket_id,
                'analysis': analysis_result
            })
        }

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from event body: {e}")
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid JSON in request body'})}
    except Exception as e:
        logger.error(f"Error processing ticket in Lambda: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

# Example of how Freshdesk might send a 'Ticket Created' payload (simplified):
# {
#   "body": {
#     "freshdesk_webhook": {
#       "ticket_id": 123,
#       "ticket_subject": "Help me!",
#       "ticket_description": "I need assistance with...",
#       "ticket_status": "Open",
#       "requester_email": "user@example.com",
#       "ticket_cf_user_information_was_validated_by_our_system": "No" // Example custom field
#       // ... other ticket fields
#     }
#   }
# }
# The actual payload structure you receive needs to be confirmed.
# The important part for the lambda_handler is to get to the `ticket_data` dictionary.
# Often, for POST requests via API Gateway, the actual payload from Freshdesk
# might be nested, e.g., event['body']['freshdesk_webhook']['ticket_requester_email']
# Or, if API Gateway is set up with a mapping template, it might be directly available.
# For this initial setup, I'm assuming the ticket object itself is passed as `ticket_data`.
# We will likely need to parse event['body'] as JSON. 