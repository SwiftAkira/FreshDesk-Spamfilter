#!/usr/bin/env python3
"""
Edge Case Spam Detection Test
Tests challenging and ambiguous cases with OpenAI to observe classification behavior.
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

# Challenging edge cases - intentionally ambiguous
EDGE_CASES = [
    {
        "name": "Legitimate Business Inquiry (Appears Promotional)",
        "subject": "Partnership Opportunity - Integration with Your Platform",
        "description": """Dear Team,

I hope this message finds you well. My name is Sarah Chen, and I'm the Business Development Manager at DataFlow Solutions, a established data analytics company serving Fortune 500 clients.

We've been following your platform's growth and are impressed with your API capabilities. We believe there could be a mutually beneficial partnership opportunity.

Our clients frequently request integrations with platforms like yours, and we'd like to explore:
- Technical integration possibilities
- Revenue sharing models
- Joint marketing opportunities

We currently process over 2 million data points daily for clients like Microsoft, Adobe, and Tesla. A partnership could bring significant value to both organizations.

Would you be available for a brief call next week to discuss this further? I'm happy to share more details about our company and specific integration requirements.

Best regards,
Sarah Chen
Business Development Manager
DataFlow Solutions
sarah.chen@dataflow-solutions.com
LinkedIn: linkedin.com/in/sarahchen-bd""",
        "sender": "sarah.chen@dataflow-solutions.com",
        "expected_observation": "BORDERLINE - Could be legitimate business inquiry or sophisticated spam"
    },
    {
        "name": "Automated System Notification (Suspicious Elements)",
        "subject": "Security Alert: Unusual Login Activity Detected",
        "description": """SECURITY NOTIFICATION

We detected unusual login activity on your account from the following location:
- IP Address: 192.168.1.100
- Location: Amsterdam, Netherlands
- Device: Chrome Browser on Windows 10
- Time: March 20, 2024 at 14:32 UTC

If this was you, no action is required. If you don't recognize this activity, please:

1. Change your password immediately
2. Review your account settings
3. Enable two-factor authentication

For immediate assistance, contact our security team:
Email: security@platform-alerts.com
Phone: +1-800-SECURITY

This is an automated message. Please do not reply to this email.

Account Security Team
Platform Security Division""",
        "sender": "noreply@platform-alerts.com",
        "expected_observation": "BORDERLINE - Could be legitimate security alert or phishing attempt"
    },
    {
        "name": "Follow-up Customer Message (No Context)",
        "subject": "Following up on our conversation",
        "description": """Hi there,

I wanted to follow up on our conversation from last week. As discussed, I'm still interested in moving forward with the proposal we talked about.

Could you please send me the updated pricing information and timeline we discussed? I need to present this to my team by Friday.

Also, do you have availability for a quick call this week to finalize the details?

Thanks for your time and looking forward to hearing from you soon.

Best,
Alex Thompson
Senior Manager
alex.thompson@corporate-email.com""",
        "sender": "alex.thompson@corporate-email.com",
        "expected_observation": "BORDERLINE - Could be legitimate follow-up or social engineering"
    },
    {
        "name": "Professional Networking (Borders on Solicitation)",
        "subject": "Connecting after the Tech Conference",
        "description": """Hello,

It was great meeting you at the TechCrunch Disrupt conference last week. I really enjoyed our conversation about AI implementation in customer service.

As mentioned, I'm the founder of ChatBot Innovations, and we specialize in helping companies like yours implement AI-powered customer support solutions. We've successfully deployed our platform for over 200+ companies, reducing support costs by an average of 40%.

I'd love to continue our conversation and show you how our solution could specifically benefit your customer support operations. We offer:

- Custom AI chatbot development
- Seamless integration with existing systems
- 24/7 multilingual support
- Advanced analytics and reporting

Would you be interested in a 20-minute demo call? I can show you exactly how we helped similar companies in your industry.

Looking forward to connecting further!

Best regards,
Mark Rodriguez
Founder & CEO
ChatBot Innovations
mark@chatbot-innovations.com
Direct: (555) 987-6543""",
        "sender": "mark@chatbot-innovations.com",
        "expected_observation": "BORDERLINE - Professional networking that becomes sales pitch"
    },
    {
        "name": "Mixed Legitimate and Promotional Content",
        "subject": "Thank you for your purchase + Special offer for loyal customers",
        "description": """Dear Valued Customer,

Thank you for your recent purchase of the Premium Analytics Package (Order #PA-78945). Your order has been processed and you should receive access credentials within 24 hours.

If you have any questions about setting up your account or need technical assistance, please don't hesitate to reach out to our support team at support@analytics-pro.com.

---

EXCLUSIVE OFFER FOR PREMIUM CUSTOMERS:

As a thank you for choosing our Premium package, we're excited to offer you early access to our new AI-Powered Insights module at a special 50% discount.

This advanced module includes:
✓ Predictive analytics capabilities
✓ Custom dashboard creation
✓ Advanced data visualization tools
✓ Priority customer support

This exclusive offer is valid until March 31st and is only available to our Premium customers.

Click here to upgrade: www.analytics-pro.com/ai-upgrade

Best regards,
Customer Success Team
Analytics Pro Solutions""",
        "sender": "orders@analytics-pro.com",
        "expected_observation": "BORDERLINE - Legitimate order confirmation mixed with promotional upsell"
    },
    {
        "name": "Vendor Inquiry (Professional but Unsolicited)",
        "subject": "Cloud Infrastructure Solutions for Your Growing Business",
        "description": """Good morning,

I hope this email finds you well. My name is Jennifer Walsh, and I'm a Solutions Architect at CloudTech Enterprise, a leading provider of cloud infrastructure services.

I came across your company profile and noticed you're experiencing rapid growth. Congratulations on your recent Series B funding round! 

Based on your company size and growth trajectory, I believe you might be facing some common infrastructure challenges:
- Scaling server capacity during peak usage
- Managing increasing data storage requirements
- Ensuring 99.9% uptime for critical applications
- Optimizing cloud costs as you scale

We've helped similar companies in your industry (SaaS, 50-200 employees) reduce their infrastructure costs by 30-45% while improving performance and reliability.

I'd like to offer you a complimentary infrastructure assessment where we can:
1. Analyze your current setup
2. Identify optimization opportunities
3. Provide a customized scaling roadmap

This assessment typically saves companies $50,000+ annually in infrastructure costs.

Would you be open to a brief 15-minute conversation to see if this might be valuable for your team?

Best regards,
Jennifer Walsh
Senior Solutions Architect
CloudTech Enterprise
jennifer.walsh@cloudtech-enterprise.com
Direct: (555) 234-5678""",
        "sender": "jennifer.walsh@cloudtech-enterprise.com",
        "expected_observation": "BORDERLINE - Professional vendor outreach with research, but still unsolicited"
    }
]

def run_edge_case_tests(client: OpenAIClient):
    """Run spam detection tests on edge cases"""
    print(f"\n{Fore.CYAN}Running Edge Case Spam Detection Tests using OpenAI ({client.model_name})...{Style.RESET_ALL}")
    print("=" * 80)
    print(f"{Fore.YELLOW}Note: These are intentionally ambiguous cases. Observe AI classification, confidence, and reasoning.{Style.RESET_ALL}")
    print("=" * 80)
    
    results = []
    
    for i, test_case in enumerate(EDGE_CASES, 1):
        print(f"\n{Fore.MAGENTA}Edge Case {i}: {test_case['name']}{Style.RESET_ALL}")
        print(f"Subject: {test_case['subject']}")
        print(f"Sender: {test_case['sender']}")
        print(f"Intended Observation: {test_case['expected_observation']}")
        
        try:
            is_spam_ai, confidence, reasoning = client.analyze_spam(
                subject=test_case['subject'],
                description=test_case['description'],
                sender_email=test_case['sender'],
                is_system_validated=False
            )
            
            ai_classification = "SPAM" if is_spam_ai else "NOT SPAM"
            
            confidence_level_str = "LOW"
            confidence_color = Fore.RED
            if confidence >= 0.8:
                confidence_level_str = "HIGH"
                confidence_color = Fore.GREEN
            elif confidence >= 0.5:
                confidence_level_str = "MEDIUM"
                confidence_color = Fore.YELLOW
            
            print(f"AI Classification: {Fore.CYAN}{ai_classification}{Style.RESET_ALL}")
            print(f"Confidence: {confidence_color}{confidence:.2f} ({confidence_level_str}){Style.RESET_ALL}")
            print(f"Reasoning: {reasoning}")
            
            results.append({
                'name': test_case['name'],
                'expected_observation': test_case['expected_observation'],
                'ai_classification': ai_classification,
                'confidence': confidence,
                'confidence_level': confidence_level_str,
                'reasoning': reasoning
            })
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error during AI analysis for edge case '{test_case['name']}': {e}{Style.RESET_ALL}")
            results.append({
                'name': test_case['name'],
                'expected_observation': test_case['expected_observation'],
                'ai_classification': 'ERROR',
                'error': str(e)
            })
        print("-" * 80)
            
    return results

def analyze_edge_case_results(results):
    """Analyze and print the summary of edge case tests (observational)."""
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}EDGE CASE TEST OBSERVATIONAL SUMMARY{Style.RESET_ALL}")
    print("=" * 80)
    
    if not results:
        print(f"{Fore.YELLOW}No edge case results to display.{Style.RESET_ALL}")
        return

    for result in results:
        print(f"{Fore.MAGENTA}Test Case: {result['name']}{Style.RESET_ALL}")
        print(f"  Expected Observation: {result['expected_observation']}")
        if result['ai_classification'] == 'ERROR':
            print(f"  AI Classification: {Fore.RED}ERROR - {result.get('error')}{Style.RESET_ALL}")
        else:
            print(f"  AI Classification: {Fore.CYAN}{result['ai_classification']}{Style.RESET_ALL}")
            print(f"  Confidence: {result.get('confidence', 0.0):.2f} ({result.get('confidence_level', 'N/A')})")
            print(f"  Reasoning: {result.get('reasoning', 'N/A')}")
        print("-" * 50)

    print("\n" + "=" * 80)
    print(f"{Fore.YELLOW}This test is observational. Review the AI's reasoning for each ambiguous case.{Style.RESET_ALL}")
    print("=" * 80)

def main():
    """Main function to run tests"""
    print(f"{Fore.BLUE}Starting Edge Case AI Spam Detection Test Suite...{Style.RESET_ALL}")
    
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
        edge_case_results = run_edge_case_tests(ai_client)
        analyze_edge_case_results(edge_case_results)
    else:
        logger.error(f"{Fore.RED}AI Client not initialized. Cannot run edge case tests.{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
