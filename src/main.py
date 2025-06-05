#!/usr/bin/env python3
"""
Freshdesk Spam Filter with OpenAI AI Integration

This application monitors Freshdesk tickets and uses a local OpenAI model
to automatically detect and handle spam tickets.
"""

import logging
import time
import schedule
import sys
from datetime import datetime
from colorama import init, Fore, Style
from .config import Config
from .spam_filter import SpamFilter

# Initialize colorama for colored output
init()

def setup_logging():
    """Setup logging configuration"""
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler('spam_filter.log')
    file_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger

def print_banner():
    """Print application banner"""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    FRESHDESK SPAM FILTER                     ║
║                   with OpenAI AI Integration                 ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}Configuration:{Style.RESET_ALL}
  • Freshdesk Domain: {Config.FRESHDESK_DOMAIN}
  • AI Model: OpenAI ({Config.OPENAI_MODEL_NAME})
  • Spam Threshold: {Config.SPAM_THRESHOLD}
  • Auto-Close Threshold: {Config.AUTO_CLOSE_SPAM_THRESHOLD}
  • Check Interval: {Config.CHECK_INTERVAL_MINUTES} minutes (for continuous mode)
  • Max Tickets/Batch: {Config.MAX_TICKETS_PER_BATCH} (for continuous mode)
  • Process New Tickets Only: {Config.PROCESS_NEW_TICKETS_ONLY}
  • Dry Run Mode (via --test): {Config.DRY_RUN_MODE}
  • Running in Lambda: {Config.IS_LAMBDA_ENVIRONMENT}

{Fore.YELLOW}Starting spam detection service...{Style.RESET_ALL}
"""
    print(banner)

def run_spam_detection(max_tickets: int = None):
    """Run a single spam detection cycle"""
    try:
        logger = logging.getLogger(__name__)
        if Config.DRY_RUN_MODE:
            logger.info("DRY RUN MODE: Starting spam detection cycle. No changes will be made.")
        else:
            logger.info("Starting spam detection cycle...")
        
        # Initialize spam filter
        spam_filter = SpamFilter()
        
        # Process tickets
        # Use max_tickets if provided, otherwise it defaults to Config.MAX_TICKETS_PER_BATCH in spam_filter.process_tickets
        stats = spam_filter.process_tickets(limit=max_tickets)
        
        # Print results
        print(f"\n{Fore.GREEN}Spam Detection Results (NEW tickets only):{Style.RESET_ALL}")
        print(f"  • Total Processed: {stats['total_processed']}")
        print(f"  • Spam Detected: {Fore.RED}{stats['spam_detected']}{Style.RESET_ALL}")
        print(f"  • Legitimate: {Fore.GREEN}{stats['legitimate']}{Style.RESET_ALL}")
        print(f"  • Already Processed: {Fore.CYAN}{stats.get('skipped_already_processed', 0)}{Style.RESET_ALL}")
        print(f"  • Errors: {Fore.YELLOW}{stats['errors']}{Style.RESET_ALL}")
        
        if stats['spam_detected'] > 0:
            print(f"\n{Fore.RED}⚠️  {stats['spam_detected']} spam ticket(s) detected and handled!{Style.RESET_ALL}")
        
        # Get overall statistics
        overall_stats = spam_filter.get_spam_statistics()
        if 'error' not in overall_stats:
            print(f"\n{Fore.CYAN}Overall Statistics:{Style.RESET_ALL}")
            print(f"  • Total Tickets in System: {overall_stats['total_tickets_checked']}")
            print(f"  • Spam Tagged Tickets: {overall_stats['spam_tagged_tickets']}")
            print(f"  • Auto-Detected Spam: {overall_stats['auto_detected_spam']}")
        
        logger.info(f"Spam detection cycle completed: {stats}")
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in spam detection cycle: {e}")
        print(f"\n{Fore.RED}❌ Error in spam detection: {e}{Style.RESET_ALL}")

def run_once():
    """Run spam detection once and exit"""
    print(f"{Fore.YELLOW}Running spam detection once for a single ticket...{Style.RESET_ALL}")
    run_spam_detection(max_tickets=1)
    print(f"\n{Fore.GREEN}✅ Single run completed.{Style.RESET_ALL}")

def run_continuous():
    """Run spam detection continuously"""
    print(f"{Fore.YELLOW}Starting continuous monitoring...{Style.RESET_ALL}")
    print(f"Press Ctrl+C to stop.\n")
    
    # Schedule the spam detection
    schedule.every(Config.CHECK_INTERVAL_MINUTES).minutes.do(run_spam_detection)
    
    # Run initial check
    run_spam_detection()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopping spam filter...{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Spam filter stopped.{Style.RESET_ALL}")

def show_help():
    """Show help information"""
    help_text = f"""
{Fore.CYAN}Freshdesk Spam Filter - Usage{Style.RESET_ALL}

{Fore.GREEN}Commands:{Style.RESET_ALL}
  python main.py                 - Run continuously (default, polls Freshdesk)
  python main.py --once          - Run once for a batch of tickets and exit
  python main.py --test          - Run in DRY RUN mode (no actual changes to Freshdesk, can be combined with --once or continuous)
  python main.py --help          - Show this help

{Fore.GREEN}Configuration (via .env file):{Style.RESET_ALL}
  Copy .env.example to .env and configure your settings:
  • FRESHDESK_DOMAIN: Your Freshdesk subdomain (e.g., yourcompany)
  • FRESHDESK_API_KEY: Your Freshdesk API key
  • OPENAI_API_KEY: Your OpenAI API key
  • OPENAI_MODEL_NAME: AI model to use (e.g., gpt-3.5-turbo)
  • See CONFIGURATION.md for all options (thresholds, agent ID, etc.)

{Fore.GREEN}Setup (for local execution):{Style.RESET_ALL}
  1. Ensure Python 3.8+ is installed.
  2. Create a virtual environment: python3 -m venv venv && source venv/bin/activate
  3. Install dependencies: pip install -r requirements.txt
  4. Configure .env file with your Freshdesk and OpenAI credentials.
  5. Run the application (e.g., python main.py)

{Fore.YELLOW}Note:{Style.RESET_ALL} For production, AWS Lambda deployment is recommended (see DEPLOYMENT.md).
"""
    print(help_text)

def main():
    """Main application entry point"""
    try:
        # Setup logging
        logger = setup_logging()
        
        # Check command line arguments
        if len(sys.argv) > 1:
            if '--help' in sys.argv or '-h' in sys.argv:
                show_help()
                return
            elif '--once' in sys.argv:
                # Check for --test in conjunction with --once
                if '--test' in sys.argv:
                    Config.DRY_RUN_MODE = True
                    print(f"{Fore.MAGENTA}INFO: Running in DRY RUN (--test) mode. No changes will be made to Freshdesk.{Style.RESET_ALL}")
                Config.validate()
                print_banner()
                run_once()
                return
            elif '--test' in sys.argv: # Handle --test for continuous mode
                Config.DRY_RUN_MODE = True
                print(f"{Fore.MAGENTA}INFO: Running in DRY RUN (--test) mode. No changes will be made to Freshdesk.{Style.RESET_ALL}")
                # Proceed to validation and continuous run
        
        # Validate configuration
        Config.validate()
        
        # Print banner
        print_banner()
        
        # Run continuously
        run_continuous()
        
    except ValueError as e:
        print(f"{Fore.RED}❌ Configuration Error: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please check your .env file and ensure all required fields are set.{Style.RESET_ALL}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application interrupted by user.{Style.RESET_ALL}")
        sys.exit(0)
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error: {e}")
        print(f"{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
