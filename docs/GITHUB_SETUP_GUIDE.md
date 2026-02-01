# GitHub Repository Setup Guide

A comprehensive guide to setting up a professional Python project with GitHub best practices. This can be reused for any project.

## Quick Setup Commands

After creating a new repository, run these commands to configure everything:

```bash
# Clone and enter the repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Enable features via GitHub API
gh api repos/YOUR_USERNAME/YOUR_REPO -X PATCH \
  -f has_discussions=true \
  -f delete_branch_on_merge=true \
  -f allow_auto_merge=true \
  -f allow_squash_merge=true \
  -f allow_merge_commit=false \
  -f allow_rebase_merge=false \
  -f squash_merge_commit_title=PR_TITLE \
  -f squash_merge_commit_message=PR_BODY

# Add repository topics
echo '{"names":["python","your-topic-1","your-topic-2"]}' | \
  gh api repos/YOUR_USERNAME/YOUR_REPO/topics -X PUT --input -

# Set up branch protection (adjust check names to match your CI)
cat > /tmp/branch-protection.json << 'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Lint", "Type Check", "Test"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
gh api repos/YOUR_USERNAME/YOUR_REPO/branches/main/protection \
  -X PUT --input /tmp/branch-protection.json
```

---

## File Structure

Here's the complete file structure for GitHub configuration:

```
your-project/
├── .github/
│   ├── CODEOWNERS
│   ├── FUNDING.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── dependabot.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── config.yml
│   └── workflows/
│       ├── ci.yml
│       ├── codeql.yml
│       ├── release.yml
│       └── stale.yml
├── .pre-commit-config.yaml
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── SECURITY.md
└── pyproject.toml
```

---

## 1. Community Standards Files

### SECURITY.md

```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by emailing the maintainers directly rather than opening a public issue.

**Please include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (if available)

We will acknowledge receipt within 48 hours and provide a timeline for a fix.
```

### CODE_OF_CONDUCT.md

```markdown
# Code of Conduct

## Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

## Our Standards

Examples of behavior that contributes to a positive environment:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

Examples of unacceptable behavior:
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org/), version 2.1.
```

### CONTRIBUTING.md

```markdown
# Contributing

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
   cd YOUR_REPO
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Quality

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Or run individual tools
ruff check .        # Linting
ruff format .       # Formatting
pyright             # Type checking
```

## Running Tests

```bash
pytest tests/ -v
```

## Making Changes

1. Create a branch for your changes
2. Make your changes
3. Ensure all checks pass: `pre-commit run --all-files`
4. Run tests: `pytest tests/ -v`
5. Submit a pull request
```

---

## 2. Issue Templates

### .github/ISSUE_TEMPLATE/bug_report.md

```markdown
---
name: Bug report
about: Report a bug to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear description of what the bug is.

## To Reproduce
Steps to reproduce:
1. ...
2. ...

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- Package version: 
- Python version: 
- OS: 

## Code Example
```python
# Minimal code to reproduce the issue
```

## Error Output
```
# Paste any error messages or tracebacks
```

## Additional Context
Any other context about the problem.
```

### .github/ISSUE_TEMPLATE/feature_request.md

```markdown
---
name: Feature request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Problem
Describe the problem or limitation you're facing.

## Proposed Solution
Describe what you'd like to happen.

## Alternatives Considered
Describe any alternative solutions you've considered.

## Use Case
Explain how this feature would benefit users.

## Additional Context
Any other context, examples, or screenshots.
```

### .github/ISSUE_TEMPLATE/config.yml

```yaml
blank_issues_enabled: false
contact_links:
  - name: Documentation
    url: https://github.com/YOUR_USERNAME/YOUR_REPO#readme
    about: Check the documentation before opening an issue
  - name: Discussions
    url: https://github.com/YOUR_USERNAME/YOUR_REPO/discussions
    about: Ask questions and discuss ideas
```

---

## 3. Pull Request Template

### .github/PULL_REQUEST_TEMPLATE.md

```markdown
## Description

Brief description of the changes.

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Checklist

- [ ] I have run `pre-commit run --all-files` and all checks pass
- [ ] I have added tests that prove my fix/feature works
- [ ] I have updated the documentation if needed
- [ ] My changes generate no new warnings

## Testing

Describe the tests you added or ran.

## Related Issues

Fixes #(issue number)
```

---

## 4. GitHub Workflows

### .github/workflows/ci.yml

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run ruff linter
        run: uv run ruff check .

      - name: Run ruff formatter check
        run: uv run ruff format --check .

  type-check:
    name: Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run pyright
        run: uv run pyright src/

  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run tests
        run: uv run pytest tests/ -v --tb=short
```

### .github/workflows/codeql.yml

```yaml
name: CodeQL

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 0 * * 0"  # Weekly on Sundays

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [python]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: security-extended,security-and-quality

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
```

### .github/workflows/release.yml

```yaml
name: Release

on:
  push:
    tags:
      - "v[0-9]*"

jobs:
  build:
    name: Build Package
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Extract version from tag
        id: get_version
        run: echo "VERSION=${GITHUB_REF_NAME#v}" >> $GITHUB_OUTPUT

      - name: Update version in pyproject.toml
        run: |
          sed -i 's/^version = ".*"/version = "${{ steps.get_version.outputs.VERSION }}"/' pyproject.toml

      - name: Install build dependencies
        run: uv sync --dev

      - name: Build package
        run: uv build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  test:
    name: Test Build
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Download build artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install package from wheel
        run: pip install dist/*.whl

      - name: Verify installation
        run: python -c "import YOUR_PACKAGE; print('Import successful')"

  publish-pypi:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    needs: [build, test]
    environment:
      name: pypi
      url: https://pypi.org/project/YOUR_PACKAGE/
    permissions:
      id-token: write
    steps:
      - name: Download build artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1

  github-release:
    name: Create GitHub Release
    runs-on: ubuntu-latest
    needs: [publish-pypi]
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - name: Download build artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
          draft: false
          prerelease: ${{ contains(github.ref, 'alpha') || contains(github.ref, 'beta') || contains(github.ref, 'rc') }}
```

### .github/workflows/stale.yml

```yaml
name: Stale Issues and PRs

on:
  schedule:
    - cron: "0 0 * * *"  # Daily at midnight UTC
  workflow_dispatch:

permissions:
  issues: write
  pull-requests: write

jobs:
  stale:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v9
        with:
          stale-issue-message: >
            This issue has been automatically marked as stale because it has not had
            recent activity. It will be closed if no further activity occurs within 7 days.
          stale-pr-message: >
            This pull request has been automatically marked as stale because it has not had
            recent activity. It will be closed if no further activity occurs within 7 days.
          days-before-stale: 30
          days-before-close: 7
          stale-issue-label: "stale"
          stale-pr-label: "stale"
          exempt-issue-labels: "pinned,security,bug"
          exempt-pr-labels: "pinned,security"
```

---

## 5. Dependabot

### .github/dependabot.yml

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "python"
    commit-message:
      prefix: "chore(deps)"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "github-actions"
    commit-message:
      prefix: "chore(deps)"
```

---

## 6. Other GitHub Files

### .github/CODEOWNERS

```
# Default owners for everything in the repo
* @YOUR_USERNAME

# Source code
/src/ @YOUR_USERNAME

# CI/CD configuration
/.github/ @YOUR_USERNAME
```

### .github/FUNDING.yml

```yaml
github: YOUR_USERNAME
```

---

## 7. Pre-commit Configuration

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: pyright
        name: pyright
        entry: pyright
        language: system
        types: [python]
        pass_filenames: false
```

Install and run:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## 8. pyproject.toml Dev Dependencies

Add to your `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "ruff>=0.8",
    "pyright>=1.1",
    "pre-commit>=3.0",
]
```

---

## Summary Checklist

### Files to Create
- [ ] `SECURITY.md`
- [ ] `CODE_OF_CONDUCT.md`
- [ ] `CONTRIBUTING.md`
- [ ] `.github/ISSUE_TEMPLATE/bug_report.md`
- [ ] `.github/ISSUE_TEMPLATE/feature_request.md`
- [ ] `.github/ISSUE_TEMPLATE/config.yml`
- [ ] `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] `.github/CODEOWNERS`
- [ ] `.github/FUNDING.yml`
- [ ] `.github/dependabot.yml`
- [ ] `.github/workflows/ci.yml`
- [ ] `.github/workflows/codeql.yml`
- [ ] `.github/workflows/release.yml`
- [ ] `.github/workflows/stale.yml`
- [ ] `.pre-commit-config.yaml`

### Repository Settings (via gh CLI)
- [ ] Enable Discussions
- [ ] Enable auto-merge
- [ ] Enable delete branch on merge
- [ ] Set up branch protection
- [ ] Add repository topics
- [ ] (Already enabled by default) Dependabot security updates
- [ ] (Already enabled by default) Secret scanning

### PyPI Publishing Setup
1. Go to https://pypi.org/manage/account/publishing/
2. Add a "Trusted Publisher" for your GitHub repo
3. Set org/user, repo name, workflow: `release.yml`, environment: `pypi`

---

## 9. GitHub Advanced Security

GitHub Advanced Security features (free for public repositories):

### Already Enabled by Default
- **Secret scanning** — Detects accidentally committed secrets (API keys, tokens)
- **Secret scanning push protection** — Blocks pushes containing secrets
- **Dependabot security updates** — Auto-creates PRs for vulnerable dependencies
- **Dependabot alerts** — Notifies about vulnerable dependencies

### Workflows to Add

#### CodeQL (Security Scanning)
Already covered in `.github/workflows/codeql.yml` above. Scans for:
- SQL injection
- Cross-site scripting (XSS)
- Path traversal
- Insecure deserialization
- And more...

#### Dependency Review (for PRs)

`.github/workflows/dependency-review.yml`:
```yaml
name: Dependency Review

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

jobs:
  dependency-review:
    name: Dependency Review
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
          deny-licenses: GPL-3.0, AGPL-3.0
          comment-summary-in-pr: always
```

This blocks PRs that introduce:
- High/critical severity vulnerabilities
- Dependencies with incompatible licenses (GPL, AGPL)

### Manual Settings (via GitHub Web UI)

Go to **Settings → Code security and analysis**:

1. **Secret scanning**
   - ✅ Enable secret scanning
   - ✅ Enable push protection
   - ⬜ Enable validity checks (verifies if detected secrets are still active)
   - ⬜ Scan for non-provider patterns (custom regex patterns)

2. **Code scanning**
   - Should show "CodeQL" as configured via workflow

3. **Dependabot**
   - ✅ Dependabot alerts
   - ✅ Dependabot security updates
   - Configure via `.github/dependabot.yml`

### Security Policy

Ensure `SECURITY.md` exists (covered above) so users know how to report vulnerabilities.

### Private Vulnerability Reporting

Enable in **Settings → Code security and analysis → Private vulnerability reporting**

This allows security researchers to privately report vulnerabilities to you.

### Security Advisories

When you need to disclose a vulnerability:
1. Go to **Security → Advisories → New draft advisory**
2. Fill in CVE details
3. Request a CVE ID
4. Publish when ready

### Custom Secret Patterns

For organization-specific secrets, create custom patterns:
1. Go to **Settings → Code security and analysis → Secret scanning**
2. Add custom patterns (regex) for your organization's secret formats
