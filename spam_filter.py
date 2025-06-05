"""
Core spam filtering logic
"""
import logging
import time
from typing import List, Dict, Optional
from freshdesk_client import FreshdeskClient
# from ollama_client import OllamaClient # Old client
from openai_client import OpenAIClient # New OpenAI client
from config import Config

logger = logging.getLogger(__name__)

class SpamFilter:
    """Main spam filtering service"""
    
    def __init__(self):
        """Initialize the spam filter"""
        self.freshdesk = FreshdeskClient()
        # self.ollama = OllamaClient() # Old client instance
        self.ai_client = OpenAIClient() # New OpenAI client instance
        self.spam_threshold = Config.SPAM_THRESHOLD
        self.processed_tickets = set()  # Track processed tickets to avoid duplicates
        
        logger.info(f"Spam filter initialized with AI client: {type(self.ai_client).__name__}, threshold: {self.spam_threshold}")
    
    def process_tickets(self, limit: int = None) -> Dict[str, int]:
        """
        Process NEW tickets for spam detection (only first customer messages)

        Args:
            limit: Maximum number of tickets to process

        Returns:
            Dictionary with processing statistics
        """
        if limit is None:
            limit = Config.MAX_TICKETS_PER_BATCH

        stats = {
            'total_processed': 0,
            'spam_detected': 0,
            'legitimate': 0,
            'errors': 0,
            'skipped_already_processed': 0
        }

        try:
            # Fetch tickets based on configuration
            if Config.PROCESS_NEW_TICKETS_ONLY:
                logger.info("Fetching NEW tickets for spam analysis...")
                tickets = self.freshdesk.get_tickets(only_new=True, limit=limit)
            else:
                logger.info("Fetching ALL open tickets for spam analysis...")
                tickets = self.freshdesk.get_tickets(status='open', limit=limit)

            logger.info(f"Found {len(tickets)} new tickets to analyze")

            for ticket in tickets:
                ticket_id = ticket['id']

                # Skip if already processed
                if ticket_id in self.processed_tickets:
                    stats['skipped_already_processed'] += 1
                    logger.debug(f"Skipping already processed ticket #{ticket_id}")
                    continue

                try:
                    # Get the first customer message only (not agent responses)
                    first_message = self.freshdesk.get_first_customer_message(ticket_id)

                    # Analyze only the first customer message
                    result = self.analyze_first_customer_message(first_message)
                    stats['total_processed'] += 1

                    if result['is_spam']:
                        stats['spam_detected'] += 1
                        logger.info(f"SPAM DETECTED - Ticket #{ticket_id}: {result['reasoning']}")
                    else:
                        stats['legitimate'] += 1
                        logger.debug(f"Legitimate ticket #{ticket_id}")

                    # Mark as processed
                    self.processed_tickets.add(ticket_id)

                except Exception as e:
                    logger.error(f"Error processing ticket {ticket_id}: {e}")
                    stats['errors'] += 1

            logger.info(f"Processing complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error in process_tickets: {e}")
            stats['errors'] += 1
            return stats
    
    def analyze_ticket(self, ticket: Dict) -> Dict:
        """
        Analyze a single ticket for spam
        
        Args:
            ticket: Ticket dictionary from Freshdesk
            
        Returns:
            Analysis result dictionary
        """
        ticket_id = ticket['id']
        subject = ticket.get('subject', '')
        description = ticket.get('description_text', '') or ticket.get('description', '')
        
        # Get requester email if available
        requester_id = ticket.get('requester_id')
        sender_email = ''
        
        try:
            # Try to get more details if needed
            if not description and ticket.get('description'):
                # Strip HTML tags from description
                import re
                description = re.sub('<[^<]+?>', '', ticket['description'])
            
            # Check for system validation phrase
            system_validated_phrase = "USER INFORMATION WAS VALIDATED BY OUR SYSTEM"
            is_system_validated = system_validated_phrase.lower() in description.lower()
            if is_system_validated:
                logger.info(f"Ticket #{ticket_id} contains system validation phrase in its description. Flagging for AI awareness.")

            logger.debug(f"Analyzing ticket #{ticket_id}: '{subject}'")
            
            # Analyze with AI
            is_spam_ai, confidence, reasoning = self.ai_client.analyze_spam(
                subject=subject,
                description=description,
                sender_email=sender_email,
                is_system_validated=is_system_validated # Pass the flag
            )
            
            result = {
                'ticket_id': ticket_id,
                'is_spam': is_spam_ai and confidence >= self.spam_threshold,
                'confidence': confidence,
                'reasoning': reasoning,
                'subject': subject
            }
            
            # Take action if spam detected
            if result['is_spam']:
                self.handle_spam_ticket(ticket_id, result)
            
            return result

        except Exception as e:
            logger.error(f"Error analyzing ticket {ticket_id}: {e}")
            return {
                'ticket_id': ticket_id,
                'is_spam': False,
                'confidence': 0.0,
                'reasoning': f"Analysis failed: {str(e)}",
                'subject': subject
            }

    def analyze_first_customer_message(self, message_data: Dict) -> Dict:
        """
        Analyze the first customer message for spam (not agent responses)

        Args:
            message_data: Dictionary containing the first customer message details

        Returns:
            Analysis result dictionary
        """
        ticket_id = message_data['ticket_id']
        subject = message_data.get('subject', '')
        description = message_data.get('description', '')
        sender_email = message_data.get('sender_email', '')

        # Check for system validation phrase
        system_validated_phrase = "USER INFORMATION WAS VALIDATED BY OUR SYSTEM"
        is_system_validated = system_validated_phrase.lower() in description.lower()
        if is_system_validated:
            logger.info(f"Ticket #{ticket_id} contains system validation phrase. Flagging for AI awareness.")

        try:
            logger.debug(f"Analyzing FIRST CUSTOMER MESSAGE for ticket #{ticket_id}: '{subject}'")

            # Analyze with AI - only the original customer message
            is_spam_ai, confidence, reasoning = self.ai_client.analyze_spam(
                subject=subject,
                description=description,
                sender_email=str(sender_email),  # Convert to string in case it's an ID
                is_system_validated=is_system_validated # Pass the flag
            )

            result = {
                'ticket_id': ticket_id,
                'is_spam': is_spam_ai and confidence >= self.spam_threshold,
                'confidence': confidence,
                'reasoning': reasoning,
                'subject': subject,
                'message_type': 'first_customer_message'
            }

            # Take action if spam detected
            if result['is_spam']:
                self.handle_spam_ticket(ticket_id, result)

            return result

        except Exception as e:
            logger.error(f"Error analyzing first customer message for ticket {ticket_id}: {e}")
            return {
                'ticket_id': ticket_id,
                'is_spam': False,
                'confidence': 0.0,
                'reasoning': f"Analysis failed: {str(e)}",
                'subject': subject,
                'message_type': 'first_customer_message'
            }
    
    def handle_spam_ticket(self, ticket_id: int, analysis_result: Dict):
        """
        Handle a ticket that has been identified as spam
        
        Args:
            ticket_id: The ticket ID
            analysis_result: The spam analysis result
        """
        try:
            confidence = analysis_result['confidence']
            reasoning = analysis_result['reasoning']
            
            logger.info(f"Handling spam ticket #{ticket_id} (confidence: {confidence:.2f})")
            
            # Check for existing spam notes from this system (OLLAMA or OpenAI)
            # Use a generic identifier for checking, but specific one for adding new notes
            generic_spam_alert_identifier = "Automatic Spam Detection Alert" 
            current_ai_specific_identifier = f"Automatic Spam Detection Alert (OpenAI)"

            try:
                conversations = self.freshdesk.get_ticket_conversations(ticket_id)
                for conv in conversations:
                    note_body_content = conv.get('body_text') or conv.get('body', '')
                    if conv.get('private') and generic_spam_alert_identifier in note_body_content:
                        logger.info(f"A spam detection note (potentially from OLLAMA or OpenAI) already exists for ticket #{ticket_id}. Skipping adding a new note.")
                        if confidence >= Config.AUTO_CLOSE_SPAM_THRESHOLD:
                            logger.info(f"Ticket #{ticket_id} (spam, confidence {confidence:.2f}) meets auto-close threshold ({Config.AUTO_CLOSE_SPAM_THRESHOLD}). Ensuring it is marked as spam/closed.")
                            try:
                                self.freshdesk.mark_as_spam(ticket_id)
                            except Exception as e_mark_spam:
                                logger.error(f"Failed to mark ticket #{ticket_id} as spam (when existing note found): {e_mark_spam}")
                        return # Exit after finding an existing note and attempting action
            except Exception as e_check_notes: # Catch errors specifically from get_ticket_conversations or its loop
                logger.warning(f"Could not check for existing notes on ticket #{ticket_id} due to: {e_check_notes}. Proceeding to add note.")

            # Construct the note content using the current AI specific identifier
            note_content = f"""
            {current_ai_specific_identifier}
            Model: {Config.OPENAI_MODEL_NAME}
            Confidence Score: {confidence:.2f}
            Analysis: {reasoning}
            
            This ticket was automatically processed based on the AI analysis.
            Threshold for action was: {self.spam_threshold}
            """
            
            # Add the analysis as a private note to the ticket
            try:
                self.freshdesk.add_note_to_ticket(ticket_id, note_content, private=True)
            except Exception as e:
                logger.error(f"Failed to add spam note to ticket #{ticket_id}: {e}")

            # Mark as spam (status update, potentially close) if confidence is high enough
            if confidence >= Config.AUTO_CLOSE_SPAM_THRESHOLD:
                logger.info(f"Ticket #{ticket_id} (spam, confidence {confidence:.2f}) meets auto-close threshold ({Config.AUTO_CLOSE_SPAM_THRESHOLD}). Marking as spam/closed.")
                self.freshdesk.mark_as_spam(ticket_id)
            else:
                logger.info(f"Ticket #{ticket_id} (spam, confidence {confidence:.2f}) is below auto-close threshold ({Config.AUTO_CLOSE_SPAM_THRESHOLD}). Tagged, but not auto-closed.")

        except Exception as e:
            logger.error(f"Error in handle_spam_ticket for ticket {ticket_id}: {e}")
    
    def get_spam_statistics(self) -> Dict:
        """Get statistics about spam detection"""
        try:
            # Get tickets with spam tags
            all_tickets = self.freshdesk.get_tickets(limit=1000)
            
            spam_tagged = 0
            auto_detected = 0
            
            for ticket in all_tickets:
                tags = ticket.get('tags', [])
                if 'spam' in tags or 'auto-spam-detected' in tags:
                    spam_tagged += 1
                if 'auto-spam-detected' in tags:
                    auto_detected += 1
            
            return {
                'total_tickets_checked': len(all_tickets),
                'spam_tagged_tickets': spam_tagged,
                'auto_detected_spam': auto_detected,
                'processed_this_session': len(self.processed_tickets)
            }
            
        except Exception as e:
            logger.error(f"Error getting spam statistics: {e}")
            return {'error': str(e)}

    def process_single_ticket_data(self, ticket_data: Dict) -> Dict:
        """
        Process a single ticket's data, typically from a webhook event.

        Args:
            ticket_data: Dictionary containing the ticket details from Freshdesk.

        Returns:
            Dictionary with processing result for this single ticket.
        """
        ticket_id = ticket_data.get('id')
        subject = ticket_data.get('subject', '')
        # Prefer plain text description if available from webhook
        description = ticket_data.get('description_text') 
        if not description:
            html_description = ticket_data.get('description', '')
            if html_description:
                import re
                description = re.sub('<[^<]+?>', '', html_description) # Strip HTML
            else:
                description = "" # Ensure description is a string
        
        # Attempt to get a sender identifier. Webhooks might provide 'email' or 'requester_id'
        # This might need adjustment based on actual webhook payload structure from Freshdesk for "Ticket Created"
        sender_email = ticket_data.get('email') # Often present for new tickets directly
        if not sender_email:
            requester_id = ticket_data.get('requester_id')
            sender_email = str(requester_id) if requester_id else ""

        if not ticket_id:
            logger.error("process_single_ticket_data: Ticket ID missing in provided data.")
            return {'error': 'Ticket ID missing', 'ticket_id': None, 'is_spam': False}

        logger.info(f"Processing single ticket event for ticket ID: {ticket_id}")

        # Check for system validation phrase
        system_validated_phrase = "USER INFORMATION WAS VALIDATED BY OUR SYSTEM"
        is_system_validated = system_validated_phrase.lower() in description.lower()
        if is_system_validated:
            logger.info(f"Ticket #{ticket_id} (from event) contains system validation phrase. Flagging for AI awareness.")

        try:
            is_spam_ai, confidence, reasoning = self.ai_client.analyze_spam(
                subject=subject,
                description=description,
                sender_email=sender_email,
                is_system_validated=is_system_validated
            )

            analysis_result = {
                'ticket_id': ticket_id,
                'subject': subject,
                'is_spam': is_spam_ai and confidence >= self.spam_threshold,
                'confidence': confidence,
                'reasoning': reasoning,
                'action_taken': 'none'
            }

            if analysis_result['is_spam']:
                logger.info(f"SPAM DETECTED (from event) - Ticket #{ticket_id}: {reasoning}")
                self.handle_spam_ticket(ticket_id, analysis_result) # analysis_result is passed here
                analysis_result['action_taken'] = 'handled_as_spam' # Update action taken
            else:
                logger.info(f"Legitimate ticket (from event) - Ticket #{ticket_id}. Confidence: {confidence:.2f}, Reasoning: {reasoning}")
                analysis_result['action_taken'] = 'marked_as_legitimate'

            self.processed_tickets.add(ticket_id) # Still useful to track if Lambda retries or processes same event
            return analysis_result

        except Exception as e:
            logger.error(f"Error processing single ticket data for ticket {ticket_id}: {e}", exc_info=True)
            return {
                'ticket_id': ticket_id,
                'is_spam': False,
                'confidence': 0.0,
                'reasoning': f"Analysis failed: {str(e)}",
                'error': str(e),
                'action_taken': 'error_in_processing'
            }
