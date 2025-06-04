"""
Freshdesk API Client for ticket management
"""
import requests
import logging
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class FreshdeskClient:
    """Client for interacting with Freshdesk API"""
    
    def __init__(self):
        """Initialize the Freshdesk client"""
        self.base_url = Config.get_freshdesk_url()
        self.api_key = Config.FRESHDESK_API_KEY
        self.session = requests.Session()
        self.session.auth = (self.api_key, 'X')
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def get_tickets(self, status: Optional[str] = None, limit: int = 50, only_new: bool = True) -> List[Dict]:
        """
        Fetch tickets from Freshdesk

        Args:
            status: Filter by ticket status (e.g., 'open', 'pending', 'resolved')
            limit: Maximum number of tickets to fetch
            only_new: If True, only fetch tickets that are newly opened (status 2)

        Returns:
            List of ticket dictionaries
        """
        try:
            url = f"{self.base_url}/tickets"
            params = {
                'per_page': min(limit, 100),  # Freshdesk max is 100
                'include': 'description',  # Include description for spam analysis
                'order_by': 'created_at',  # Order by creation time
                'order_type': 'desc'  # Newest first
            }

            # If only_new is True, filter for newly opened tickets (status 2)
            if only_new:
                params['filter'] = 'new_and_my_open'  # This gets new tickets
            elif status:
                params['filter'] = status

            logger.info(f"Fetching tickets from Freshdesk: {url}")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            tickets = response.json()

            # Additional filtering for truly new tickets (status 2 = Open)
            if only_new:
                original_count = len(tickets)
                tickets = [ticket for ticket in tickets if ticket.get('status') == 2]
                logger.debug(f"Filtered {original_count} tickets down to {len(tickets)} new tickets (status=2)")

            logger.info(f"Successfully fetched {len(tickets)} tickets")
            return tickets

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching tickets from Freshdesk: {e}")
            raise
    
    def get_ticket(self, ticket_id: int) -> Dict:
        """
        Fetch a specific ticket by ID
        
        Args:
            ticket_id: The ticket ID to fetch
            
        Returns:
            Ticket dictionary
        """
        try:
            url = f"{self.base_url}/tickets/{ticket_id}"
            params = {'include': 'description'}
            
            logger.debug(f"Fetching ticket {ticket_id}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching ticket {ticket_id}: {e}")
            raise

    def get_ticket_conversations(self, ticket_id: int) -> List[Dict]:
        """
        Fetch all conversations for a specific ticket

        Args:
            ticket_id: The ticket ID to fetch conversations for

        Returns:
            List of conversation dictionaries
        """
        try:
            url = f"{self.base_url}/tickets/{ticket_id}/conversations"

            logger.debug(f"Fetching conversations for ticket {ticket_id}")
            response = self.session.get(url)
            response.raise_for_status()

            conversations = response.json()
            logger.debug(f"Found {len(conversations)} conversations for ticket {ticket_id}")
            return conversations

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching conversations for ticket {ticket_id}: {e}")
            raise

    def get_first_customer_message(self, ticket_id: int) -> Dict:
        """
        Get the first customer message from a ticket (not agent responses)

        Args:
            ticket_id: The ticket ID

        Returns:
            Dictionary containing the first customer message details
        """
        try:
            # Get the ticket details first
            ticket = self.get_ticket(ticket_id)

            # Get conversations to find the first customer message
            conversations = self.get_ticket_conversations(ticket_id)

            # Find the first message that's from a customer (not private, not from agent)
            first_customer_message = None

            for conversation in conversations:
                # Skip private notes (these are internal agent communications)
                if conversation.get('private', False):
                    continue

                # Skip if it's from an agent (incoming should be False for customer messages)
                if conversation.get('incoming', True) == False:
                    continue

                # This should be the first customer message
                first_customer_message = conversation
                break

            if first_customer_message:
                # Extract the message content
                subject = ticket.get('subject', '')
                description = first_customer_message.get('body_text', '') or first_customer_message.get('body', '')

                # Strip HTML tags if present
                if description and '<' in description:
                    import re
                    description = re.sub('<[^<]+?>', '', description)

                return {
                    'ticket_id': ticket_id,
                    'subject': subject,
                    'description': description,
                    'sender_email': ticket.get('requester_id'),  # We'll resolve this later if needed
                    'created_at': first_customer_message.get('created_at'),
                    'conversation_id': first_customer_message.get('id')
                }
            else:
                # Fallback to ticket description if no conversations found
                subject = ticket.get('subject', '')
                description = ticket.get('description_text', '') or ticket.get('description', '')

                if description and '<' in description:
                    import re
                    description = re.sub('<[^<]+?>', '', description)

                return {
                    'ticket_id': ticket_id,
                    'subject': subject,
                    'description': description,
                    'sender_email': ticket.get('requester_id'),
                    'created_at': ticket.get('created_at'),
                    'conversation_id': None
                }

        except Exception as e:
            logger.error(f"Error getting first customer message for ticket {ticket_id}: {e}")
            raise
    
    def update_ticket(self, ticket_id: int, updates: Dict) -> Dict:
        """
        Update a ticket with new information
        
        Args:
            ticket_id: The ticket ID to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated ticket dictionary
        """
        try:
            url = f"{self.base_url}/tickets/{ticket_id}"
            
            logger.debug(f"Updating ticket {ticket_id} with: {updates}")
            response = self.session.put(url, json=updates)
            response.raise_for_status()
            
            logger.info(f"Successfully updated ticket {ticket_id}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating ticket {ticket_id}: {e}")
            raise
    
    def add_tag_to_ticket(self, ticket_id: int, tag: str) -> Dict:
        """
        Add a tag to a ticket
        
        Args:
            ticket_id: The ticket ID
            tag: Tag to add
            
        Returns:
            Updated ticket dictionary
        """
        try:
            # First get current tags
            ticket = self.get_ticket(ticket_id)
            current_tags = ticket.get('tags', [])
            
            # Add new tag if not already present
            if tag not in current_tags:
                current_tags.append(tag)
                return self.update_ticket(ticket_id, {'tags': current_tags})
            else:
                logger.debug(f"Tag '{tag}' already exists on ticket {ticket_id}")
                return ticket
                
        except Exception as e:
            logger.error(f"Error adding tag to ticket {ticket_id}: {e}")
            raise
    
    def mark_as_spam(self, ticket_id: int) -> Dict:
        """
        Mark a ticket as spam
        
        Args:
            ticket_id: The ticket ID to mark as spam
            
        Returns:
            Updated ticket dictionary
        """
        try:
            # Add spam tag and update status
            updates = {
                'status': 5,  # Status 5 is typically 'Closed'
                'tags': ['spam', 'auto-detected']
            }
            
            logger.info(f"Marking ticket {ticket_id} as spam")
            return self.update_ticket(ticket_id, updates)
            
        except Exception as e:
            logger.error(f"Error marking ticket {ticket_id} as spam: {e}")
            raise
