#!/usr/bin/env python3
"""
Test script to verify Freshdesk and OLLAMA setup
"""

import sys
import logging
from colorama import init, Fore, Style
from config import Config

# Initialize colorama
init()

def test_configuration():
    """Test configuration validity"""
    print(f"{Fore.CYAN}Testing Configuration...{Style.RESET_ALL}")
    
    try:
        Config.validate()
        print(f"{Fore.GREEN}✅ Configuration is valid{Style.RESET_ALL}")
        
        print(f"  • Freshdesk Domain: {Config.FRESHDESK_DOMAIN}")
        print(f"  • OLLAMA Host: {Config.OLLAMA_HOST}")
        print(f"  • OLLAMA Model: {Config.OLLAMA_MODEL}")
        print(f"  • Spam Threshold: {Config.SPAM_THRESHOLD}")
        
        return True
        
    except ValueError as e:
        print(f"{Fore.RED}❌ Configuration Error: {e}{Style.RESET_ALL}")
        return False

def test_freshdesk_connection():
    """Test Freshdesk API connection"""
    print(f"\n{Fore.CYAN}Testing Freshdesk Connection...{Style.RESET_ALL}")
    
    try:
        from freshdesk_client import FreshdeskClient
        
        client = FreshdeskClient()
        
        # Try to fetch a small number of tickets
        tickets = client.get_tickets(limit=1)
        
        print(f"{Fore.GREEN}✅ Successfully connected to Freshdesk{Style.RESET_ALL}")
        print(f"  • API URL: {client.base_url}")
        print(f"  • Test fetch returned {len(tickets)} ticket(s)")
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Freshdesk connection failed: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please check your FRESHDESK_DOMAIN and FRESHDESK_API_KEY{Style.RESET_ALL}")
        return False

def test_ollama_connection():
    """Test OLLAMA connection"""
    print(f"\n{Fore.CYAN}Testing OLLAMA Connection...{Style.RESET_ALL}")
    
    try:
        from ollama_client import OllamaClient
        
        client = OllamaClient()
        
        # Test with a simple spam analysis
        is_spam, confidence, reasoning = client.analyze_spam(
            subject="Test Subject",
            description="This is a test message to verify OLLAMA is working.",
            sender_email="test@example.com"
        )
        
        print(f"{Fore.GREEN}✅ Successfully connected to OLLAMA{Style.RESET_ALL}")
        print(f"  • Host: {client.host}")
        print(f"  • Model: {client.model}")
        print(f"  • Test analysis result: spam={is_spam}, confidence={confidence:.2f}")
        print(f"  • Reasoning: {reasoning}")
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ OLLAMA connection failed: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please ensure OLLAMA is running and the model is available{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Try: ollama serve (in another terminal){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Try: ollama pull {Config.OLLAMA_MODEL}{Style.RESET_ALL}")
        return False

def test_spam_filter():
    """Test the complete spam filter"""
    print(f"\n{Fore.CYAN}Testing Complete Spam Filter...{Style.RESET_ALL}")
    
    try:
        from spam_filter import SpamFilter
        
        spam_filter = SpamFilter()
        
        # Get statistics
        stats = spam_filter.get_spam_statistics()
        
        if 'error' in stats:
            print(f"{Fore.YELLOW}⚠️  Could not get full statistics: {stats['error']}{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}✅ Spam filter is working{Style.RESET_ALL}")
            print(f"  • Total tickets in system: {stats.get('total_tickets_checked', 'N/A')}")
            print(f"  • Previously tagged spam: {stats.get('spam_tagged_tickets', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Spam filter test failed: {e}{Style.RESET_ALL}")
        return False

def main():
    """Run all tests"""
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    SETUP VERIFICATION TEST                   ║
║                   Freshdesk Spam Filter                      ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
    
    # Suppress some logging for cleaner output
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    tests = [
        ("Configuration", test_configuration),
        ("Freshdesk Connection", test_freshdesk_connection),
        ("OLLAMA Connection", test_ollama_connection),
        ("Complete System", test_spam_filter),
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
        print(f"\n{Fore.GREEN}🎉 All tests passed! Your spam filter is ready to use.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Run 'python main.py' to start the spam filter.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ Some tests failed. Please fix the issues above before running the spam filter.{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
