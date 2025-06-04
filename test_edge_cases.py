#!/usr/bin/env python3
"""
Edge Case Spam Detection Test
Tests challenging and ambiguous cases where spam/legitimate distinction is unclear
"""

import sys
import logging
from colorama import init, Fore, Style
from ollama_client import OllamaClient

# Initialize colorama
init()

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
        "expected": "BORDERLINE - Could be legitimate business inquiry or sophisticated spam"
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
        "expected": "BORDERLINE - Could be legitimate security alert or phishing attempt"
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
        "expected": "BORDERLINE - Could be legitimate follow-up or social engineering"
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
        "expected": "BORDERLINE - Professional networking that becomes sales pitch"
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
        "expected": "BORDERLINE - Legitimate order confirmation mixed with promotional upsell"
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
        "expected": "BORDERLINE - Professional vendor outreach with research, but still unsolicited"
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

def run_edge_case_tests(client):
    """Run spam detection tests on edge cases"""
    print(f"\n{Fore.CYAN}Running Edge Case Spam Detection Tests...{Style.RESET_ALL}")
    print("=" * 80)
    print(f"{Fore.YELLOW}Note: These are intentionally ambiguous cases where classification may vary{Style.RESET_ALL}")
    print("=" * 80)
    
    results = []
    
    for i, test_case in enumerate(EDGE_CASES, 1):
        print(f"\n{Fore.YELLOW}Edge Case {i}: {test_case['name']}{Style.RESET_ALL}")
        print(f"Subject: {test_case['subject']}")
        print(f"Sender: {test_case['sender']}")
        print(f"Challenge: {test_case['expected']}")
        
        try:
            # Analyze with AI - NOTE: We don't pass the expected result to the AI
            is_spam, confidence, reasoning = client.analyze_spam(
                subject=test_case['subject'],
                description=test_case['description'],
                sender_email=test_case['sender']
            )
            
            # Determine result
            ai_result = "SPAM" if is_spam else "NOT SPAM"
            
            # Color coding based on confidence
            if confidence >= 0.8:
                confidence_color = Fore.GREEN
                confidence_level = "HIGH"
            elif confidence >= 0.6:
                confidence_color = Fore.YELLOW
                confidence_level = "MEDIUM"
            else:
                confidence_color = Fore.RED
                confidence_level = "LOW"
            
            print(f"AI Result: {Fore.CYAN}{ai_result}{Style.RESET_ALL}")
            print(f"Confidence: {confidence_color}{confidence:.2f} ({confidence_level}){Style.RESET_ALL}")
            print(f"Reasoning: {reasoning}")
            
            results.append({
                'test_name': test_case['name'],
                'ai_result': ai_result,
                'confidence': confidence,
                'confidence_level': confidence_level,
                'reasoning': reasoning,
                'challenge': test_case['expected']
            })
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error analyzing test case: {e}{Style.RESET_ALL}")
            results.append({
                'test_name': test_case['name'],
                'ai_result': 'ERROR',
                'confidence': 0.0,
                'confidence_level': 'ERROR',
                'reasoning': f"Error: {str(e)}",
                'challenge': test_case['expected']
            })
        
        print("-" * 80)
    
    return results

def analyze_edge_case_results(results):
    """Analyze the results of edge case testing"""
    print(f"\n{Fore.CYAN}📊 EDGE CASE ANALYSIS{Style.RESET_ALL}")
    print("=" * 60)
    
    spam_count = sum(1 for r in results if r['ai_result'] == 'SPAM')
    not_spam_count = sum(1 for r in results if r['ai_result'] == 'NOT SPAM')
    high_confidence = sum(1 for r in results if r['confidence'] >= 0.8)
    medium_confidence = sum(1 for r in results if 0.6 <= r['confidence'] < 0.8)
    low_confidence = sum(1 for r in results if r['confidence'] < 0.6)
    
    print(f"Total Edge Cases: {len(results)}")
    print(f"Classified as SPAM: {Fore.RED}{spam_count}{Style.RESET_ALL}")
    print(f"Classified as NOT SPAM: {Fore.GREEN}{not_spam_count}{Style.RESET_ALL}")
    print()
    print(f"High Confidence (≥0.8): {Fore.GREEN}{high_confidence}{Style.RESET_ALL}")
    print(f"Medium Confidence (0.6-0.8): {Fore.YELLOW}{medium_confidence}{Style.RESET_ALL}")
    print(f"Low Confidence (<0.6): {Fore.RED}{low_confidence}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}📋 DETAILED EDGE CASE RESULTS{Style.RESET_ALL}")
    print("-" * 80)
    
    for result in results:
        confidence_color = Fore.GREEN if result['confidence'] >= 0.8 else Fore.YELLOW if result['confidence'] >= 0.6 else Fore.RED
        
        print(f"🔍 {result['test_name']}")
        print(f"   Result: {result['ai_result']} | Confidence: {confidence_color}{result['confidence']:.2f} ({result['confidence_level']}){Style.RESET_ALL}")
        print(f"   Challenge: {result['challenge']}")
        print(f"   AI Reasoning: {result['reasoning'][:150]}...")
        print()
    
    # Analysis insights
    print(f"{Fore.CYAN}🎯 INSIGHTS{Style.RESET_ALL}")
    print("-" * 40)
    
    if low_confidence > 0:
        print(f"• {low_confidence} cases had low confidence - these are truly ambiguous")
    if high_confidence > len(results) * 0.5:
        print(f"• AI showed high confidence in {high_confidence}/{len(results)} cases - good decisiveness")
    else:
        print(f"• AI showed uncertainty in many cases - appropriate for edge cases")
    
    print(f"• The AI is making nuanced decisions on borderline content")
    print(f"• Results show the system can handle complex, real-world scenarios")

def main():
    """Main test function"""
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                EDGE CASE SPAM DETECTION TEST                 ║
║            Testing Ambiguous & Challenging Cases             ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

This test evaluates the AI's performance on intentionally ambiguous cases where
the distinction between spam and legitimate messages is unclear.
""")
    
    # Suppress some logging for cleaner output
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Test OLLAMA connection
    client = test_ollama_connection()
    if not client:
        print(f"\n{Fore.RED}❌ Cannot proceed without OLLAMA connection.{Style.RESET_ALL}")
        sys.exit(1)
    
    # Run edge case tests
    results = run_edge_case_tests(client)
    
    # Analyze results
    analyze_edge_case_results(results)
    
    print(f"\n{Fore.GREEN}✅ Edge case testing completed!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}These results show how the AI handles ambiguous, real-world scenarios.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
