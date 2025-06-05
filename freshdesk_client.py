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
            # First attempt: try to include the description
            url = f"{self.base_url}/tickets/{ticket_id}"
            params = {'include': 'description'}
            
            logger.debug(f"Fetching ticket {ticket_id} with description included.")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # If the first attempt failed, check if it was a 400 Bad Request
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 400:
                logger.info(f"Fetching ticket {ticket_id} with include=description failed with 400 Bad Request. Retrying without include=description.")
                try:
                    # Second attempt: fetch without including the description
                    # The URL is the same, just no params
                    response_no_desc = self.session.get(url) # No params here
                    response_no_desc.raise_for_status()
                    logger.info(f"Successfully fetched ticket {ticket_id} without include=description after initial 400 error.")
                    return response_no_desc.json()
                except requests.exceptions.RequestException as e2:
                    logger.error(f"Error fetching ticket {ticket_id} on second attempt (without include=description): {e2}")
                    # Raise the error from the second attempt, as it's the more specific failure after a retry
                    raise e2 
            else:
                # If it was not a 400 error, or no response object, re-raise the original error
                logger.error(f"Error fetching ticket {ticket_id} (original attempt): {e}")
                raise e

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
        if Config.DRY_RUN_MODE:
            logger.info(f"DRY RUN MODE: Would update ticket #{ticket_id} with: {updates}")
            # In dry run, we should return the current state of the ticket or a representation
            # to allow the calling logic to proceed smoothly.
            try:
                return self.get_ticket(ticket_id) # Return current ticket data
            except Exception as e:
                logger.warning(f"DRY RUN MODE: Could not fetch ticket #{ticket_id} for simulated update response: {e}")
                return {"id": ticket_id, **updates} # Fallback to a simple dict

        try:
            url = f"{self.base_url}/tickets/{ticket_id}"
            
            logger.debug(f"Updating ticket {ticket_id} with: {updates}")
            response = self.session.put(url, json=updates)
            response.raise_for_status()
            
            logger.info(f"Successfully updated ticket {ticket_id}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                error_content = "No response content"
                try:
                    error_content = e.response.json() # Try to parse as JSON
                except ValueError: # If not JSON
                    error_content = e.response.text # Fallback to text
                logger.error(f"Error updating ticket {ticket_id}. Status: {e.response.status_code}, Response: {error_content}, Original Error: {e}")
            else:
                logger.error(f"Error updating ticket {ticket_id}: {e} (No response object)")
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
        if Config.DRY_RUN_MODE:
            logger.info(f"DRY RUN MODE: Would attempt to add tag '{tag}' to ticket #{ticket_id}. Checking current tags first.")
            # Simulate fetching current ticket for tag checking
            try:
                ticket = self.get_ticket(ticket_id) # get_ticket is read-only, safe in dry run
                current_tags = ticket.get('tags', [])
                if tag not in current_tags:
                    logger.info(f"DRY RUN MODE: Tag '{tag}' not present. Update to ticket #{ticket_id} would be simulated by update_ticket.")
                    # The call to update_ticket below will handle its own dry run logic
                else:
                    logger.info(f"DRY RUN MODE: Tag '{tag}' already exists on ticket #{ticket_id}. No update would be attempted.")
                    return ticket # Return current ticket data
            except Exception as e:
                logger.warning(f"DRY RUN MODE: Could not fetch ticket #{ticket_id} to check tags: {e}")
                # If we can't get the ticket, assume we'd try to add the tag
                logger.info(f"DRY RUN MODE: Assuming update for tag '{tag}' on ticket #{ticket_id} would be simulated by update_ticket.")
                # The call to update_ticket below will handle its own dry run logic

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
        Mark a ticket as spam by assigning to an agent, updating its tags, and then status.
        Operations are performed in sequence: Assign Agent -> Update Tags -> Update Status.
        
        Args:
            ticket_id: The ticket ID to mark as spam
            
        Returns:
            The final updated ticket dictionary (after status update).
        """
        agent_id_to_assign = 80059226092 # Agent ID for "Ria No"

        if Config.DRY_RUN_MODE:
            logger.info(f"DRY RUN MODE: Simulating marking ticket #{ticket_id} as spam.")
            try:
                ticket_for_dry_run = self.get_ticket(ticket_id)
                current_tags_dry_run = ticket_for_dry_run.get('tags', [])
                current_responder_id = ticket_for_dry_run.get('responder_id')
            except Exception:
                ticket_for_dry_run = {} # Ensure it's a dict for merging
                current_tags_dry_run = []
                current_responder_id = None

            spam_tags_to_add = ['spam', 'auto-detected']
            exclusive_tag_dry_run = ['Auto-Spam-Detected']

            if current_responder_id != agent_id_to_assign:
                logger.info(f"DRY RUN MODE: Would assign ticket #{ticket_id} to agent ID: {agent_id_to_assign}")
            else:
                logger.info(f"DRY RUN MODE: Ticket #{ticket_id} already assigned to agent ID: {agent_id_to_assign}. No assignment change.")

            # DRY RUN: Tags will be set exclusively
            logger.info(f"DRY RUN MODE: Would set tags for ticket #{ticket_id} exclusively to: {exclusive_tag_dry_run}")
            logger.info(f"DRY RUN MODE: Would update status for ticket #{ticket_id} to: 5 (Spam/Closed)")
            
            final_simulated_ticket = {
                "id": ticket_id, 
                "responder_id": agent_id_to_assign,
                "tags": exclusive_tag_dry_run, 
                "status": 5
            }
            # Merge with other existing fields if possible to make the simulation more complete
            final_simulated_ticket = {**ticket_for_dry_run, **final_simulated_ticket}
            return final_simulated_ticket

        try:
            # Step 1: Assign to Agent
            logger.info(f"Marking ticket {ticket_id} as spam: Step 1 - Assigning to agent ID {agent_id_to_assign}.")
            current_ticket_state = self.get_ticket(ticket_id) # Get current state to check if already assigned
            if current_ticket_state.get('responder_id') != agent_id_to_assign:
                ticket_after_agent_assign = self.update_ticket(ticket_id, {'responder_id': agent_id_to_assign})
            else:
                logger.info(f"Ticket {ticket_id} already assigned to agent ID {agent_id_to_assign}. Skipping agent assignment.")
                ticket_after_agent_assign = current_ticket_state

            # Step 2: Update Tags - Set exclusively to ['Auto-Spam-Detected']
            logger.info(f"Marking ticket {ticket_id} as spam: Step 2 - Setting tags exclusively to ['Auto-Spam-Detected'].")
            exclusive_tag = ['Auto-Spam-Detected']
            # We always attempt to set this exclusive tag, overwriting others if necessary.
            logger.info(f"Setting tags for ticket {ticket_id} to: {exclusive_tag}")
            ticket_after_tags_update = self.update_ticket(ticket_id, {'tags': exclusive_tag})
            
            # Step 3: Update Status
            logger.info(f"Marking ticket {ticket_id} as spam: Step 3 - Updating status to 5 (Spam/Closed).")
            final_updated_ticket = self.update_ticket(ticket_id, {'status': 5})
            
            logger.info(f"Successfully marked ticket {ticket_id} as spam (agent assigned, tags and status updated).")
            return final_updated_ticket
            
        except Exception as e:
            logger.error(f"Error marking ticket {ticket_id} as spam: {e}")
            raise

    def add_note_to_ticket(self, ticket_id: int, note_body: str, private: bool = True) -> Dict:
        """
        Add a note to a ticket.

        Args:
            ticket_id: The ticket ID.
            note_body: The content of the note.
            private: Whether the note should be private (default True).

        Returns:
            The API response dictionary for the created note.
        """
        if Config.DRY_RUN_MODE:
            logger.info(f"DRY RUN MODE: Would add {'private' if private else 'public'} note to ticket #{ticket_id} with body: '{note_body[:100]}...'")
            # Simulate a successful note creation response
            return {
                "id": 0, # Placeholder ID for the note
                "body": note_body,
                "private": private,
                "ticket_id": ticket_id,
                "user_id": 0, # Placeholder user ID
                "created_at": "DRY_RUN_TIMESTAMP",
                "updated_at": "DRY_RUN_TIMESTAMP"
            }

        try:
            url = f"{self.base_url}/tickets/{ticket_id}/notes"
            payload = {
                "body": note_body,
                "private": private
            }
            logger.info(f"Adding {'private' if private else 'public'} note to ticket #{ticket_id}")
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            logger.debug(f"Successfully added note to ticket {ticket_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error adding note to ticket {ticket_id}: {e}")
            raise
