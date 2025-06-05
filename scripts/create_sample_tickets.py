import requests
import random
import string
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file (primarily for API_KEY)
load_dotenv()

# --- Configuration for this script ---
# Freshdesk subdomain is hardcoded here to ensure correct URL construction for this script.
FRESHDESK_SUBDOMAIN = 'onair' 
API_KEY = os.getenv('FRESHDESK_API_KEY')
# --- End Configuration ---

# Base URL for the API - constructed using the hardcoded subdomain
BASE_URL = f'https://{FRESHDESK_SUBDOMAIN}.freshdesk.com/api/v2/tickets'

# Headers for the request
headers = {
    'Content-Type': 'application/json'
}

# Sample spam-like subjects and descriptions
spam_subjects = [
    "Win a Free iPhone Now!",
    "Congratulations! You've won a prize",
    "Limited Time Offer: Act Now",
    "Earn $5000 per week from home",
    "Your account has been compromised",
    "URGENT: Security Alert - Action Required!",
    "Claim Your Free Bitcoin Today!",
    "You are a Winner! Click Here",
    "Hot Singles in Your Area Waiting For You",
    "Make Money Fast - Guaranteed Results!"
]

spam_descriptions = [
    "Click here to claim your reward: http://spamlink.com/iphone-offer",
    "Urgent: Update your account information immediately by visiting http://phishingsite.net/update",
    "Exclusive deal just for you, don't miss out! Visit www.scamdeal.org now.",
    "You've been selected for a special offer. Provide your details at http://datathief.com/special",
    "Act fast to secure your winnings! Go to http://totallynotavirus.com/winner",
    "Your online banking profile has suspicious activity. Verify at http://fakebanklogin.com immediately.",
    "Double your investment in 24 hours! Send Bitcoin to 1SpAmAdDrEsS...",
    "To receive your $1,000,000 USD, please provide your bank account details and a small processing fee to http://getrichquickscam.com.",
    "Lonely hearts are waiting. Sign up for free at http://malwaredating.com and find your match!",
    "Learn the secret to earning $10,000 a month with no effort. Download our ebook from http://randomdownload.info/secret."
]

# Function to generate a random email address
def generate_random_email():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    domain = random.choice([
        'spamdomain.com', 'malicious.org', 'phishing.net', 'fakedelivery.com',
        'winbig.org', 'freestuff.net', 'secure-update.com', 'lotterywinner.info'
    ])
    return f"{username}@{domain}"

# Number of spam tickets to create
number_of_tickets = 10

print(f"Attempting to create {number_of_tickets} sample spam tickets on Freshdesk domain: {FRESHDESK_SUBDOMAIN}.freshdesk.com")

if not API_KEY:
    print("\n--- ERROR ---")
    print("FRESHDESK_API_KEY not found in your .env file or environment variables.")
    print("Please ensure FRESHDESK_API_KEY is correctly set in your .env file.")
    print("Script will not run without the API key.")
    exit()

created_count = 0
failed_count = 0

# Make copies of lists to allow removal during iteration without affecting original lists
current_spam_subjects = list(spam_subjects)
current_spam_descriptions = list(spam_descriptions)

for i in range(number_of_tickets):
    if not current_spam_subjects: # Replenish if empty
        current_spam_subjects = list(spam_subjects)
    subject = random.choice(current_spam_subjects)
    current_spam_subjects.remove(subject)
      
    if not current_spam_descriptions: # Replenish if empty
        current_spam_descriptions = list(spam_descriptions)
    description = random.choice(current_spam_descriptions)
    current_spam_descriptions.remove(description)

    email = generate_random_email()

    data = {
        "email": email,
        "subject": subject,
        "description": description,
        "status": 2,  # Open
        "priority": 1  # Low
    }

    print(f"\nCreating ticket {i+1}/{number_of_tickets} with subject: '{subject}' from email: {email}")

    try:
        response = requests.post(
            BASE_URL, # Uses the globally defined BASE_URL
            auth=(API_KEY, 'X'), # 'X' is a placeholder for password when using API key
            headers=headers,
            json=data,
            timeout=10 # Adding a timeout
        )

        if response.status_code == 201:
            print(f"  SUCCESS: Ticket created. ID: {response.json().get('id')}, Subject: {subject}")
            created_count += 1
        else:
            print(f"  FAILED to create ticket: {response.status_code} - {response.text}")
            failed_count += 1
            
    except requests.exceptions.RequestException as e:
        print(f"  ERROR creating ticket {i+1}: {e}")
        failed_count += 1
    
    # Brief pause to avoid overwhelming the API
    if i < number_of_tickets - 1: # Pause after each request except the last one
        time.sleep(1) # 1 second pause between requests

print(f"\n--- Summary ---")
print(f"Successfully created tickets: {created_count}")
print(f"Failed to create tickets: {failed_count}")
print("Script finished.") 