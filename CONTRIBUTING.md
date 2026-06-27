# Contributing to KDP Discovery Engine Pro

First off, thank you for considering contributing! We welcome contributions from everyone — whether it's fixing a bug, suggesting a feature, improving documentation, or helping with code.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Submitting Code Changes](#submitting-code-changes)
- [Development Setup](#development-setup)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. **Fork the repository** — click "Fork" on GitHub
2. **Clone your fork**:

   ```bash
   git clone https://github.com/your-username/kdp-discovery-engine-pro.git
   cd kdp-discovery-engine-pro
   ```

3. **Set up the development environment** (see [Development Setup](#development-setup))
4. **Create a branch** for your changes:

   ```bash
   git checkout -b feature/your-feature-name
   ```

## How to Contribute

### Reporting Bugs

Before submitting a bug report:

- Check the [existing issues](https://github.com/your-org/kdp-discovery-engine-pro/issues) to see if it's already reported
- Ensure you're running the latest version

When filing a bug report, include:

- **Steps to reproduce** — a minimal, complete, and reproducible example
- **Expected behavior** — what you expected to happen
- **Actual behavior** — what actually happened (include error messages, stack traces)
- **Environment details** — OS, Python version, dependency versions (`pip freeze`)
- **Screenshots** — if applicable

> Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) when creating an issue.

### Suggesting Features

Feature suggestions are welcome! When proposing a feature:

- **Describe the problem** you're trying to solve
- **Explain the proposed solution** — how should it work?
- **Consider alternatives** — what else have you considered?
- **Provide context** — is this a common workflow for KDP authors?

> Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) when creating an issue.

### Submitting Code Changes

1. Ensure your code follows our [Style Guidelines](#style-guidelines)
2. Add or update tests as needed
3. Update documentation (README, docstrings) if your change affects the user interface or API
4. Run the test suite before submitting
5. Submit a pull request with a clear description of your changes

## Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/kdp-discovery-engine-pro.git
cd kdp-discovery-engine-pro

# 2. Create a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install development dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt  # or: pip install -r requirements.txt

# 4. Configure your API key
cp config.ini.example config.ini
# Edit config.ini with your SerpApi key

# 5. Verify the setup
streamlit run main.py
```

## Style Guidelines

### Python

- **PEP 8** — follow standard Python style conventions
- **Type hints** — always use type annotations for function signatures
- **Docstrings** — all public functions must have Google-style docstrings
- **Line length** — maximum 100 characters
- **Imports** — order: standard library → third-party → local; separate groups with blank lines

```python
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from core import scraper, analyzer
```

### Naming Conventions

- `snake_case` for functions, variables, and modules
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Single leading underscore for internal/private functions (`_helper`)

### Additive-Only Principle

This project follows an **additive-only** pattern in core modules. When adding features:

- **Append new functions** — never modify or remove existing public functions
- **Preserve signatures** — existing function signatures must remain unchanged
- **Add new columns** — preserve all existing columns in DataFrames

This ensures backward compatibility for all users and downstream tools.

## Testing

### Running Tests

```bash
# Compile check (all modules must compile)
python -m py_compile main.py
python -m py_compile src/dashboard.py
python -m py_compile src/core/analyzer.py
# (repeat for all .py files)

# Functional tests
python tests/test_features.py

# Manual verification
streamlit run main.py
```

### Test Requirements

- All new functions must have corresponding test coverage
- Tests should not require a SerpApi key (use mock data)
- The existing test suite must pass before a PR is merged

### CI Pipeline

Tests are run automatically on every PR via GitHub Actions. The CI checks:

1. All Python files compile
2. All functional tests pass
3. No new dependencies are introduced without justification

## Pull Request Process

1. **Ensure tests pass** — run the test suite locally
2. **Update documentation** — README, docstrings, and any relevant docs
3. **Squash commits** — keep the commit history clean
4. **Write a good PR description** — what changed and why
5. **Link related issues** — use "Closes #123" syntax
6. **Request review** — at least one maintainer must approve
7. **Merge** — after approval, a maintainer will merge your PR

### PR Title Format

```
<type>: <brief description>
```

Types:
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `style` — formatting, missing semicolons, etc.
- `refactor` — code change that neither fixes nor adds
- `test` — adding or updating tests
- `chore` — build process, dependencies, etc.

Examples:
```
feat: add historical BSR graph to niche tracker
fix: handle empty keyword list in extract_keywords_from_titles
docs: update API key setup instructions in README
```

## Project Structure

```
kdp-discovery-engine-pro/
├── main.py                 # Entry point
├── src/
│   ├── dashboard.py        # Streamlit UI
│   ├── cli.py              # CLI mode
│   └── core/               # Core logic (additive-only)
│       ├── analyzer.py     # Scoring algorithms
│       ├── scraper.py      # Amazon data collection
│       ├── database.py     # SQLite persistence
│       ├── exporter.py     # Google Sheets export
│       └── config_manager.py
├── assets/                 # Static resources
├── data/                   # Runtime data (gitignored)
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
├── build_spec.spec         # PyInstaller config
└── pyarmor_build.py        # Obfuscation script
```

## Questions?

If you have questions, feel free to:

- Open a [Discussion](https://github.com/your-org/kdp-discovery-engine-pro/discussions)
- Ask in the issue tracker

Thank you for contributing!
