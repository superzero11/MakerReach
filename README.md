# MakerReach

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A Python toolkit for scraping product launches and sending personalized outreach emails to makers. Currently supports Product Hunt, with more platforms coming soon.

## ✨ Features

- 🔍 **Scrape Product Hunt** - Automatically get today's launches
- 📧 **Extract Emails** - Find contact emails from product websites
- 👤 **Maker Info** - Capture maker names and profile links
- 🔗 **Social Links** - Extract Twitter, LinkedIn, GitHub profiles
- ✉️ **Send Emails** - Personalized outreach via Resend API
- 📊 **Track Status** - CSV tracking for sent/failed/skipped emails
- 🧪 **Test Mode** - Preview emails before sending to real recipients

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- [Resend](https://resend.com) account (for sending emails)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/makerreach.git
cd makerreach

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium
```

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:
   ```bash
   RESEND_API_KEY=re_your_api_key_here
   FROM_EMAIL=Your Name <your@domain.com>
   TEST_EMAIL=your-test@email.com
   ```

3. Create your email template:
   ```bash
   cp template.example.txt template.txt
   # Edit template.txt with your message
   ```

## 📖 Usage

### Master Script (Recommended)

The `run.py` script orchestrates the full workflow:

```bash
# Full workflow: scrape → show stats → confirm → send emails
python3 run.py

# Test mode: scrape 10 products, send 5 test emails
python3 run.py --scrape-limit 10 --email-limit 5 --test

# Scrape only (no emails)
python3 run.py --scrape-only

# Email only (use today's CSV)
python3 run.py --email-only --email-limit 20

# Skip confirmation prompt
python3 run.py --no-confirm --email-limit 10
```

### Individual Scripts

#### Scraper

```bash
# Scrape all of today's launches
python3 scraper.py

# Scrape first 10 products (for testing)
python3 scraper.py 10
```

#### Emailer

```bash
# Test mode - sends to your test email
python3 emailer.py data/launches-2024-01-15.csv 5 --test

# Production - send to actual recipients
python3 emailer.py data/launches-2024-01-15.csv 10
```

## 🎛️ Command Line Options

### run.py Options

| Flag | Description |
|------|-------------|
| `--scrape-limit N` | Limit products to scrape |
| `--scrape-only` | Only scrape, skip emailing |
| `--email-limit N` | Limit emails to send |
| `--email-only` | Only email, skip scraping |
| `--test` | Test mode (send to test email) |
| `--test-email EMAIL` | Custom test email address |
| `--no-confirm` | Skip confirmation prompt |
| `--date YYYY-MM-DD` | Use specific date's CSV |

## 📁 Project Structure

```
makerreach/
├── run.py              # Master orchestration script
├── scraper.py          # Product Hunt scraper
├── emailer.py          # Email sender (Resend API)
├── template.txt        # Your email template (git-ignored)
├── template.example.txt# Example template
├── requirements.txt    # Python dependencies
├── .env                # Your credentials (git-ignored)
├── .env.example        # Example environment file
├── data/               # CSV outputs (git-ignored)
│   └── launches-YYYY-MM-DD.csv
├── LICENSE
├── CONTRIBUTING.md
└── README.md
```

## 📝 Email Template

Edit `template.txt` with your personalized message. Available placeholders:

| Placeholder | Description |
|-------------|-------------|
| `{{FirstName}}` | Maker's first name |
| `{{ProductName}}` | Product name |
| `{{LaunchPlatform}}` | Platform name (e.g., "Product Hunt") |

## 📊 CSV Output Columns

| Column | Description |
|--------|-------------|
| `name` | Product name |
| `tagline` | Product tagline |
| `website` | Product website URL |
| `email` | Contact email |
| `maker_name` | Maker's full name |
| `maker_profile` | Product Hunt profile URL |
| `twitter` | Twitter/X profile |
| `linkedin` | LinkedIn profile |
| `github` | GitHub profile |
| `other_social` | Other social links |
| `ph_url` | Product Hunt URL |
| `email_sent` | Status: sent/failed/skipped |
| `email_sent_at` | Timestamp |

## 🔄 Typical Workflow

1. **Morning**: Scrape today's launches
   ```bash
   python3 run.py --scrape-only
   ```

2. **Review**: Check the CSV in `data/` folder

3. **Test**: Send test emails to yourself
   ```bash
   python3 run.py --email-only --email-limit 3 --test
   ```

4. **Send**: Send to actual recipients
   ```bash
   python3 run.py --email-only --email-limit 50
   ```

## ⚠️ Important Notes

- **Rate Limiting**: 5-second delay between emails to avoid rate limits
- **Browser Mode**: Scraper runs with visible browser to avoid detection
- **Crash Recovery**: CSV saves after each email to prevent duplicates
- **Email Filtering**: Invalid emails (noreply@, example.com) are auto-skipped

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) for browser automation
- [Resend](https://resend.com) for email API

---

**Disclaimer**: Use this tool responsibly. Respect rate limits and anti-spam laws. Always get proper consent before sending marketing emails.
