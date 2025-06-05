"""
Configuration management for Freshdesk Spam Filter
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the spam filter application"""
    
    # Freshdesk Configuration
    FRESHDESK_DOMAIN = os.getenv('FRESHDESK_DOMAIN')
    FRESHDESK_API_KEY = os.getenv('FRESHDESK_API_KEY')
    
    # OLLAMA Configuration
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME', 'gpt-3.5-turbo') # Default to gpt-3.5-turbo
    
    # Spam Filter Configuration
    SPAM_THRESHOLD = float(os.getenv('SPAM_THRESHOLD', '0.7'))
    AUTO_CLOSE_SPAM_THRESHOLD = float(os.getenv('AUTO_CLOSE_SPAM_THRESHOLD', '0.75'))
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '5'))
    MAX_TICKETS_PER_BATCH = int(os.getenv('MAX_TICKETS_PER_BATCH', '50'))
    PROCESS_NEW_TICKETS_ONLY = os.getenv('PROCESS_NEW_TICKETS_ONLY', 'true').lower() == 'true'

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Application Mode
    DRY_RUN_MODE = False # Default to False, will be set by main.py if --test is used
    IS_LAMBDA_ENVIRONMENT = os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None

    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_fields = [
            ('FRESHDESK_DOMAIN', cls.FRESHDESK_DOMAIN),
            ('FRESHDESK_API_KEY', cls.FRESHDESK_API_KEY),
            ('OPENAI_API_KEY', cls.OPENAI_API_KEY)
        ]
        
        missing_fields = []
        for field_name, field_value in required_fields:
            if not field_value:
                missing_fields.append(field_name)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True
    
    @classmethod
    def get_freshdesk_url(cls):
        """Get the base Freshdesk API URL"""
        if not cls.FRESHDESK_DOMAIN:
            raise ValueError("FRESHDESK_DOMAIN not configured")
        
        # Ensure domain has proper format
        domain = cls.FRESHDESK_DOMAIN
        if not domain.startswith('http'):
            domain = f"https://{domain}"
        
        return f"{domain}/api/v2"
