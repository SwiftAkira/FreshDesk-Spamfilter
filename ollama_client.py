"""
OLLAMA AI Client for spam detection
"""
import ollama
import logging
import json
from typing import Dict, Tuple
from config import Config

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with OLLAMA AI for spam detection"""
    
    def __init__(self):
        """Initialize the OLLAMA client"""
        self.host = Config.OLLAMA_HOST
        self.model = Config.OLLAMA_MODEL
        self.client = ollama.Client(host=self.host)
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to OLLAMA server"""
        try:
            models = self.client.list()
            available_models = [model['name'] for model in models['models']]
            
            if self.model not in available_models:
                logger.warning(f"Model '{self.model}' not found. Available models: {available_models}")
                logger.info(f"Attempting to pull model '{self.model}'...")
                self.client.pull(self.model)
            
            logger.info(f"Successfully connected to OLLAMA at {self.host}")
            
        except Exception as e:
            logger.error(f"Failed to connect to OLLAMA at {self.host}: {e}")
            raise
    
    def analyze_spam(self, subject: str, description: str, sender_email: str = "") -> Tuple[bool, float, str]:
        """
        Analyze ticket content for spam using AI
        
        Args:
            subject: Ticket subject
            description: Ticket description/content
            sender_email: Sender's email address
            
        Returns:
            Tuple of (is_spam, confidence_score, reasoning)
        """
        try:
            # Create prompt for spam analysis
            prompt = self._create_spam_analysis_prompt(subject, description, sender_email)
            
            logger.debug(f"Analyzing content with OLLAMA model: {self.model}")
            
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
    
    def _create_spam_analysis_prompt(self, subject: str, description: str, sender_email: str) -> str:
        """Create a detailed prompt for spam analysis"""
        
        prompt = f"""
Analyze the following support ticket for spam characteristics:

SUBJECT: {subject}

DESCRIPTION: {description}

SENDER EMAIL: {sender_email}

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
