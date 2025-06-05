# Contributing Guidelines

## Welcome Contributors!

Thank you for your interest in contributing to the Freshdesk Spam Filter project! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Documentation](#documentation)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background, experience level, or identity.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing private information without permission
- Any conduct that would be inappropriate in a professional setting

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. **Python 3.8+** installed
2. **Git** for version control
3. **OpenAI API Key** (for running tests that interact with the AI)
4. **Code editor** with Python support (VS Code recommended)

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/freshdesk-spam-filter.git
   cd freshdesk-spam-filter
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/freshdesk-spam-filter.git
   ```

## Development Setup

### Environment Setup

```bash
# Create virtual environment
python -m venv dev-env
source dev-env/bin/activate  # On Windows: dev-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black mypy flake8 pytest-cov

# Copy environment template
cp .env.example .env.dev
```

### Configuration for Development

Edit `.env.dev` with test credentials:

```env
# Use test/development Freshdesk instance
FRESHDESK_DOMAIN=test-company.freshdesk.com
FRESHDESK_API_KEY=test_api_key_here

# OpenAI Configuration (for development/testing)
OPENAI_API_KEY=your_openai_api_key_for_dev_tests 
OPENAI_MODEL_NAME=gpt-3.5-turbo # Or a specific model you are testing against

# Development settings
SPAM_THRESHOLD=0.6
CHECK_INTERVAL_MINUTES=1
LOG_LEVEL=DEBUG
```

### Verify Setup

```bash
# Link development config
ln -sf .env.dev .env

# Test setup
python test_setup.py

# Run tests
python -m pytest tests/ -v
```

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line Length:** 88 characters (Black formatter default)
- **Indentation:** 4 spaces
- **Quotes:** Double quotes for strings
- **Imports:** Organized using isort

### Code Formatting

Use **Black** for automatic code formatting:

```bash
# Format all Python files
black .

# Check formatting without changes
black --check .
```

### Type Hints

All functions must include type hints:

```python
from typing import List, Dict, Optional

def process_tickets(limit: Optional[int] = None) -> Dict[str, int]:
    """Process tickets with optional limit."""
    pass

def get_tickets(status: str) -> List[Dict]:
    """Get tickets with specified status."""
    pass
```

### Docstrings

Use **Google-style docstrings** for all classes and functions:

```python
def analyze_spam(subject: str, description: str, sender_email: str = "") -> Tuple[bool, float, str]:
    """Analyze ticket content for spam using AI.
    
    Args:
        subject: Ticket subject line
        description: Ticket description/content
        sender_email: Sender's email address (optional)
        
    Returns:
        Tuple containing:
        - is_spam: Whether content is classified as spam
        - confidence: Confidence score (0.0-1.0)
        - reasoning: AI's explanation for the decision
        
    Raises:
        Exception: On AI processing errors
        
    Example:
        >>> from openai_client import OpenAIClient # Assuming client is configured
        >>> client = OpenAIClient()
        >>> is_spam, confidence, reasoning = client.analyze_spam(
        ...     subject="Help with login",
        ...     description="I can't access my account"
        ... )
    """
    pass
```

### Error Handling

Implement proper exception handling:

```python
import logging

logger = logging.getLogger(__name__)

def risky_operation():
    """Example of proper error handling."""
    try:
        # Risky code here
        result = some_api_call()
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### Logging Standards

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

# Good logging examples
logger.info(f"Processing ticket #{ticket_id}")
logger.warning(f"High confidence spam detected: {confidence:.2f}")
logger.error(f"Failed to process ticket {ticket_id}: {error}")
logger.debug(f"API response: {response.json()}")
```

## Testing Requirements

### Test Categories

1. **Unit Tests:** Test individual functions and methods
2. **Integration Tests:** Test component interactions
3. **End-to-End Tests:** Test complete workflows
4. **Mock Tests:** Test without external dependencies
   - **Mock External APIs:** Use mocks for Freshdesk and OpenAI API calls where appropriate to isolate units under test and avoid excessive real API calls during unit/integration testing.

### Writing Tests

Create tests in the `tests/` directory:

```python
import pytest
from unittest.mock import Mock, patch
from spam_filter import SpamFilter

class TestSpamFilter:
    """Test cases for SpamFilter class."""
    
    def test_analyze_spam_detection(self):
        """Test spam detection functionality."""
        # Arrange
        spam_filter = SpamFilter()
        
        # Act
        result = spam_filter.analyze_first_customer_message({
            'ticket_id': 123,
            'subject': 'SPAM: Buy our product!',
            'description': 'Click here to buy now!',
            'sender_email': 'spam@example.com'
        })
        
        # Assert
        assert result['is_spam'] is True
        assert result['confidence'] > 0.7
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_spam_filter.py

# Run with verbose output
python -m pytest -v

# Run integration tests
python test_ai_spam_detection.py
python test_edge_cases.py
```

### Test Requirements

- **Coverage:** Aim for >80% code coverage
- **Mock External APIs:** Use mocks for Freshdesk and OpenAI
- **Test Edge Cases:** Include error conditions and edge cases
- **Performance Tests:** Test with realistic data volumes

## Pull Request Process

### Before Submitting

1. **Update from upstream:**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** following coding standards

4. **Run tests:**
   ```bash
   python -m pytest
   black --check .
   mypy .
   flake8 .
   ```

5. **Update documentation** if needed

### Pull Request Template

When creating a pull request, include:

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Integration tests pass

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

### Review Process

1. **Automated Checks:** CI/CD pipeline runs tests and linting
2. **Code Review:** Maintainers review code quality and design
3. **Testing:** Reviewers may test functionality
4. **Approval:** At least one maintainer approval required
5. **Merge:** Maintainer merges after approval

## Issue Reporting

### Bug Reports

If you find a bug, please include:

- **Description:** Clear and concise summary of the bug
- **Steps to Reproduce:** Detailed steps to reproduce the behavior
- **Expected Behavior:** What you expected to happen
- **Actual Behavior:** What actually happened
- **Error Messages/Logs:** Full error messages and relevant log snippets
- **Environment:**
    - Python Version: [e.g., 3.9.5]
    - Operating System: [e.g., macOS, Windows, Linux]
    - OpenAI Model Name (if relevant): [e.g., gpt-3.5-turbo]
    - Key Configuration (from .env, excluding secrets): [e.g., SPAM_THRESHOLD, PROCESS_NEW_TICKETS_ONLY]
- **Screenshots/Videos:** (Optional) If helpful for demonstrating the issue

### Feature Requests

Use the feature request template:

```markdown
**Feature Description**
Clear description of the proposed feature.

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
Other approaches you've considered.

**Additional Context**
Any other relevant information.
```

### Security Issues

For security vulnerabilities:

1. **Do NOT** create public issues
2. **Email maintainers** directly
3. **Include:** Description, impact, reproduction steps
4. **Wait** for response before public disclosure

## Documentation

### Documentation Standards

- **Clear and Concise:** Easy to understand
- **Examples:** Include code examples
- **Up-to-Date:** Keep documentation current
- **Comprehensive:** Cover all features

### Documentation Types

1. **API Documentation:** Function and class documentation
2. **User Guides:** How-to guides for users
3. **Developer Guides:** Setup and contribution guides
4. **Architecture Docs:** System design documentation

### Updating Documentation

When making changes:

1. **Update relevant documentation files**
2. **Update docstrings** for modified functions
3. **Add examples** for new features
4. **Update API reference** if needed

## Development Workflow

### Branching Strategy

- **main:** Stable, production-ready code
- **develop:** Integration branch for features
- **feature/\*:** Feature development branches
- **bugfix/\*:** Bug fix branches
- **hotfix/\*:** Critical production fixes

### Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(spam-filter): add confidence threshold configuration
fix(api): handle missing ticket description field
docs(readme): update installation instructions
```

### Release Process

1. **Version Bump:** Update version numbers
2. **Changelog:** Update CHANGELOG.md
3. **Testing:** Run full test suite
4. **Tag:** Create git tag for release
5. **Documentation:** Update release documentation

## Getting Help

### Communication Channels

- **GitHub Issues:** Bug reports and feature requests
- **GitHub Discussions:** General questions and discussions
- **Email:** Direct contact for sensitive issues

### Resources

- **Documentation:** Read all documentation files
- **Code Examples:** Check existing code for patterns
- **Tests:** Look at test files for usage examples
- **Issues:** Search existing issues for similar problems

## Recognition

Contributors will be recognized in:

- **CHANGELOG.md:** Major contributions noted
- **README.md:** Contributors section
- **Release Notes:** Significant contributions highlighted

Thank you for contributing to the Freshdesk Spam Filter project!
