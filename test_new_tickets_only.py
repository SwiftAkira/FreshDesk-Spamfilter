#!/usr/bin/env python3
"""
Test New Tickets Only Functionality
Tests that the spam filter only processes new tickets and first customer messages
"""

import sys
import logging
from colorama import init, Fore, Style
from unittest.mock import Mock, patch

# Initialize colorama
init()

def test_new_ticket_filtering():
    """Test that only new tickets are processed"""
    print(f"{Fore.CYAN}Testing New Ticket Filtering...{Style.RESET_ALL}")
    
    try:
        from freshdesk_client import FreshdeskClient
        
        # Test the actual filtering logic without mocking the method
        # We'll mock the HTTP response instead
        with patch('requests.Session.get') as mock_get:
            # Simulate mixed ticket statuses from API
            mock_tickets = [
                {'id': 1, 'status': 2, 'subject': 'New ticket', 'created_at': '2024-01-01T10:00:00Z'},  # New
                {'id': 2, 'status': 3, 'subject': 'Pending ticket', 'created_at': '2024-01-01T09:00:00Z'},  # Pending
                {'id': 3, 'status': 2, 'subject': 'Another new ticket', 'created_at': '2024-01-01T11:00:00Z'},  # New
                {'id': 4, 'status': 4, 'subject': 'Resolved ticket', 'created_at': '2024-01-01T08:00:00Z'},  # Resolved
            ]

            # Mock the HTTP response
            mock_response = Mock()
            mock_response.json.return_value = mock_tickets
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            client = FreshdeskClient()

            # Test with only_new=True (default)
            new_tickets = client.get_tickets(only_new=True, limit=10)

            print(f"  • Total mock tickets: {len(mock_tickets)}")
            print(f"  • New tickets returned: {len(new_tickets)}")
            print(f"  • Expected new tickets: 2 (status=2)")

            # Verify only status 2 tickets are returned
            new_ticket_ids = [t['id'] for t in new_tickets]
            expected_ids = [1, 3]  # Only tickets with status 2

            if new_ticket_ids == expected_ids:
                print(f"  {Fore.GREEN}✅ Correctly filtered new tickets only{Style.RESET_ALL}")
                return True
            else:
                print(f"  {Fore.RED}❌ Filter failed. Got: {new_ticket_ids}, Expected: {expected_ids}{Style.RESET_ALL}")
                return False
                
    except Exception as e:
        print(f"  {Fore.RED}❌ Error testing new ticket filtering: {e}{Style.RESET_ALL}")
        return False

def test_first_customer_message_extraction():
    """Test extraction of first customer message only"""
    print(f"\n{Fore.CYAN}Testing First Customer Message Extraction...{Style.RESET_ALL}")
    
    try:
        from freshdesk_client import FreshdeskClient
        
        # Mock the Freshdesk client
        with patch.object(FreshdeskClient, 'get_ticket') as mock_get_ticket, \
             patch.object(FreshdeskClient, 'get_ticket_conversations') as mock_get_conversations:
            
            # Mock ticket data
            mock_ticket = {
                'id': 123,
                'subject': 'Help with login issue',
                'description': 'Original ticket description',
                'requester_id': 456,
                'created_at': '2024-01-01T10:00:00Z'
            }
            
            # Mock conversations - mix of customer and agent messages
            mock_conversations = [
                {
                    'id': 1,
                    'body_text': 'This is the first customer message with the actual issue details.',
                    'body': '<p>This is the first customer message with the actual issue details.</p>',
                    'private': False,
                    'incoming': True,  # Customer message
                    'created_at': '2024-01-01T10:00:00Z'
                },
                {
                    'id': 2,
                    'body_text': 'This is an agent response to the customer.',
                    'body': '<p>This is an agent response to the customer.</p>',
                    'private': False,
                    'incoming': False,  # Agent message
                    'created_at': '2024-01-01T10:30:00Z'
                },
                {
                    'id': 3,
                    'body_text': 'This is a private note between agents.',
                    'body': '<p>This is a private note between agents.</p>',
                    'private': True,  # Private note
                    'incoming': False,
                    'created_at': '2024-01-01T11:00:00Z'
                },
                {
                    'id': 4,
                    'body_text': 'Customer follow-up message.',
                    'body': '<p>Customer follow-up message.</p>',
                    'private': False,
                    'incoming': True,  # Another customer message
                    'created_at': '2024-01-01T12:00:00Z'
                }
            ]
            
            mock_get_ticket.return_value = mock_ticket
            mock_get_conversations.return_value = mock_conversations
            
            client = FreshdeskClient()
            
            # Test first customer message extraction
            first_message = client.get_first_customer_message(123)
            
            print(f"  • Total conversations: {len(mock_conversations)}")
            print(f"  • First message ID: {first_message.get('conversation_id')}")
            print(f"  • First message content: {first_message.get('description')[:50]}...")
            
            # Verify we got the first customer message (ID 1)
            if (first_message.get('conversation_id') == 1 and 
                'first customer message' in first_message.get('description', '')):
                print(f"  {Fore.GREEN}✅ Correctly extracted first customer message{Style.RESET_ALL}")
                return True
            else:
                print(f"  {Fore.RED}❌ Failed to extract correct first customer message{Style.RESET_ALL}")
                return False
                
    except Exception as e:
        print(f"  {Fore.RED}❌ Error testing first customer message extraction: {e}{Style.RESET_ALL}")
        return False

def test_spam_filter_integration():
    """Test the complete spam filter with new ticket processing"""
    print(f"\n{Fore.CYAN}Testing Spam Filter Integration...{Style.RESET_ALL}")
    
    try:
        from spam_filter import SpamFilter
        from ollama_client import OllamaClient
        
        # Mock the OLLAMA client to avoid actual AI calls
        with patch.object(OllamaClient, 'analyze_spam') as mock_analyze:
            # Mock AI response
            mock_analyze.return_value = (False, 0.3, "This appears to be a legitimate support request")
            
            # Mock the Freshdesk methods
            with patch('spam_filter.FreshdeskClient') as mock_freshdesk_class:
                mock_freshdesk = Mock()
                mock_freshdesk_class.return_value = mock_freshdesk
                
                # Mock new tickets
                mock_freshdesk.get_tickets.return_value = [
                    {'id': 100, 'status': 2, 'subject': 'Test ticket', 'created_at': '2024-01-01T10:00:00Z'}
                ]
                
                # Mock first customer message
                mock_freshdesk.get_first_customer_message.return_value = {
                    'ticket_id': 100,
                    'subject': 'Test ticket',
                    'description': 'I need help with my account login',
                    'sender_email': 'customer@example.com',
                    'created_at': '2024-01-01T10:00:00Z',
                    'conversation_id': 1
                }
                
                # Create spam filter and process
                spam_filter = SpamFilter()
                stats = spam_filter.process_tickets(limit=5)
                
                print(f"  • Tickets processed: {stats['total_processed']}")
                print(f"  • Spam detected: {stats['spam_detected']}")
                print(f"  • Legitimate: {stats['legitimate']}")
                print(f"  • Errors: {stats['errors']}")
                
                # Verify the process worked
                if (stats['total_processed'] > 0 and 
                    stats['errors'] == 0 and
                    mock_freshdesk.get_tickets.called and
                    mock_freshdesk.get_first_customer_message.called):
                    print(f"  {Fore.GREEN}✅ Spam filter integration working correctly{Style.RESET_ALL}")
                    return True
                else:
                    print(f"  {Fore.RED}❌ Spam filter integration failed{Style.RESET_ALL}")
                    return False
                    
    except Exception as e:
        print(f"  {Fore.RED}❌ Error testing spam filter integration: {e}{Style.RESET_ALL}")
        return False

def main():
    """Run all tests"""
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║              NEW TICKETS ONLY - FUNCTIONALITY TEST          ║
║          Testing First Customer Message Processing           ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

This test verifies that the spam filter:
1. Only processes NEW tickets (status 2)
2. Only analyzes the FIRST customer message (not agent responses)
3. Skips private notes and agent communications
""")
    
    # Suppress some logging for cleaner output
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    tests = [
        ("New Ticket Filtering", test_new_ticket_filtering),
        ("First Customer Message Extraction", test_first_customer_message_extraction),
        ("Spam Filter Integration", test_spam_filter_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{Fore.RED}❌ {test_name} test crashed: {e}{Style.RESET_ALL}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{Fore.CYAN}Test Summary:{Style.RESET_ALL}")
    all_passed = True
    
    for test_name, passed in results:
        status = f"{Fore.GREEN}✅ PASS" if passed else f"{Fore.RED}❌ FAIL"
        print(f"  • {test_name}: {status}{Style.RESET_ALL}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n{Fore.GREEN}🎉 All tests passed! New ticket filtering is working correctly.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}The spam filter will now only process:{Style.RESET_ALL}")
        print(f"  • NEW tickets (status 2 = Open)")
        print(f"  • FIRST customer messages only")
        print(f"  • No agent responses or private notes")
    else:
        print(f"\n{Fore.RED}❌ Some tests failed. Please review the implementation.{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
