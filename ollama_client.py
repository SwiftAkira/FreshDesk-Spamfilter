"""
OLLAMA AI Client for spam detection
"""
import ollama
import logging
import json
from typing import Dict, Tuple
from config import Config
import subprocess
import time
import requests

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with OLLAMA AI for spam detection"""
    
    def __init__(self):
        """Initialize the OLLAMA client"""
        self.host = Config.OLLAMA_HOST
        self.model = Config.OLLAMA_MODEL
        self.client = ollama.Client(host=self.host)
        
        # Test connection and attempt to start OLLAMA if not running
        self._test_and_prepare_ollama()
    
    def _test_and_prepare_ollama(self):
        """Test connection to OLLAMA server, try to start it if not running, and pull the model."""
        max_retries = 3
        server_start_delay_seconds = 15  # Time to wait after attempting to start ollama serve
        connection_retry_delay_seconds = 5 # Time to wait between connection retries
        ollama_started_by_script = False

        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to OLLAMA server at {self.host} (Attempt {attempt + 1}/{max_retries})...")
                # The list() call will attempt the actual connection
                models_info = self.client.list() 
                
                available_models = [model_data['name'] for model_data in models_info['models']]
                logger.info(f"Successfully connected to OLLAMA at {self.host}. Available models: {available_models}")

                if self.model not in available_models:
                    logger.warning(f"Model '{self.model}' not found locally. Attempting to pull model '{self.model}'...")
                    try:
                        self.client.pull(self.model)
                        logger.info(f"Model '{self.model}' pulled successfully.")
                    except ollama.ResponseError as pull_error:
                        logger.error(f"Failed to pull OLLAMA model '{self.model}': {pull_error}")
                        logger.error("Please ensure the model name is correct and accessible on the OLLAMA hub.")
                        raise # Re-raise the error as this is a configuration/model availability issue
                
                return # Connection successful, model checked/pulled

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection to OLLAMA at {self.host} failed on attempt {attempt + 1}: {e}")
                
                if attempt == 0 and not ollama_started_by_script:
                    # Only attempt to auto-start if NOT in a Lambda environment
                    if not Config.IS_LAMBDA_ENVIRONMENT:
                        logger.info("OLLAMA server not detected. Attempting to start 'ollama serve' in the background (not in Lambda env)...")
                        try:
                            # start_new_session=True makes it more independent on POSIX systems
                            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                            ollama_started_by_script = True
                            logger.info(f"'ollama serve' command issued. Waiting {server_start_delay_seconds} seconds for server to initialize...")
                            time.sleep(server_start_delay_seconds) # Wait for server to potentially start
                        except FileNotFoundError:
                            logger.error("'ollama' command not found. Please ensure OLLAMA is installed and in your system PATH.")
                            logger.error("Cannot automatically start OLLAMA server.")
                            # If not in Lambda, this is a critical local setup issue. Re-raise for local context.
                            raise ConnectionError(f"OLLAMA command not found and server not running at {self.host}.") from e
                        except Exception as start_exception:
                            logger.error(f"An error occurred while trying to start 'ollama serve': {start_exception}")
                            # Don't raise immediately, let the retry logic handle it
                        
                        # After attempting to start, continue to the next iteration to retry connection
                        continue 
                    else:
                        logger.warning("Running in Lambda environment. OLLAMA auto-start skipped. OLLAMA_HOST must be an accessible, running OLLAMA service.")

                if attempt < max_retries - 1:
                    logger.info(f"Retrying connection in {connection_retry_delay_seconds} seconds...")
                    time.sleep(connection_retry_delay_seconds)
                else:
                    logger.error(f"Max retries reached ({max_retries}). Failed to connect to OLLAMA server at {self.host}.")
                    if ollama_started_by_script:
                        logger.error("Although an attempt was made to start 'ollama serve', the connection could not be established.")
                        logger.error("Please check manually if 'ollama serve' started correctly and if the host/port are correct.")
                    else:
                        logger.error("Please ensure 'ollama serve' is running and accessible.")
                    raise ConnectionError(f"Failed to connect to OLLAMA at {self.host} after {max_retries} retries.") from e
            
            except ollama.ResponseError as e: # Catch other OLLAMA API errors (e.g., during list if server is up but misbehaving)
                logger.error(f"OLLAMA API Response Error during setup: {e}")
                raise # Re-raise, as this indicates a problem with the OLLAMA server itself or the request
            
            except Exception as e: # Catch any other unexpected errors during the setup process
                logger.error(f"An unexpected error occurred while preparing OLLAMA client: {e}")
                raise # Re-raise the original unexpected error
    
    def analyze_spam(self, subject: str, description: str, sender_email: str = "", is_system_validated: bool = False) -> Tuple[bool, float, str]:
        """
        Analyze ticket content for spam using AI
        
        Args:
            subject: Ticket subject
            description: Ticket description/content
            sender_email: Sender's email address
            is_system_validated: Flag indicating if the user/ticket was pre-validated by an internal system.
            
        Returns:
            Tuple of (is_spam, confidence_score, reasoning)
        """
        try:
            # Create prompt for spam analysis
            prompt = self._create_spam_analysis_prompt(subject, description, sender_email, is_system_validated)
            
            logger.debug(f"Analyzing content with OLLAMA model: {self.model}. System validated: {is_system_validated}")
            
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert spam detection system. Analyze the provided content and respond with a JSON object containing your analysis.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.1,  # Low temperature for consistent results
                    'top_p': 0.9
                }
            )
            
            # Parse the AI response
            return self._parse_spam_response(response['message']['content'])
            
        except Exception as e:
            logger.error(f"Error analyzing spam with OLLAMA: {e}")
            # Return safe default (not spam) on error
            return False, 0.0, f"Analysis failed: {str(e)}"
    
    def _create_spam_analysis_prompt(self, subject: str, description: str, sender_email: str, is_system_validated: bool) -> str:
        """Create a detailed prompt for spam analysis"""
        
        system_validation_guidance = ""
        if is_system_validated:
            system_validation_guidance = """

IMPORTANT CONTEXT FROM OUR SYSTEM:
- This user/ticket has been marked with: 'USER INFORMATION WAS VALIDATED BY OUR SYSTEM'.
- This means we have a strong internal indicator that this is a legitimate interaction.

INSTRUCTIONS BASED ON SYSTEM VALIDATION:
- If the above system validation is present (true), you MUST give this information very high priority.
- Be EXTREMELY hesitant to classify the ticket as spam. A simple request like 'Please delete my account' from a system-validated user is almost certainly NOT SPAM.
- To override system validation and classify as spam, you need OVERWHELMING and UNDENIABLE evidence of malicious activity, phishing, or clear spam content that directly contradicts the system validation.
- If in doubt, and system validation is present, err on the side of classifying as NOT SPAM.
"""

        prompt = f"""
Analyze the following support ticket for spam characteristics:

SUBJECT: {subject}

DESCRIPTION:
{description}

SENDER EMAIL: {sender_email}
{system_validation_guidance}
Please analyze this content and determine if it's spam. Consider these factors:
1. Promotional/marketing content
2. Suspicious links or attachments
3. Generic/template-like language
4. Irrelevant content for support
5. Suspicious sender patterns
6. Phishing attempts
7. Malicious content

Respond with a JSON object in this exact format:
{{
    "is_spam": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of your decision",
    "spam_indicators": ["list", "of", "specific", "indicators", "found"]
}}

Be conservative - only mark as spam if you're confident it's not a legitimate support request.
"""
        return prompt
    
    def _parse_spam_response(self, response_text: str) -> Tuple[bool, float, str]:
        """Parse the AI response and extract spam analysis"""
        try:
            # Try to extract JSON from the response
            response_text = response_text.strip()
            
            # Find JSON content (sometimes AI adds extra text)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_text = response_text[start_idx:end_idx]
            result = json.loads(json_text)
            
            is_spam = result.get('is_spam', False)
            confidence = float(result.get('confidence', 0.0))
            reasoning = result.get('reasoning', 'No reasoning provided')
            indicators = result.get('spam_indicators', [])
            
            # Add indicators to reasoning if available
            if indicators:
                reasoning += f" Indicators: {', '.join(indicators)}"
            
            logger.debug(f"Spam analysis result: spam={is_spam}, confidence={confidence}")
            
            return is_spam, confidence, reasoning
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"Raw response: {response_text}")
            
            # Fallback: try to determine from text content
            response_lower = response_text.lower()
            if 'spam' in response_lower and ('true' in response_lower or 'yes' in response_lower):
                return True, 0.5, "Parsed from text response (JSON parsing failed)"
            else:
                return False, 0.0, "Could not parse response, defaulting to not spam"
