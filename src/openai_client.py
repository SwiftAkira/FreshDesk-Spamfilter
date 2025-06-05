"""
OpenAI API Client for spam detection
"""
import os
import json
import logging
from openai import OpenAI # Corrected import for OpenAI v1.x+
from .config import Config

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Client for interacting with OpenAI API for spam detection"""
    
    def __init__(self):
        """Initialize the OpenAI client"""
        if not Config.OPENAI_API_KEY:
            logger.error("OpenAI API key not configured. Please set OPENAI_API_KEY in your environment.")
            raise ValueError("OpenAI API key is missing.")
        
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL_NAME
        logger.info(f"OpenAIClient initialized with model: {self.model}")

    def _create_spam_analysis_prompt_messages(self, subject: str, description: str, sender_email: str, is_system_validated: bool) -> list:
        """Create a list of messages for the OpenAI Chat Completions prompt."""
        
        system_validation_guidance = ""
        if is_system_validated:
            system_validation_guidance = """

IMPORTANT CONTEXT FROM OUR SYSTEM:
- This user/ticket has been marked with: 'USER INFORMATION WAS VALIDATED BY OUR SYSTEM'.
- This means we have a strong internal indicator that this is a legitimate interaction.

INSTRUCTIONS BASED ON SYSTEM VALIDATION:
- If the above system validation is present, you MUST give this information very high priority.
- Be EXTREMELY hesitant to classify the ticket as spam. A simple request like 'Please delete my account' from a system-validated user is almost certainly NOT SPAM.
- To override system validation and classify as spam, you need OVERWHELMING and UNDENIABLE evidence of malicious activity, phishing, or clear spam content that directly contradicts the system validation.
- If in doubt, and system validation is present, err on the side of classifying as NOT SPAM.
"""
        system_message_content = f"""
You are an expert spam detection system. Analyze the provided support ticket content and respond with a JSON object containing your analysis.
Your response MUST be a single JSON object with the following schema:
{{
  "is_spam": boolean, // true if spam, false otherwise
  "confidence": float, // a score from 0.0 (definitely not spam) to 1.0 (definitely spam)
  "reasoning": "string", // brief explanation of your decision, highlighting key indicators
  "spam_indicators": ["string"] // a list of specific textual or contextual cues if spam, empty list otherwise
}}

{system_validation_guidance}
Be conservative - only mark as spam if you are confident it is not a legitimate support request or if it clearly violates spam criteria despite system validation (with strong justification).
"""
        
        user_message_content = f"""
Analyze the following support ticket for spam characteristics:

SUBJECT: {subject}

DESCRIPTION:
{description}

SENDER EMAIL: {sender_email}

Provide your analysis in the specified JSON format.
"""
        return [
            {"role": "system", "content": system_message_content},
            {"role": "user", "content": user_message_content}
        ]

    def analyze_spam(self, subject: str, description: str, sender_email: str = "", is_system_validated: bool = False) -> Tuple[bool, float, str]:
        """
        Analyze ticket content for spam using OpenAI API.
        
        Args:
            subject: Ticket subject
            description: Ticket description/content
            sender_email: Sender's email address
            is_system_validated: Flag indicating if the user/ticket was pre-validated by an internal system.
            
        Returns:
            Tuple of (is_spam, confidence_score, reasoning_with_indicators)
        """
        messages = self._create_spam_analysis_prompt_messages(subject, description, sender_email, is_system_validated)
        
        logger.debug(f"Sending request to OpenAI model: {self.model} with system_validated: {is_system_validated}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2, # Lower temperature for more deterministic and consistent output
                response_format={"type": "json_object"} # Enforce JSON output if model supports it
            )
            
            response_content = response.choices[0].message.content
            logger.debug(f"OpenAI raw response: {response_content}")
            
            # Parse the JSON response from AI
            result = json.loads(response_content)
            
            is_spam = result.get('is_spam', False)
            confidence = float(result.get('confidence', 0.0))
            reasoning = result.get('reasoning', 'No reasoning provided by AI.')
            indicators = result.get('spam_indicators', [])
            
            reasoning_with_indicators = reasoning
            if indicators:
                reasoning_with_indicators += f" Indicators: {', '.join(indicators)}"
            
            logger.debug(f"OpenAI analysis result: spam={is_spam}, confidence={confidence}, reasoning='{reasoning_with_indicators}'")
            return is_spam, confidence, reasoning_with_indicators
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from OpenAI: {e}. Raw response: '{response_content}'")
            return False, 0.0, "AI response parsing failed (JSONDecodeError)."
        except openai.APIError as e:
            logger.error(f"OpenAI API Error: {e}")
            return False, 0.0, f"OpenAI API Error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error analyzing spam with OpenAI: {e}", exc_info=True)
            return False, 0.0, f"Unexpected error during OpenAI analysis: {str(e)}" 