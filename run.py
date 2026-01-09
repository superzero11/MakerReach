#!/usr/bin/env python3
"""
Master Script - Orchestrates scraping and emailing workflow
Runs scraper, shows stats, then sends emails with user confirmation
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional for scrape-only mode

# Import from local modules
from scraper import scrape_producthunt, save_to_csv
from emailer import process_csv

# Get test email from environment
TEST_EMAIL_DEFAULT = os.getenv("TEST_EMAIL", "")


def get_csv_path(date: str = None) -> Path:
    """Get the CSV file path for a given date"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    data_dir = Path(__file__).parent / "data"
    return data_dir / f"launches-{date}.csv"


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def run_scraper(limit: int = None) -> tuple[Path, dict]:
    """
    Run the scraper and return CSV path and stats
    
    Returns:
        (csv_path, stats_dict)
    """
    print_section("🔍 STEP 1: SCRAPING PRODUCT HUNT")
    
    if limit:
        print(f"\n⚠️  Limiting to first {limit} products")
    
    print("\n📥 Scraping ProductHunt...")
    
    try:
        products = scrape_producthunt(limit=limit)
        
        # Calculate stats
        stats = {
            'total': len(products),
            'with_email': sum(1 for p in products if p.email),
            'with_maker': sum(1 for p in products if p.maker_name),
            'with_twitter': sum(1 for p in products if p.twitter),
            'with_linkedin': sum(1 for p in products if p.linkedin),
        }
        
        # Save to CSV
        print("\n💾 Saving results...")
        save_to_csv(products)
        
        csv_path = get_csv_path()
        
        return csv_path, stats
        
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")
        sys.exit(1)


def print_scraper_stats(stats: dict):
    """Print scraper statistics"""
    print_section("📊 SCRAPING COMPLETE - STATS")
    
    print(f"""
    📦 Total Products:     {stats['total']}
    📧 With Email:         {stats['with_email']} ({stats['with_email']*100//max(stats['total'],1)}%)
    👤 With Maker Info:    {stats['with_maker']} ({stats['with_maker']*100//max(stats['total'],1)}%)
    🐦 With Twitter/X:     {stats['with_twitter']}
    💼 With LinkedIn:      {stats['with_linkedin']}
    """)


def run_emailer(csv_path: Path, limit: int = None, test_mode: bool = False, test_email: str = None) -> dict:
    """
    Run the emailer and return stats
    
    Returns:
        stats_dict with sent, failed counts
    """
    print_section("📧 STEP 2: SENDING EMAILS")
    
    if test_mode:
        print(f"\n🧪 TEST MODE: All emails will be sent to {test_email}")
    
    if limit:
        print(f"⚠️  Limiting to {limit} emails")
    
    # Run emailer
    process_csv(
        csv_path=str(csv_path),
        limit=limit,
        test_mode=test_mode,
        test_email=test_email
    )


def print_final_summary(scraper_stats: dict, csv_path: Path):
    """Print final summary"""
    print_section("✅ WORKFLOW COMPLETE - SUMMARY")
    
    print(f"""
    📅 Date:               {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    📁 CSV File:           {csv_path}
    
    SCRAPING:
    ─────────
    📦 Products Scraped:   {scraper_stats['total']}
    📧 With Email:         {scraper_stats['with_email']}
    
    Check the CSV file for detailed email send status.
    """)


def main():
    parser = argparse.ArgumentParser(
        description='Master script to scrape Product Hunt and send outreach emails',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full run: scrape all products, send all emails (with confirmation)
  python3 run.py

  # Scrape 50 products, send 20 emails in test mode
  python3 run.py --scrape-limit 50 --email-limit 20 --test

  # Scrape only (no emails)
  python3 run.py --scrape-only

  # Email only (use existing CSV from today)
  python3 run.py --email-only --email-limit 10

  # Use specific date's CSV for emailing
  python3 run.py --email-only --date 2026-01-08
        """
    )
    
    # Scraper options
    scraper_group = parser.add_argument_group('Scraper Options')
    scraper_group.add_argument('--scrape-limit', type=int, default=None,
                               help='Limit number of products to scrape')
    scraper_group.add_argument('--scrape-only', action='store_true',
                               help='Only run scraper, skip emailing')
    
    # Emailer options
    emailer_group = parser.add_argument_group('Emailer Options')
    emailer_group.add_argument('--email-limit', type=int, default=None,
                               help='Limit number of emails to send')
    emailer_group.add_argument('--email-only', action='store_true',
                               help='Only run emailer, skip scraping')
    emailer_group.add_argument('--test', action='store_true',
                               help='Test mode - send emails to test address')
    emailer_group.add_argument('--test-email', default=None,
                               help='Test email address (uses TEST_EMAIL from .env if not specified)')
    emailer_group.add_argument('--no-confirm', action='store_true',
                               help='Skip confirmation before sending emails')
    
    # General options
    parser.add_argument('--date', type=str, default=None,
                        help='Use CSV from specific date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("  🚀 PRODUCT HUNT SCRAPER & EMAILER")
    print("=" * 60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    scraper_stats = None
    csv_path = None
    
    # Step 1: Scraping
    if not args.email_only:
        csv_path, scraper_stats = run_scraper(limit=args.scrape_limit)
        print_scraper_stats(scraper_stats)
    else:
        # Use existing CSV
        csv_path = get_csv_path(args.date)
        if not csv_path.exists():
            print(f"\n❌ CSV file not found: {csv_path}")
            sys.exit(1)
        print(f"\n📁 Using existing CSV: {csv_path}")
        scraper_stats = {'total': 0, 'with_email': 0, 'with_maker': 0, 'with_twitter': 0, 'with_linkedin': 0}
    
    # Step 2: Emailing
    if not args.scrape_only:
        # Resolve test email
        test_email = args.test_email or TEST_EMAIL_DEFAULT
        
        # Validate test email in test mode
        if args.test and not test_email:
            print("\n❌ TEST_EMAIL not configured")
            print("   Set TEST_EMAIL in .env or use --test-email flag")
            sys.exit(1)
        
        # Ask for confirmation unless --no-confirm
        if not args.no_confirm:
            print_section("📧 READY TO SEND EMAILS")
            
            mode_str = "TEST MODE" if args.test else "PRODUCTION"
            limit_str = f"up to {args.email_limit}" if args.email_limit else "all available"
            
            print(f"""
    Mode:        {mode_str}
    CSV:         {csv_path}
    Emails:      {limit_str}
    Delay:       5 seconds between emails
            """)
            
            if args.test:
                print(f"    Test Email:  {test_email}")
            
            try:
                response = input("\n    Proceed with sending emails? [y/N]: ").strip().lower()
                if response != 'y':
                    print("\n    ⏹️  Email sending cancelled.")
                    print_final_summary(scraper_stats, csv_path)
                    return
            except KeyboardInterrupt:
                print("\n\n    ⏹️  Cancelled by user.")
                return
        
        run_emailer(
            csv_path=csv_path,
            limit=args.email_limit,
            test_mode=args.test,
            test_email=test_email
        )
    
    # Final summary
    print_final_summary(scraper_stats, csv_path)


if __name__ == "__main__":
    main()
