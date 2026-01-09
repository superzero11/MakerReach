#!/usr/bin/env python3
"""
Email Sender - Send personalized emails to Product Hunt launches
Uses Resend API to send emails based on CSV data and template
"""

import csv
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

try:
    import resend
except ImportError:
    print("❌ Please install resend: pip3 install resend")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("❌ Please install python-dotenv: pip3 install python-dotenv")
    sys.exit(1)

# Configuration from .env
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "")
TEST_EMAIL_DEFAULT = os.getenv("TEST_EMAIL", "")
TEMPLATE_FILE = "template.txt"

if not RESEND_API_KEY or not FROM_EMAIL:
    print("❌ Missing RESEND_API_KEY or FROM_EMAIL in .env file")
    print("   Copy .env.example to .env and fill in your credentials")
    sys.exit(1)


def validate_test_email(test_email: str) -> bool:
    """Validate that test email is configured when running in test mode"""
    if not test_email:
        print("❌ TEST_EMAIL not configured")
        print("   Set TEST_EMAIL in .env or use --test-email flag")
        return False
    return True


def load_template(template_path: str) -> str:
    """Load email template from file"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_first_name(maker_name: str) -> str:
    """Extract first name from maker name"""
    if not maker_name:
        return "there"  # Fallback if no name
    
    # Split by space and take first part
    parts = maker_name.strip().split()
    if parts:
        return parts[0]
    return "there"


def personalize_email(template: str, product: dict) -> tuple[str, str]:
    """
    Replace placeholders in template with actual values
    Returns (subject, body)
    """
    first_name = extract_first_name(product.get('maker_name', ''))
    product_name = product.get('name', 'your product')
    launch_platform = product.get('source', 'Product Hunt')
    
    # Map source to friendly name
    platform_names = {
        'producthunt': 'Product Hunt',
        'hackernews': 'Hacker News',
        'indiehackers': 'Indie Hackers'
    }
    launch_platform = platform_names.get(launch_platform.lower(), launch_platform)
    
    # Replace placeholders in body
    body = template.replace('{{FirstName}}', first_name)
    body = body.replace('{{ProductName}}', product_name)
    body = body.replace('{{LaunchPlatform}}', launch_platform)
    
    # Create subject
    subject = f"Congrats on launching {product_name}!"
    
    return subject, body


def send_email(to_email: str, subject: str, body: str, test_mode: bool = False, test_email: str = None) -> tuple[bool, str]:
    """
    Send email using Resend API
    Returns (success, message)
    """
    resend.api_key = RESEND_API_KEY
    
    # In test mode, send to test email instead
    actual_recipient = test_email if test_mode else to_email
    
    try:
        params = {
            "from": FROM_EMAIL,
            "to": [actual_recipient],
            "subject": subject,
            "text": body,
        }
        
        response = resend.Emails.send(params)
        
        if response and response.get('id'):
            return True, f"Sent (ID: {response['id']})"
        else:
            return False, f"Failed: {response}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"


def process_csv(csv_path: str, limit: int = None, test_mode: bool = False, test_email: str = None):
    """
    Process CSV file and send emails
    
    Args:
        csv_path: Path to CSV file
        limit: Maximum number of emails to send
        test_mode: If True, send all emails to test_email instead
        test_email: Email address for testing
    """
    # Validate test email in test mode
    actual_test_email = test_email or TEST_EMAIL_DEFAULT
    if test_mode and not validate_test_email(actual_test_email):
        sys.exit(1)
    
    # Load template from script directory
    script_dir = Path(__file__).parent
    template_path = script_dir / TEMPLATE_FILE
    
    if not template_path.exists():
        print(f"❌ Template file not found: {template_path}")
        sys.exit(1)
    
    template = load_template(str(template_path))
    print(f"✅ Loaded template from {template_path}")
    
    # Read CSV
    rows = []
    fieldnames = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    
    print(f"📊 Found {len(rows)} products in CSV")
    
    # Add email_sent and email_sent_at columns if not present
    if 'email_sent' not in fieldnames:
        fieldnames.append('email_sent')
    if 'email_sent_at' not in fieldnames:
        fieldnames.append('email_sent_at')
    
    # Filter products with valid emails that haven't been sent yet
    to_send = []
    for i, row in enumerate(rows):
        email = row.get('email', '').strip()
        email_sent = row.get('email_sent', '').strip().lower()
        
        # Skip if no email or already sent
        if not email:
            continue
        if email_sent == 'sent':
            continue
        
        # Skip placeholder/invalid emails
        invalid_patterns = ['example.com', 'your@', 'you@', 'noreply@', 'no-reply@', 
                          'test@', 'demo@', '.webp', 'footer.email']
        if any(p in email.lower() for p in invalid_patterns):
            rows[i]['email_sent'] = 'skipped'
            rows[i]['email_sent_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            continue
            
        to_send.append((i, row))
    
    print(f"📧 Found {len(to_send)} products with valid emails to send")
    
    if limit and limit < len(to_send):
        print(f"⚠️  Limiting to first {limit} emails")
        to_send = to_send[:limit]
    
    if test_mode:
        print(f"🧪 TEST MODE: All emails will be sent to {actual_test_email}")
    
    # Send emails
    sent_count = 0
    failed_count = 0
    
    for idx, (row_index, product) in enumerate(to_send):
        email = product.get('email', '')
        name = product.get('name', 'Unknown')
        maker = product.get('maker_name', 'Unknown')
        
        print(f"\n[{idx + 1}/{len(to_send)}] {name}")
        print(f"    Maker: {maker}")
        print(f"    Email: {email}" + (f" → {actual_test_email}" if test_mode else ""))
        
        # Personalize email
        subject, body = personalize_email(template, product)
        
        # Send email
        success, message = send_email(email, subject, body, test_mode, actual_test_email)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if success:
            print(f"    ✅ {message}")
            rows[row_index]['email_sent'] = 'sent'
            rows[row_index]['email_sent_at'] = timestamp
            sent_count += 1
        else:
            print(f"    ❌ {message}")
            rows[row_index]['email_sent'] = 'failed'
            rows[row_index]['email_sent_at'] = timestamp
            failed_count += 1
        
        # Save CSV after each email to prevent duplicates if interrupted
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                for field in fieldnames:
                    if field not in row:
                        row[field] = ''
                writer.writerow(row)
        
        # Add delay between emails (except for the last one)
        if idx < len(to_send) - 1:
            print(f"    ⏳ Waiting 5 seconds...")
            time.sleep(5)
    
    print(f"\n{'=' * 50}")
    print(f"✅ Done!")
    print(f"   📤 Sent: {sent_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📝 CSV updated: {csv_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Send personalized emails to Product Hunt launches',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode - send 2 emails to your test email
  python3 emailer.py launches-2026-01-08.csv 2 --test

  # Production - send 5 emails to actual recipients
  python3 emailer.py launches-2026-01-08.csv 5
  
  # Send all emails (no limit)
  python3 emailer.py launches-2026-01-08.csv
        """
    )
    
    parser.add_argument('csv_file', help='Path to CSV file with product launches')
    parser.add_argument('limit', nargs='?', type=int, default=None,
                        help='Maximum number of emails to send (optional)')
    parser.add_argument('--test', action='store_true',
                        help='Test mode - send all emails to test email instead')
    parser.add_argument('--test-email', default=TEST_EMAIL_DEFAULT,
                        help=f'Email address for test mode (default: {TEST_EMAIL_DEFAULT})')
    
    args = parser.parse_args()
    
    # Validate CSV file exists
    if not Path(args.csv_file).exists():
        print(f"❌ CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    print("\n📧 Product Launch Emailer")
    print("=" * 50)
    
    process_csv(
        csv_path=args.csv_file,
        limit=args.limit,
        test_mode=args.test,
        test_email=args.test_email
    )


if __name__ == "__main__":
    main()
