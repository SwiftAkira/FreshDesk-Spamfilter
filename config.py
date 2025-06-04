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
    
    # Spam Filter Configuration
    SPAM_THRESHOLD = float(os.getenv('SPAM_THRESHOLD', '0.7'))
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '5'))
    MAX_TICKETS_PER_BATCH = int(os.getenv('MAX_TICKETS_PER_BATCH', '50'))
    PROCESS_NEW_TICKETS_ONLY = os.getenv('PROCESS_NEW_TICKETS_ONLY', 'true').lower() == 'true'

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_fields = [
            ('FRESHDESK_DOMAIN', cls.FRESHDESK_DOMAIN),
            ('FRESHDESK_API_KEY', cls.FRESHDESK_API_KEY),
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
