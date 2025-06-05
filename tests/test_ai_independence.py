#!/usr/bin/env python3
"""
AI Independence Test
Verifies that the OpenAI AI makes decisions based solely on content,
ignoring any hypothetical or mislabeled 'expected' outcomes provided in test data structures.
Ensure your .env file is configured with OPENAI_API_KEY and OPENAI_MODEL_NAME.
"""

import sys
import logging
import random
from colorama import init, Fore, Style
from src.openai_client import OpenAIClient
from src.config import Config

# Initialize colorama
init()

# Configure basic logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test cases with intentionally WRONG expected labels to verify AI independence
INDEPENDENCE_TEST_CASES = [
    {
        "name": "Clear Spam with WRONG 'NOT SPAM' Label",
        "subject": "🎉 URGENT: Claim Your $10,000 Prize NOW!",
        "description": """CONGRATULATIONS!!! 

You have been selected as our GRAND PRIZE WINNER! You've won $10,000 CASH!

To claim your prize, click here IMMEDIATELY: http://fake-lottery-scam.com/claim

This offer expires in 24 HOURS! Don't miss out on this AMAZING opportunity!

Enter your personal information to claim:
- Full name
- Social Security Number  
- Bank account details
- Credit card information

ACT NOW before it's too late!

Lottery Commission (TOTALLY LEGIT)""",
        "sender": "winner@fake-lottery.com",
        "fake_expected": "NOT SPAM",  # INTENTIONALLY WRONG for test structure
        "actual_expected": "SPAM" # The true nature of the content
    },
    {
        "name": "Legitimate Support with WRONG 'SPAM' Label", 
        "subject": "Critical production server outage - immediate assistance needed",
        "description": """Hello Support Team,

We are experiencing a critical production server outage that started at 3:47 AM EST. Our main application server (srv-prod-01) is completely unresponsive.

Impact:
- All customer-facing services are down
- Approximately 50,000 users affected
- Revenue impact: ~$5,000 per hour

Technical details:
- Server IP: 10.0.1.15
- Last known status: HTTP 500 errors
- Database connections: Timing out
- Load balancer health checks: Failing

Actions taken:
1. Attempted server restart - failed
2. Checked network connectivity - normal
3. Reviewed system logs - see attached
4. Escalated to on-call engineer

Account Information:
- Company: TechCorp Industries
- Account ID: TC-789456
- Support Plan: Enterprise 24/7
- Primary Contact: james.wilson@techcorp.com

This is a P1 incident requiring immediate attention. Please contact me at (555) 123-4567.

James Wilson
Senior DevOps Engineer
TechCorp Industries""",
        "sender": "james.wilson@techcorp.com",
        "fake_expected": "SPAM",  # INTENTIONALLY WRONG
        "actual_expected": "NOT SPAM"
    },
    {
        "name": "Obvious Phishing with WRONG 'NOT SPAM' Label",
        "subject": "URGENT: Your account will be deleted in 24 hours",
        "description": """SECURITY ALERT!!!

Your account has been COMPROMISED and will be PERMANENTLY DELETED in 24 hours unless you take immediate action!

Suspicious activity detected:
- Multiple failed login attempts
- Unauthorized access from foreign IP addresses
- Potential data breach

IMMEDIATE ACTION REQUIRED:
Click this link NOW to verify your identity: http://phishing-site-123.com/verify-account

You MUST enter the following information to prevent account deletion:
- Username and password
- Social Security Number
- Credit card details
- Mother's maiden name

WARNING: Failure to verify within 24 hours will result in permanent account closure and loss of all data!

Security Team (Definitely Real)
security@totally-legit-company.com""",
        "sender": "security@fake-company.com",
        "fake_expected": "NOT SPAM",  # INTENTIONALLY WRONG
        "actual_expected": "SPAM"
    },
    {
        "name": "Real Customer Complaint with WRONG 'SPAM' Label",
        "subject": "Defective product received - requesting refund",
        "description": """Dear Customer Service,

I am writing to report a defective product I received and to request a full refund.

Order Details:
- Order Number: ORD-456789
- Product: Wireless Bluetooth Headphones Model XH-200
- Order Date: March 10, 2024
- Delivery Date: March 15, 2024

Issue Description:
The headphones I received have several defects:
1. Left speaker produces no sound
2. Bluetooth connection drops every 2-3 minutes
3. Charging case lid is cracked
4. Product appears to be a returned/refurbished item despite ordering new

I have attempted basic troubleshooting:
- Reset the device multiple times
- Tried connecting to different devices
- Checked for firmware updates

The product is clearly defective and not as described. I would like to return it for a full refund as per your 30-day return policy.

Please provide return instructions and a prepaid shipping label.

Customer Information:
- Name: Lisa Rodriguez
- Email: lisa.rodriguez@email.com
- Phone: (555) 987-6543
- Address: 123 Main St, Anytown, ST 12345

I look forward to your prompt response.

Sincerely,
Lisa Rodriguez""",
        "sender": "lisa.rodriguez@email.com",
        "fake_expected": "SPAM",  # INTENTIONALLY WRONG
        "actual_expected": "NOT SPAM"
    },
    {
        "name": "Crypto Scam with WRONG 'NOT SPAM' Label",
        "subject": "Exclusive Bitcoin Investment Opportunity - 500% Returns Guaranteed!",
        "description": """Hello Future Millionaire!

I am Dr. Michael Thompson, a former Wall Street executive who discovered a SECRET Bitcoin trading algorithm that GUARANTEES 500% returns in just 30 days!

PROOF OF SUCCESS:
- Turned $1,000 into $50,000 in one month
- Over 10,000 satisfied customers
- Featured on CNN, Forbes, and Bloomberg (totally true!)

LIMITED TIME OFFER:
For the next 48 hours ONLY, I'm sharing this exclusive system with 100 lucky people.

What you get:
✅ My personal trading bot (worth $10,000)
✅ 24/7 automated trading
✅ GUARANTEED 500% returns or money back
✅ Personal mentorship from me
✅ Access to secret crypto insider information

SPECIAL PRICE: Only $497 (normally $5,000)

But HURRY! This offer expires in 47 hours and 23 minutes!

Click here to secure your spot: http://crypto-scam-guaranteed.com/join-now

Don't let this life-changing opportunity pass you by!

To your inevitable success,
Dr. Michael Thompson
Crypto Trading Genius
(Definitely not a scammer)""",
        "sender": "dr.thompson@crypto-millions.com",
        "fake_expected": "NOT SPAM",  # INTENTIONALLY WRONG
        "actual_expected": "SPAM"
    }
]

def run_independence_tests(client: OpenAIClient):
    """Run tests to verify AI independence from any hypothetical 'expected' labels in test data."""
    print(f"\n{Fore.CYAN}Running AI Independence Tests using OpenAI ({client.model_name})...{Style.RESET_ALL}")
    print("=" * 80)
    print(f"{Fore.YELLOW}These tests verify the AI classifies content based on its nature, not by comparing to any stored 'expected' label within the test case structure.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}The 'fake_expected' label is part of the test data structure ONLY to highlight what the AI should ignore.{Style.RESET_ALL}")
    print("=" * 80)
    
    results = []
    correct_decisions = 0 # Based on actual_expected
    
    for i, test_case in enumerate(INDEPENDENCE_TEST_CASES, 1):
        print(f"\n{Fore.MAGENTA}Independence Test {i}: {test_case['name']}{Style.RESET_ALL}")
        print(f"Subject: {test_case['subject']}")
        # print(f"Description: {test_case['description'][:100]}...")
        print(f"Sender: {test_case['sender']}")
        print(f"Structure's Fake Expected Label: {Fore.RED}{test_case['fake_expected']}{Style.RESET_ALL} (This is for test structure, AI does NOT see this)")
        print(f"Actual Nature of Content: {Fore.GREEN}{test_case['actual_expected']}{Style.RESET_ALL} (This is what AI prediction is compared against)")
        
        try:
            is_spam_ai, confidence, reasoning = client.analyze_spam(
                subject=test_case['subject'],
                description=test_case['description'],
                sender_email=test_case['sender'],
                is_system_validated=False # Assuming these general tests are not system validated
            )
            
            ai_prediction = "SPAM" if is_spam_ai else "NOT SPAM"
            # Correctness is determined if AI prediction matches the *actual* nature of the content
            is_correct_based_on_actual = ai_prediction == test_case['actual_expected']
            
            if is_correct_based_on_actual:
                correct_decisions += 1
            
            print(f"AI Prediction: {Fore.GREEN if is_correct_based_on_actual else Fore.RED}{ai_prediction}{Style.RESET_ALL}")
            print(f"Confidence: {confidence:.2f}")
            print(f"Reasoning: {reasoning}")
            
            status_text = "" 
            if is_correct_based_on_actual:
                status_text = f"{Fore.GREEN}PASS (Correctly classified as {ai_prediction}){Style.RESET_ALL}"
            else:
                status_text = f"{Fore.RED}FAIL (Incorrectly classified as {ai_prediction}, should be {test_case['actual_expected']}){Style.RESET_ALL}"
            print(f"Status: {status_text}")

            results.append({
                "name": test_case['name'],
                "actual_expected": test_case['actual_expected'],
                "fake_expected_in_test_data": test_case['fake_expected'],
                "ai_prediction": ai_prediction,
                "confidence": confidence,
                "reasoning": reasoning,
                "correct_based_on_actual": is_correct_based_on_actual
            })
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error during AI analysis: {e}{Style.RESET_ALL}")
            results.append({
                "name": test_case['name'],
                "actual_expected": test_case['actual_expected'],
                "fake_expected_in_test_data": test_case['fake_expected'],
                "ai_prediction": "ERROR",
                "correct_based_on_actual": False,
                "error": str(e)
            })
        print("-" * 80)
            
    return results, correct_decisions

def analyze_independence_results(results, correct_decisions):
    """Analyze and print the summary of independence tests."""
    total_tests = len(INDEPENDENCE_TEST_CASES)
    accuracy = (correct_decisions / total_tests) * 100 if total_tests > 0 else 0
    
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}AI INDEPENDENCE TEST SUMMARY{Style.RESET_ALL}")
    print("=" * 80)
    
    for result in results:
        status_color = Fore.GREEN if result["correct_based_on_actual"] else Fore.RED
        status_icon = "✅" if result["correct_based_on_actual"] else "❌"
        
        if result["ai_prediction"] == "ERROR":
            status_color = Fore.RED
            status_icon = "❗"

        print(f"{status_icon} Test: {result['name']:<50}")
        print(f"    Actual Nature: {result['actual_expected']:<10} | AI Predicted: {status_color}{result['ai_prediction']:<10}{Style.RESET_ALL}")
        if result["ai_prediction"] == "ERROR":
            print(f"    Error: {result.get('error')}")
        elif not result["correct_based_on_actual"]:
             print(f"    Reasoning: {result.get('reasoning', 'N/A')}")
        print("-" * 50)

    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}Overall Correct Classifications (based on actual content nature): {correct_decisions}/{total_tests} ({accuracy:.2f}%){Style.RESET_ALL}")
    if correct_decisions == total_tests:
        print(f"{Fore.GREEN}Excellent! The AI correctly classified all items based on their actual content, ignoring misleading labels in test data.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Review any failed tests. The AI should classify based on content, not test structure.{Style.RESET_ALL}")
    print("=" * 80)

def main():
    """Main function to run tests"""
    print(f"{Fore.BLUE}Starting AI Independence Test Suite...{Style.RESET_ALL}")
    
    try:
        Config.validate()
        logger.info("Configuration validated.")
    except ValueError as e:
        logger.error(f"{Fore.RED}❌ Configuration Error: {e}{Style.RESET_ALL}")
        logger.error(f"{Fore.YELLOW}Please ensure OPENAI_API_KEY is set in your .env file.{Style.RESET_ALL}")
        sys.exit(1)

    ai_client = None
    try:
        ai_client = OpenAIClient()
        logger.info(f"OpenAIClient initialized with model: {ai_client.model_name}")
    except Exception as e:
        logger.error(f"{Fore.RED}❌ Failed to initialize OpenAIClient: {e}{Style.RESET_ALL}")
        logger.error(f"{Fore.YELLOW}Ensure OPENAI_API_KEY is correctly set in .env and you have network access.{Style.RESET_ALL}")
        sys.exit(1)

    if ai_client:
        results, correct_decisions = run_independence_tests(ai_client)
        analyze_independence_results(results, correct_decisions)
    else:
        logger.error(f"{Fore.RED}AI Client not initialized. Cannot run tests.{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
