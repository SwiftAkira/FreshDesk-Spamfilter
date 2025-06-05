#!/usr/bin/env python3
"""
Standalone AI Spam Detection Test
Tests the OpenAI AI spam detection without requiring Freshdesk connection.
Ensure your .env file is configured with OPENAI_API_KEY and OPENAI_MODEL_NAME.
"""

import sys
import logging
from colorama import init, Fore, Style
from src.openai_client import OpenAIClient
from src.config import Config

# Initialize colorama
init()

# Configure basic logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test cases with various types of messages - based on real examples
TEST_CASES = [
    {
        "name": "Mobile App Development Spam",
        "subject": "Custom Mobile App Development Services",
        "description": """Hi,

Are you interested in a mobile app for Android, iOS, or iPad?

I create custom apps based on your needs. Feel free to share your idea or the type of app you want.

Looking forward to your reply!

Best regards,

Innayat""",
        "sender": "innayat.dev@gmail.com",
        "expected": "SPAM"
    },
    {
        "name": "Legitimate Order Issue",
        "subject": "T-shirt order still not received after 3 weeks",
        "description": """Hello Bruno,

I was delighted to read your message. Unfortunately I have to report that the t-shirt has still not arrived almost 3 weeks later.

So what now?

Best regards,

Martin""",
        "sender": "martin.customer@email.com",
        "expected": "NOT SPAM"
    },
    {
        "name": "SEO Services Spam",
        "subject": "Boost Your Website Rankings - Free SEO Audit",
        "description": """Dear Website Owner,

I hope this email finds you well. I came across your website and noticed it has great potential but could benefit from improved search engine visibility.

We specialize in helping businesses like yours achieve:
- First page Google rankings
- Increased organic traffic
- Higher conversion rates
- Better online presence

I'd like to offer you a FREE comprehensive SEO audit worth $500. This audit will show you exactly what's holding your website back and how we can fix it.

Our proven strategies have helped over 1,000+ businesses improve their rankings. We guarantee results within 90 days or your money back.

Would you be interested in a quick 15-minute call to discuss your goals?

Best regards,
Sarah Johnson
Digital Marketing Specialist
SEO Masters Inc.
Phone: +1-555-0123""",
        "sender": "sarah@seo-masters.com",
        "expected": "SPAM"
    },
    {
        "name": "Password Reset Request",
        "subject": "Password reset assistance needed",
        "description": """Hi Support Team,

I'm having trouble accessing my account and need help with resetting my password. I've tried using the "Forgot Password" link multiple times, but I'm not receiving any reset emails.

I've checked my spam folder and confirmed my email address is correct: jennifer.smith@company.org

My account details:
- Username: jsmith2024
- Last login: approximately 2 weeks ago
- Account type: Premium subscriber since 2022

Could you please help me regain access to my account? I have important files stored there that I need for work.

Thank you for your assistance.

Best regards,
Jennifer Smith""",
        "sender": "jennifer.smith@company.org",
        "expected": "NOT SPAM"
    },
    {
        "name": "Cryptocurrency Investment Spam",
        "subject": "Turn $500 into $50,000 with Bitcoin Trading",
        "description": """Hello Future Millionaire!

My name is Alex Rodriguez and I'm a professional cryptocurrency trader who has made MILLIONS using a secret trading algorithm.

I'm now sharing this EXCLUSIVE system with a select few people who are serious about financial freedom.

Here's what you'll get:
✅ My personal trading bot that works 24/7
✅ Step-by-step video training course
✅ Live trading signals sent to your phone
✅ 1-on-1 mentorship calls with me personally
✅ 100% money-back guarantee

PROOF: I turned $1,000 into $100,000 in just 30 days!

This offer is only available for the next 48 hours. After that, I'm closing enrollment forever.

Don't miss this life-changing opportunity!

Click here to secure your spot: www.crypto-millions-system.com/join

To your success,
Alex Rodriguez
Crypto Trading Expert""",
        "sender": "alex@crypto-millions.com",
        "expected": "SPAM"
    },
    {
        "name": "Billing Inquiry",
        "subject": "Question about recent charge on my account",
        "description": """Dear Billing Department,

I noticed a charge of $89.99 on my credit card statement from your company dated March 15th, but I cannot find any corresponding invoice or service in my account dashboard.

Could you please help me understand what this charge is for? Here are my account details:

Account ID: ACC-789456
Email: robert.wilson@techcorp.com
Credit card ending in: 4567

I've been a customer for over 3 years and this is the first time I've encountered this issue. I'd appreciate a detailed breakdown of what this charge covers.

If this is an error, please let me know how we can resolve it. If it's a legitimate charge, I'd like to understand what service or product it's for.

Thank you for your time and assistance.

Best regards,
Robert Wilson
Senior Developer
TechCorp Solutions""",
        "sender": "robert.wilson@techcorp.com",
        "expected": "NOT SPAM"
    },
    {
        "name": "Web Design Services Spam",
        "subject": "Professional Website Design - Special Offer",
        "description": """Greetings!

I hope you're doing well. I'm reaching out because I noticed your website could use some improvements to better represent your business.

My name is David and I'm a professional web designer with 8+ years of experience. I've helped hundreds of businesses create stunning, modern websites that convert visitors into customers.

Here's what I can do for you:
• Complete website redesign
• Mobile-responsive design
• SEO optimization
• Fast loading speeds
• Professional copywriting
• Social media integration
• E-commerce functionality

SPECIAL OFFER: This month only, I'm offering a complete website package for just $499 (normally $1,500).

I'd love to show you some examples of my work and discuss how I can help grow your business online.

Are you available for a brief call this week?

Best regards,
David Thompson
Web Design Professional
Portfolio: www.daviddesigns.net
Phone: (555) 123-4567""",
        "sender": "david@webdesignpro.net",
        "expected": "SPAM"
    },
    {
        "name": "Technical Support Request",
        "subject": "API integration error - urgent assistance needed",
        "description": """Hello Technical Support,

I'm experiencing a critical issue with our API integration that's affecting our production environment. The error started occurring this morning around 9:00 AM EST.

Error details:
- Error code: API_TIMEOUT_ERROR
- Endpoint: /api/v2/users/authenticate
- HTTP Status: 504 Gateway Timeout
- Frequency: Approximately 60% of requests

This is impacting our user authentication system and preventing customers from logging in. We've tried the following troubleshooting steps:

1. Verified our API credentials are correct
2. Checked our firewall settings
3. Tested from multiple IP addresses
4. Reviewed our request rate limits

Our development team is standing by to implement any fixes you recommend. This is affecting our business operations, so any expedited assistance would be greatly appreciated.

Technical contact: dev-team@ourcompany.com
Account ID: API-CLIENT-7891
Environment: Production

Please let me know if you need any additional information.

Thanks,
Michael Chen
Lead Developer
OurCompany Inc.""",
        "sender": "michael.chen@ourcompany.com",
        "expected": "NOT SPAM"
    }
]

def run_spam_detection_tests(client: OpenAIClient):
    """Run spam detection tests on various message types"""
    print(f"\n{Fore.CYAN}Running AI Spam Detection Tests using OpenAI ({client.model_name})...{Style.RESET_ALL}")
    print("=" * 80)
    
    results = []
    correct_predictions = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{Fore.YELLOW}Test {i}: {test_case['name']}{Style.RESET_ALL}")
        print(f"Subject: {test_case['subject']}")
        print(f"Sender: {test_case['sender']}")
        print(f"Expected: {test_case['expected']}")
        
        try:
            is_spam_ai, confidence, reasoning = client.analyze_spam(
                subject=test_case['subject'],
                description=test_case['description'],
                sender_email=test_case['sender'],
                is_system_validated=False
            )
            
            prediction = "SPAM" if is_spam_ai else "NOT SPAM"
            
            print(f"AI Prediction: {Fore.GREEN if prediction == test_case['expected'] else Fore.RED}{prediction}{Style.RESET_ALL}")
            print(f"Confidence: {confidence:.2f}")
            print(f"Reasoning: {reasoning}")
            
            test_result = {
                "name": test_case['name'],
                "expected": test_case['expected'],
                "prediction": prediction,
                "confidence": confidence,
                "reasoning": reasoning,
                "correct": prediction == test_case['expected']
            }
            results.append(test_result)
            
            if test_result["correct"]:
                correct_predictions += 1
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error during AI analysis: {e}{Style.RESET_ALL}")
            results.append({
                "name": test_case['name'],
                "expected": test_case['expected'],
                "prediction": "ERROR",
                "correct": False,
                "error": str(e)
            })
            
    return results, correct_predictions

def print_summary(results, correct_predictions):
    """Print summary of test results"""
    total_tests = len(TEST_CASES)
    accuracy = (correct_predictions / total_tests) * 100 if total_tests > 0 else 0
    
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}AI SPAM DETECTION TEST SUMMARY{Style.RESET_ALL}")
    print("=" * 80)
    
    for result in results:
        status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if result["correct"] else f"{Fore.RED}FAIL{Style.RESET_ALL}"
        if result["prediction"] == "ERROR":
            status = f"{Fore.RED}ERROR{Style.RESET_ALL}"
        print(f"Test: {result['name']:<30} | Expected: {result['expected']:<10} | Prediction: {result['prediction']:<10} | Status: {status}")
        if result["prediction"] == "ERROR":
            print(f"  └─ Error: {result.get('error')}")
        elif not result["correct"]:
            print(f"  └─ Reasoning: {result.get('reasoning', 'N/A')}")


    print("-" * 80)
    print(f"{Fore.CYAN}Overall Accuracy: {correct_predictions}/{total_tests} ({accuracy:.2f}%){Style.RESET_ALL}")
    print("=" * 80)

def main():
    """Main function to run tests"""
    print(f"{Fore.BLUE}Starting AI Spam Detection Test Suite...{Style.RESET_ALL}")
    
    # Load configuration to ensure API keys and model names are available
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
        results, correct_count = run_spam_detection_tests(ai_client)
        print_summary(results, correct_count)
    else:
        logger.error(f"{Fore.RED}AI Client not initialized. Cannot run tests.{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
