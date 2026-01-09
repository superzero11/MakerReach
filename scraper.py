#!/usr/bin/env python3
"""
ProductHunt Scraper - Finds today's launches, their websites, and emails
"""

import csv
import re
from datetime import datetime
from dataclasses import dataclass, asdict, field
from playwright.sync_api import sync_playwright, Page, Browser


@dataclass
class Product:
    name: str
    tagline: str
    ph_url: str
    website: str
    email: str
    maker_name: str = ""
    maker_profile: str = ""
    twitter: str = ""
    linkedin: str = ""
    github: str = ""
    other_social: str = ""
    source: str = "producthunt"
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))


def extract_emails_from_page(page: Page) -> list[str]:
    """Extract email addresses from page content"""
    emails = set()
    
    try:
        # Get page content
        content = page.content()
        
        # Find emails using regex
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        found = re.findall(email_pattern, content)
        
        for email in found:
            email = email.lower()
            # Filter out common non-contact emails
            if not any(x in email for x in ['example.com', 'sentry.io', 'wixpress', 
                       'cloudflare', 'googleapis', 'schema.org', 'w3.org', 
                       'webpack', 'github', '.png', '.jpg', '.svg']):
                emails.add(email)
        
        # Also check for mailto: links
        mailto_links = page.query_selector_all('a[href^="mailto:"]')
        for link in mailto_links:
            href = link.get_attribute('href') or ''
            if href.startswith('mailto:'):
                email = href.replace('mailto:', '').split('?')[0].lower()
                emails.add(email)
                
    except Exception:
        pass
    
    return list(emails)


def get_product_website(page: Page, ph_product_url: str) -> str:
    """Visit ProductHunt product page and find the actual website"""
    try:
        page.goto(ph_product_url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        
        # Look for "Visit website" link - it has the actual URL
        visit_links = page.query_selector_all('a')
        for link in visit_links:
            text = (link.inner_text() or '').strip().lower()
            if 'visit website' in text:
                href = link.get_attribute('href')
                if href and 'producthunt.com' not in href:
                    # Clean the URL - remove ref parameter
                    clean_url = href.split('?')[0]
                    return clean_url
                    
    except Exception as e:
        print(f"    ⚠️  Error getting website: {e}")
    
    return ""


def get_maker_info(page: Page, ph_product_url: str) -> dict:
    """Extract maker info from the first comment on product page
    
    Returns dict with maker_name, maker_profile, twitter, linkedin, github, other_social
    """
    result = {
        'maker_name': '',
        'maker_profile': '',
        'twitter': '',
        'linkedin': '',
        'github': '',
        'other_social': ''
    }
    
    try:
        # Make sure we're on the product page
        if page.url != ph_product_url:
            page.goto(ph_product_url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
        
        # Find the first comment with "Maker" badge
        # The maker badge appears near the commenter's name
        maker_elements = page.query_selector_all('text=Maker')
        
        if maker_elements:
            # Find the parent container and look for the maker's profile link
            for maker_badge in maker_elements:
                try:
                    # Navigate up to find the comment container
                    parent = maker_badge.evaluate_handle('el => el.closest("div")')
                    if not parent:
                        continue
                    
                    # Look for the maker's profile link nearby
                    # The structure is usually: name link followed by Maker badge
                    profile_links = page.query_selector_all('a[href^="/@"], a[href^="https://www.producthunt.com/@"]')
                    
                    for link in profile_links:
                        href = link.get_attribute('href') or ''
                        if '/@' in href:
                            # Get maker name
                            name = link.inner_text().strip()
                            if name and len(name) > 1 and not name.startswith('Image'):
                                result['maker_name'] = name
                                # Get full profile URL
                                if href.startswith('/'):
                                    result['maker_profile'] = f"https://www.producthunt.com{href}"
                                else:
                                    result['maker_profile'] = href
                                break
                    
                    if result['maker_profile']:
                        break
                except Exception:
                    continue
        
        # If we found a maker profile, visit it to get social links
        if result['maker_profile']:
            print(f"    → Found maker: {result['maker_name']}")
            print(f"    → Visiting maker profile...")
            
            social_links = get_maker_social_links(page, result['maker_profile'])
            result.update(social_links)
            
    except Exception as e:
        print(f"    ⚠️  Error getting maker info: {e}")
    
    return result


def get_maker_social_links(page: Page, maker_profile_url: str) -> dict:
    """Visit maker profile page and extract social links"""
    result = {
        'twitter': '',
        'linkedin': '',
        'github': '',
        'other_social': ''
    }
    
    try:
        page.goto(maker_profile_url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        
        # Find all links on the page
        all_links = page.query_selector_all('a[href]')
        other_socials = []
        
        for link in all_links:
            href = (link.get_attribute('href') or '').lower()
            
            # Twitter/X
            if ('twitter.com/' in href or 'x.com/' in href) and not result['twitter']:
                if '/ProductHunt' not in href and '/producthunt' not in href:
                    result['twitter'] = link.get_attribute('href')
            
            # LinkedIn
            elif 'linkedin.com/in/' in href and not result['linkedin']:
                result['linkedin'] = link.get_attribute('href')
            
            # GitHub
            elif 'github.com/' in href and not result['github']:
                # Exclude common non-personal github links
                if not any(x in href for x in ['/issues', '/pull', '/blob', '/tree']):
                    result['github'] = link.get_attribute('href')
            
            # Other social links (Instagram, YouTube, personal website, etc.)
            elif any(social in href for social in ['instagram.com/', 'youtube.com/', 'facebook.com/', 
                     'tiktok.com/', 'medium.com/@', 'dev.to/', 'threads.net/']):
                other_socials.append(link.get_attribute('href'))
        
        # Join other social links
        if other_socials:
            result['other_social'] = ' | '.join(other_socials[:3])  # Limit to 3
            
        # Log what we found
        found = [k for k, v in result.items() if v]
        if found:
            print(f"    → Social links: {', '.join(found)}")
        else:
            print(f"    → No social links found")
            
    except Exception as e:
        print(f"    ⚠️  Error getting social links: {e}")
    
    return result


def get_email_from_website(page: Page, website_url: str) -> str:
    """Visit website and find email address"""
    if not website_url:
        return ""
    
    emails = []
    
    try:
        # Visit main page
        page.goto(website_url, timeout=20000)
        page.wait_for_timeout(2000)
        emails.extend(extract_emails_from_page(page))
        
        # If no emails found, try common pages
        if not emails:
            base_url = website_url.rstrip('/')
            for path in ['/contact', '/about', '/support']:
                try:
                    page.goto(f"{base_url}{path}", timeout=10000)
                    page.wait_for_timeout(1000)
                    emails.extend(extract_emails_from_page(page))
                    if emails:
                        break
                except Exception:
                    continue
                    
    except Exception as e:
        print(f"    ⚠️  Error visiting website: {e}")
    
    # Return first valid email or empty
    return emails[0] if emails else ""


def scrape_producthunt(limit: int = None) -> list[Product]:
    """Scrape today's products from ProductHunt homepage
    
    Args:
        limit: Optional limit on number of products to process (for testing)
    """
    products = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        # Step 1: Load ProductHunt homepage
        print("  📡 Loading ProductHunt homepage...")
        page.goto("https://www.producthunt.com", timeout=60000)
        page.wait_for_timeout(5000)
        
        # Step 2: Click "See all of today's products" to load all today's products
        print("  🔘 Clicking 'See all of today's products'...")
        try:
            btn = page.query_selector('button:has-text("See all of today")')
            if btn:
                btn.click()
                # Wait for products to load (takes ~4 seconds)
                page.wait_for_timeout(5000)
                print("  ✅ Loaded all today's products")
            else:
                print("  ⚠️  'See all' button not found")
        except Exception as e:
            print(f"  ⚠️  Could not click 'See all': {e}")
        
        # Step 3: Get only today's products from the today section
        today_section = page.query_selector('[data-test="homepage-section-today"]')
        
        if today_section:
            posts = today_section.query_selector_all('[data-test^="post-item-"]')
        else:
            posts = page.query_selector_all('[data-test^="post-item-"]')
        
        print(f"  ℹ️  Found {len(posts)} products launching today")
        
        # Collect product info first (deduplicate by post_id)
        product_data = []
        seen_ids = set()
        
        for post in posts:
            try:
                test_id = post.get_attribute("data-test")
                post_id = test_id.replace("post-item-", "")
                
                if post_id in seen_ids:
                    continue
                seen_ids.add(post_id)
                
                # Get product name
                name_el = page.query_selector(f'[data-test="post-name-{post_id}"]')
                name = name_el.inner_text().strip() if name_el else ""
                
                if not name:
                    continue
                
                # Clean up numbered names like "333. ProductName"
                if '. ' in name[:6] and name.split('. ')[0].isdigit():
                    name = name.split('. ', 1)[1]
                
                # Get ProductHunt product page link
                link = post.query_selector("a[href*='/products/']")
                href = link.get_attribute("href") if link else ""
                ph_url = f"https://www.producthunt.com{href}" if href and href.startswith("/") else href
                
                # Get tagline
                tagline = ""
                texts = post.query_selector_all("p, span")
                for t in texts:
                    txt = t.inner_text().strip()
                    if txt and not txt.isdigit() and len(txt) > 10 and txt != name and not txt.startswith(name):
                        tagline = txt
                        break
                
                product_data.append({
                    'name': name,
                    'tagline': tagline,
                    'ph_url': ph_url
                })
                
            except Exception:
                continue
        
        print(f"\n  🔍 Processing {len(product_data)} unique products...")
        
        # Apply limit if specified
        if limit and limit < len(product_data):
            print(f"  ⚠️  Limiting to first {limit} products")
            product_data = product_data[:limit]
        
        # Step 4: Visit each product page to get website, then get email
        for i, data in enumerate(product_data):
            print(f"\n  [{i+1}/{len(product_data)}] {data['name']}")
            
            # Get actual website from PH product page
            print(f"    → Getting website...")
            website = get_product_website(page, data['ph_url'])
            print(f"    → Website: {website or 'Not found'}")
            
            # Get maker info (name, profile, social links)
            print(f"    → Getting maker info...")
            maker_info = get_maker_info(page, data['ph_url'])
            
            # Get email from website
            email = ""
            if website:
                print(f"    → Finding email...")
                email = get_email_from_website(page, website)
                print(f"    → Email: {email or 'Not found'}")
            
            products.append(Product(
                name=data['name'],
                tagline=data['tagline'],
                ph_url=data['ph_url'],
                website=website,
                email=email,
                maker_name=maker_info['maker_name'],
                maker_profile=maker_info['maker_profile'],
                twitter=maker_info['twitter'],
                linkedin=maker_info['linkedin'],
                github=maker_info['github'],
                other_social=maker_info['other_social']
            ))
        
        browser.close()
    
    return products


def save_to_csv(products: list[Product], filename: str = None):
    """Save products to CSV file in data directory"""
    from pathlib import Path
    
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    if not filename:
        filename = f"launches-{datetime.now().strftime('%Y-%m-%d')}.csv"
    
    filepath = data_dir / filename
    
    if not products:
        print("  ⚠️  No products to save")
        return
    
    fieldnames = ["date", "source", "name", "tagline", "website", "email", "maker_name", 
                  "maker_profile", "twitter", "linkedin", "github", "other_social", "ph_url"]
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for product in products:
            row = asdict(product)
            writer.writerow({k: row[k] for k in fieldnames})
    
    print(f"  ✅ Saved {len(products)} products to {filepath}")


def main():
    import sys
    
    # Optional limit from command line: python scraper.py 10
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    print("\n🚀 ProductHunt Scraper")
    print("=" * 50)
    if limit:
        print(f"⚠️  Limiting to first {limit} products")
    
    print("\n📥 Scraping ProductHunt...")
    try:
        products = scrape_producthunt(limit=limit)
        print(f"\n  ✅ Found {len(products)} products")
        
        # Count stats
        with_email = sum(1 for p in products if p.email)
        with_maker = sum(1 for p in products if p.maker_name)
        with_twitter = sum(1 for p in products if p.twitter)
        with_linkedin = sum(1 for p in products if p.linkedin)
        
        print(f"  📧 {with_email} products have email addresses")
        print(f"  👤 {with_maker} products have maker info")
        print(f"  🐦 {with_twitter} makers have Twitter/X")
        print(f"  💼 {with_linkedin} makers have LinkedIn")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        products = []
    
    # Save results
    print("\n💾 Saving results...")
    save_to_csv(products)
    
    print("\n" + "=" * 50)
    print(f"✅ Done! Total: {len(products)} products")


if __name__ == "__main__":
    main()
