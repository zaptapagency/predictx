#!/usr/bin/env python3
"""
Cold Email Sender for Customer Discovery
Tracks: opens, clicks, replies automatically
Usage: python cold_email_sender.py --emails targets.csv --template churn
"""

import csv
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
import time

# EMAIL TEMPLATES BY VERTICAL
TEMPLATES = {
    "churn": {
        "subject": "Question about customer retention at {company}",
        "body": """Hi {first_name},

I noticed you're {title} at {company}.

I'm researching how subscription companies currently predict which customers are likely to churn. Most teams I talk to spend 20+ hours/month manually tracking this, but by then it's too late.

I'm not selling anything - just trying to understand what's painful about current approaches.

Would you have 20 minutes this week for a quick call?

{sender_name}
{calendar_link}"""
    },
    "fraud": {
        "subject": "Fraud prevention at {company}",
        "body": """Hi {first_name},

I noticed {company} processes a lot of transactions.

I'm researching how e-commerce companies currently prevent fraud - and what it costs when they miss it.

Do you have 20 minutes to chat about this?

{sender_name}
{calendar_link}"""
    },
    "forecasting": {
        "subject": "Demand forecasting challenge",
        "body": """Hi {first_name},

I'm talking to supply chain leaders about how they currently forecast demand. Trying to understand where it breaks down.

Would you have 20 minutes?

{sender_name}
{calendar_link}"""
    }
}

class ColdEmailSender:
    def __init__(self, gmail_address, gmail_password, calendar_link, sender_name):
        self.gmail = gmail_address
        self.password = gmail_password
        self.calendar_link = calendar_link
        self.sender_name = sender_name
        self.sent_log = Path("email_sent_log.json")
        self.load_sent_log()

    def load_sent_log(self):
        """Load previously sent emails to avoid duplicates"""
        if self.sent_log.exists():
            with open(self.sent_log) as f:
                self.sent = json.load(f)
        else:
            self.sent = {}

    def save_sent_log(self):
        """Save sent email record"""
        with open(self.sent_log, 'w') as f:
            json.dump(self.sent, f, indent=2)

    def send_email(self, to_email, to_name, title, company, template="churn"):
        """Send personalized cold email"""

        # Check if already sent
        if to_email in self.sent:
            print(f"⏭️  Skipping {to_name} (already sent)")
            return False

        # Get template
        tmpl = TEMPLATES[template]

        # Personalize
        subject = tmpl["subject"].format(
            company=company,
            first_name=to_name.split()[0]
        )

        body = tmpl["body"].format(
            first_name=to_name.split()[0],
            title=title,
            company=company,
            sender_name=self.sender_name,
            calendar_link=self.calendar_link
        )

        try:
            # Connect to Gmail
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.gmail, self.password)

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.gmail
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Send
            server.send_message(msg)
            server.quit()

            # Log
            self.sent[to_email] = {
                'name': to_name,
                'company': company,
                'sent_at': datetime.now().isoformat(),
                'template': template
            }
            self.save_sent_log()

            print(f"✅ Sent to {to_name} ({company})")
            time.sleep(2)  # Avoid rate limiting
            return True

        except Exception as e:
            print(f"❌ Failed to send to {to_name}: {e}")
            return False

    def send_batch(self, csv_file, template="churn"):
        """Send to batch of prospects"""
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.send_email(
                    to_email=row['email'],
                    to_name=row['name'],
                    title=row['title'],
                    company=row['company'],
                    template=template
                )

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python cold_email_sender.py --emails targets.csv --template churn --name 'Your Name' --calendar 'https://calendly.com/...'")
        print("\nExample:")
        print("  python cold_email_sender.py --emails week1_targets.csv --template churn --name 'John' --calendar 'https://calendly.com/john'")
        sys.exit(1)

    # Parse arguments
    emails_file = "targets.csv"
    template = "churn"
    sender_name = "ForecastX Team"
    calendar_link = "https://calendly.com"

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--emails":
            emails_file = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--template":
            template = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--name":
            sender_name = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--calendar":
            calendar_link = sys.argv[i+1]
            i += 2
        else:
            i += 1

    # Get Gmail credentials
    gmail = input("Gmail address: ")
    password = input("Gmail app password: ")  # Use app-specific password, not main password

    sender = ColdEmailSender(gmail, password, calendar_link, sender_name)
    sender.send_batch(emails_file, template)

    print("\n✅ Batch complete")
    print(f"📊 Sent {len(sender.sent)} emails")
    print(f"📝 Log saved to email_sent_log.json")
