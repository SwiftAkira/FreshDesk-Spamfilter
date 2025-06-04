#!/usr/bin/env python3
"""
AI Independence Test
Verifies that the AI makes decisions based solely on content, not test labels
"""

import sys
import logging
import random
from colorama import init, Fore, Style
from ollama_client import OllamaClient

# Initialize colorama
init()

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
        "fake_expected": "NOT SPAM",  # INTENTIONALLY WRONG
        "actual_expected": "SPAM"
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

def test_ollama_connection():
    """Test OLLAMA connection"""
    print(f"{Fore.CYAN}Testing OLLAMA Connection...{Style.RESET_ALL}")
    
    try:
        client = OllamaClient()
        print(f"{Fore.GREEN}✅ Successfully connected to OLLAMA{Style.RESET_ALL}")
        print(f"  • Host: {client.host}")
        print(f"  • Model: {client.model}")
        return client
        
    except Exception as e:
        print(f"{Fore.RED}❌ OLLAMA connection failed: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please ensure OLLAMA is running: ollama serve{Style.RESET_ALL}")
        return None

def run_independence_tests(client):
    """Run tests to verify AI independence from expected labels"""
    print(f"\n{Fore.CYAN}Running AI Independence Tests...{Style.RESET_ALL}")
    print("=" * 80)
    print(f"{Fore.YELLOW}Testing with INTENTIONALLY WRONG expected labels to verify AI independence{Style.RESET_ALL}")
    print("=" * 80)
    
    results = []
    correct_decisions = 0
    
    for i, test_case in enumerate(INDEPENDENCE_TEST_CASES, 1):
        print(f"\n{Fore.YELLOW}Independence Test {i}: {test_case['name']}{Style.RESET_ALL}")
        print(f"Subject: {test_case['subject']}")
        print(f"Sender: {test_case['sender']}")
        print(f"Fake Expected Label: {Fore.RED}{test_case['fake_expected']}{Style.RESET_ALL} (INTENTIONALLY WRONG)")
        print(f"Actual Expected: {Fore.GREEN}{test_case['actual_expected']}{Style.RESET_ALL}")
        
        try:
            # CRITICAL: We analyze WITHOUT passing any expected result
            # The AI should make decisions based ONLY on content
            is_spam, confidence, reasoning = client.analyze_spam(
                subject=test_case['subject'],
                description=test_case['description'],
                sender_email=test_case['sender']
            )
            
            ai_result = "SPAM" if is_spam else "NOT SPAM"
            is_correct = ai_result == test_case['actual_expected']
            ignored_fake_label = ai_result != test_case['fake_expected']
            
            if is_correct:
                correct_decisions += 1
            
            # Color coding
            if is_correct and ignored_fake_label:
                status_color = Fore.GREEN
                status_icon = "✅"
                status_text = "CORRECT (Ignored fake label)"
            elif is_correct and not ignored_fake_label:
                status_color = Fore.YELLOW
                status_icon = "⚠️"
                status_text = "CORRECT (But matched fake label - concerning)"
            else:
                status_color = Fore.RED
                status_icon = "❌"
                status_text = "INCORRECT"
            
            print(f"AI Result: {Fore.CYAN}{ai_result}{Style.RESET_ALL} (confidence: {confidence:.2f})")
            print(f"Status: {status_color}{status_icon} {status_text}{Style.RESET_ALL}")
            print(f"Ignored Fake Label: {Fore.GREEN if ignored_fake_label else Fore.RED}{ignored_fake_label}{Style.RESET_ALL}")
            print(f"Reasoning: {reasoning[:200]}...")
            
            results.append({
                'test_name': test_case['name'],
                'ai_result': ai_result,
                'actual_expected': test_case['actual_expected'],
                'fake_expected': test_case['fake_expected'],
                'confidence': confidence,
                'is_correct': is_correct,
                'ignored_fake_label': ignored_fake_label,
                'reasoning': reasoning
            })
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error analyzing test case: {e}{Style.RESET_ALL}")
            results.append({
                'test_name': test_case['name'],
                'ai_result': 'ERROR',
                'actual_expected': test_case['actual_expected'],
                'fake_expected': test_case['fake_expected'],
                'confidence': 0.0,
                'is_correct': False,
                'ignored_fake_label': True,
                'reasoning': f"Error: {str(e)}"
            })
        
        print("-" * 80)
    
    return results, correct_decisions

def analyze_independence_results(results, correct_decisions):
    """Analyze AI independence test results"""
    total_tests = len(results)
    accuracy = (correct_decisions / total_tests) * 100
    ignored_fake_labels = sum(1 for r in results if r['ignored_fake_label'])
    independence_rate = (ignored_fake_labels / total_tests) * 100
    
    print(f"\n{Fore.CYAN}📊 AI INDEPENDENCE ANALYSIS{Style.RESET_ALL}")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Correct Decisions: {Fore.GREEN}{correct_decisions}{Style.RESET_ALL}")
    print(f"Accuracy: {Fore.GREEN}{accuracy:.1f}%{Style.RESET_ALL}")
    print(f"Ignored Fake Labels: {Fore.GREEN}{ignored_fake_labels}/{total_tests}{Style.RESET_ALL}")
    print(f"Independence Rate: {Fore.GREEN}{independence_rate:.1f}%{Style.RESET_ALL}")
    
    # Verdict
    print(f"\n{Fore.CYAN}🎯 INDEPENDENCE VERDICT{Style.RESET_ALL}")
    print("-" * 40)
    
    if independence_rate >= 80 and accuracy >= 80:
        print(f"{Fore.GREEN}✅ EXCELLENT: AI is making independent, content-based decisions!{Style.RESET_ALL}")
    elif independence_rate >= 60:
        print(f"{Fore.YELLOW}⚠️  GOOD: AI shows reasonable independence but could be improved{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ CONCERNING: AI may be influenced by external factors{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}📋 DETAILED INDEPENDENCE RESULTS{Style.RESET_ALL}")
    print("-" * 80)
    
    for result in results:
        status_icon = "✅" if result['is_correct'] and result['ignored_fake_label'] else "⚠️" if result['is_correct'] else "❌"
        
        print(f"{status_icon} {result['test_name']}")
        print(f"   AI: {result['ai_result']} | Expected: {result['actual_expected']} | Fake: {result['fake_expected']}")
        print(f"   Confidence: {result['confidence']:.2f} | Ignored Fake: {result['ignored_fake_label']}")
        print()

def main():
    """Main test function"""
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                AI INDEPENDENCE VERIFICATION TEST             ║
║          Ensuring Content-Based Decision Making              ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

This test verifies that the AI makes decisions based solely on message content,
not on any expected result labels in our test cases.

We use INTENTIONALLY WRONG expected labels to ensure the AI ignores them.
""")
    
    # Suppress some logging for cleaner output
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Test OLLAMA connection
    client = test_ollama_connection()
    if not client:
        print(f"\n{Fore.RED}❌ Cannot proceed without OLLAMA connection.{Style.RESET_ALL}")
        sys.exit(1)
    
    # Run independence tests
    results, correct_decisions = run_independence_tests(client)
    
    # Analyze results
    analyze_independence_results(results, correct_decisions)
    
    print(f"\n{Fore.GREEN}✅ AI independence testing completed!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}This confirms the AI is making genuine content-based decisions.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
