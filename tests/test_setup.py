#!/usr/bin/env python3
"""
Test script to verify Freshdesk and OpenAI setup
"""

import sys
import logging
from colorama import init, Fore, Style
from src.config import Config
from src.freshdesk_client import FreshdeskClient
from src.openai_client import OpenAIClient
from src.spam_filter import SpamFilter

# Initialize colorama
init()

def test_configuration():
    """Test configuration validity"""
    print(f"{Fore.CYAN}Testing Configuration...{Style.RESET_ALL}")
    
    try:
        Config.validate() # This checks for FRESHDESK_DOMAIN, FRESHDESK_API_KEY, OPENAI_API_KEY
        print(f"{Fore.GREEN}✅ Required configurations are present (according to Config.validate()){Style.RESET_ALL}")
        
        print(f"  • Freshdesk Domain: {Config.FRESHDESK_DOMAIN}")
        # OPENAI_API_KEY is validated by Config.validate() but not printed for security.
        print(f"  • OpenAI API Key: {Fore.GREEN}{'Present' if Config.OPENAI_API_KEY else Fore.RED + 'Missing'}{Style.RESET_ALL}")
        print(f"  • OpenAI Model: {Config.OPENAI_MODEL_NAME}")
        print(f"  • Spam Threshold: {Config.SPAM_THRESHOLD}")
        print(f"  • Auto-Close Threshold: {Config.AUTO_CLOSE_SPAM_THRESHOLD}")
        
        return True
        
    except ValueError as e:
        print(f"{Fore.RED}❌ Configuration Error: {e}{Style.RESET_ALL}")
        return False

def test_freshdesk_connection():
    """Test Freshdesk API connection"""
    print(f"\n{Fore.CYAN}Testing Freshdesk Connection...{Style.RESET_ALL}")
    
    try:
        client = FreshdeskClient()
        
        # Try to fetch a small number of tickets
        # This also implicitly tests Config.get_freshdesk_url()
        tickets = client.get_tickets(limit=1)
        
        print(f"{Fore.GREEN}✅ Successfully connected to Freshdesk{Style.RESET_ALL}")
        print(f"  • API URL: {client.base_url}")
        print(f"  • Test fetch returned {len(tickets)} ticket(s)")
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Freshdesk connection failed: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please check your FRESHDESK_DOMAIN and FRESHDESK_API_KEY in .env file.{Style.RESET_ALL}")
        return False

def test_openai_client_initialization():
    """Test OpenAIClient initialization"""
    print(f"\n{Fore.CYAN}Testing OpenAI Client Initialization...{Style.RESET_ALL}")
    
    if not Config.OPENAI_API_KEY:
        print(f"{Fore.RED}❌ OpenAI API Key is missing in configuration.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please set OPENAI_API_KEY in your .env file.{Style.RESET_ALL}")
        return False
        
    try:
        client = OpenAIClient() # Initialization depends on Config (API key, model)
        
        print(f"{Fore.GREEN}✅ Successfully initialized OpenAIClient{Style.RESET_ALL}")
        print(f"  • Configured Model: {client.model_name}")
        # No actual API call is made here to conserve quota for a setup test.
        # Successful initialization implies API key is available via Config.
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ OpenAIClient initialization failed: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please ensure OPENAI_API_KEY is correctly set in .env and a valid OPENAI_MODEL_NAME is specified.{Style.RESET_ALL}")
        return False

def test_spam_filter_initialization():
    """Test the SpamFilter class initialization"""
    print(f"\n{Fore.CYAN}Testing SpamFilter Class Initialization...{Style.RESET_ALL}")
    
    try:
        spam_filter = SpamFilter() # Initializes FreshdeskClient and OpenAIClient
        
        print(f"{Fore.GREEN}✅ SpamFilter class initialized successfully.{Style.RESET_ALL}")
        print(f"  • AI Client in SpamFilter: {type(spam_filter.ai_client).__name__}")
        print(f"  • Spam Threshold in SpamFilter: {spam_filter.spam_threshold}")
        
        # Optionally, a light test of get_spam_statistics if it doesn't depend on live processing too much
        # For now, just initialization is fine for a setup test.
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ SpamFilter class initialization failed: {e}{Style.RESET_ALL}")
        return False

def main():
    """Run all tests"""
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    SETUP VERIFICATION TEST                   ║
║              Freshdesk Spam Filter with OpenAI               ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
    
    # Suppress some common library logging for cleaner test output
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING) # Added for OpenAI library
    
    tests = [
        ("Configuration Variables", test_configuration),
        ("Freshdesk Connection", test_freshdesk_connection),
        ("OpenAI Client Initialization", test_openai_client_initialization),
        ("SpamFilter Class Initialization", test_spam_filter_initialization),
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
        print(f"\n{Fore.GREEN}🎉 All setup checks passed! Your spam filter seems ready.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Ensure your .env file is correctly configured for API keys and desired behavior.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}To run locally: python main.py{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}For Lambda deployment, see DEPLOYMENT.MD.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ Some setup checks failed. Please review the errors above.{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
