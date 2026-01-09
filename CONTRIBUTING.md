# Contributing to MakerReach

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](../../issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the bug
   - Expected vs actual behavior
   - Your environment (OS, Python version)

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Explain why it would be valuable

### Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test your changes thoroughly
5. Commit with clear messages: `git commit -m "Add: feature description"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/makerreach.git
cd makerreach

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
python -m playwright install chromium

# Set up environment
cp .env.example .env
# Edit .env with your credentials
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions
- Keep functions focused and small
- Add comments for complex logic

## Testing

Before submitting a PR:

1. Test scraping with a small limit: `python3 scraper.py 5`
2. Test emailing in test mode: `python3 run.py --email-only --email-limit 2 --test`
3. Ensure no sensitive data is committed

## Commit Messages

Use clear, descriptive commit messages:

- `Add: description` - New feature
- `Fix: description` - Bug fix
- `Update: description` - Update existing feature
- `Docs: description` - Documentation changes
- `Refactor: description` - Code refactoring

## Pull Request Process

1. Update README.md if needed
2. Update requirements.txt if you add dependencies
3. Ensure no sensitive data is included
4. Request review from maintainers

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Questions?

Feel free to open an issue for any questions about contributing.
