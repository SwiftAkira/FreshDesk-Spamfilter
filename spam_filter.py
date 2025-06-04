"""
Core spam filtering logic
"""
import logging
import time
from typing import List, Dict, Optional
from freshdesk_client import FreshdeskClient
from ollama_client import OllamaClient
from config import Config

logger = logging.getLogger(__name__)

class SpamFilter:
    """Main spam filtering service"""
    
    def __init__(self):
        """Initialize the spam filter"""
        self.freshdesk = FreshdeskClient()
        self.ollama = OllamaClient()
        self.spam_threshold = Config.SPAM_THRESHOLD
        self.processed_tickets = set()  # Track processed tickets to avoid duplicates
        
        logger.info(f"Spam filter initialized with threshold: {self.spam_threshold}")
    
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
            
            logger.debug(f"Analyzing ticket #{ticket_id}: '{subject}'")
            
            # Analyze with AI
            is_spam, confidence, reasoning = self.ollama.analyze_spam(
                subject=subject,
                description=description,
                sender_email=sender_email
            )
            
            result = {
                'ticket_id': ticket_id,
                'is_spam': is_spam and confidence >= self.spam_threshold,
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

        try:
            logger.debug(f"Analyzing FIRST CUSTOMER MESSAGE for ticket #{ticket_id}: '{subject}'")

            # Analyze with AI - only the original customer message
            is_spam, confidence, reasoning = self.ollama.analyze_spam(
                subject=subject,
                description=description,
                sender_email=str(sender_email)  # Convert to string in case it's an ID
            )

            result = {
                'ticket_id': ticket_id,
                'is_spam': is_spam and confidence >= self.spam_threshold,
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
            
            # Add spam tag
            self.freshdesk.add_tag_to_ticket(ticket_id, 'auto-spam-detected')
            
            # Add a note with the analysis
            note_content = f"""
            Automatic Spam Detection Alert
            
            This ticket has been automatically flagged as potential spam.
            
            Confidence Score: {confidence:.2f}
            Analysis: {reasoning}
            
            Please review this ticket manually to confirm.
            """
            
            # Update ticket with spam status if confidence is very high
            if confidence >= 0.9:
                logger.info(f"High confidence spam - marking ticket #{ticket_id} as spam")
                self.freshdesk.mark_as_spam(ticket_id)
            else:
                # Just add tag for manual review
                logger.info(f"Medium confidence spam - tagging ticket #{ticket_id} for review")
                self.freshdesk.add_tag_to_ticket(ticket_id, 'needs-spam-review')
            
        except Exception as e:
            logger.error(f"Error handling spam ticket {ticket_id}: {e}")
    
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
