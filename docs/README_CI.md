# CI/CD Pipeline Documentation

## Overview
This document describes the CI/CD pipeline for the Inventory Management System (IMS) project. The pipeline is implemented using GitHub Actions and consists of 5 sequential stages that ensure code quality, security, and functionality.

---

## Pipeline Stages

### **STAGE 1: Build**
**Purpose:**
- Set up Python 3.10 environment for the project
- Install all production dependencies from `requirements.txt`
- Install development dependencies from `requirements-dev.txt`
- Verify project structure and display folder tree for debugging

**Local Execution:**
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify installation
pip list

# Display project structure
tree /F  # Windows
# or
ls -R    # Linux/Mac
```

---

### **STAGE 2: Test (ALL TEST CASES)**
**Purpose:**
- Execute ALL unit, integration, and system tests automatically
- Verify that test discovery and execution work correctly
- Generate test results for validation
- Upload test artifacts for review

**Local Execution:**
```bash
# Run all tests (unit + integration + system)
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/system/ -v

# Run with detailed output
pytest tests/ -v --tb=short
```

---

### **STAGE 3: Coverage (APPLY TO ALL CODE)**
**Purpose:**
- Measure code coverage across ALL source modules in `src/`
- Generate HTML coverage report for detailed analysis
- Enforce minimum coverage threshold of 75%
- Upload coverage reports as artifacts

**Local Execution:**
```bash
# Run coverage on all source code
pytest --cov=src --cov-report=html --cov-report=term tests/

# View coverage report
# Open htmlcov/index.html in browser

# Check coverage with minimum threshold
pytest --cov=src --cov-report=term --cov-fail-under=75 tests/

# Generate XML report for CI tools
pytest --cov=src --cov-report=xml tests/
```

---

### **STAGE 4: Lint (APPLY TO ALL MODULES)**
**Purpose:**
- Run pylint on ALL Python modules in `src/` directory
- Enforce code quality standards and PEP 8 compliance
- Require minimum pylint score of 7.5/10
- Generate detailed lint report

**Local Execution:**
```bash
# Lint all source code
pylint src/

# Lint with custom config
pylint --rcfile=.pylintrc src/

# Generate detailed report
pylint src/ --output-format=text > reports/pylint_report.txt

# Check specific modules
pylint src/cli.py src/product_manager.py

# Display score only
pylint src/ --score=y
```

---

### **STAGE 5: Security Scan (APPLY TO ALL CODE)**
**Purpose:**
- Run Bandit security scanner recursively on ALL `src/` code
- Detect common security vulnerabilities and coding errors
- Fail pipeline on high-severity issues
- Upload security scan report

**Local Execution:**
```bash
# Run security scan on all code
bandit -r src/

# Generate detailed report
bandit -r src/ -f txt -o reports/bandit_report.txt

# Generate JSON report
bandit -r src/ -f json -o reports/bandit_report.json

# Scan with severity filtering
bandit -r src/ -ll  # Only show low severity and above

# Verbose output
bandit -r src/ -v
```

---

## Package and Deploy

**Purpose:**
- Package the application for deployment (placeholder script)

**Local Execution:**
```bash
# On Linux/Mac
bash scripts/package_deploy.sh

# On Windows (Git Bash or WSL)
bash scripts/package_deploy.sh
```

---

## Pipeline Workflow

The pipeline stages execute **sequentially** with dependencies:

```
Build → Test → Coverage → Lint → Security Scan
```

Each stage:
- **Depends** on successful completion of the previous stage
- **Uploads** artifacts (test results, coverage reports, lint reports, security reports)
- **Fails** the pipeline if quality thresholds are not met

---

## Triggers

The pipeline runs automatically on:
- **Push** to any branch
- **Pull Request** to `main` branch

---

## Artifacts

Each pipeline run generates and uploads:
- Test results (Stage 2)
- HTML coverage report (Stage 3)
- Pylint report (Stage 4)
- Bandit security report (Stage 5)

Artifacts are available for download from the GitHub Actions interface for 90 days.

---

## Quality Gates

| Stage | Metric | Threshold |
|-------|--------|-----------|
| Test | Test Pass Rate | 100% |
| Coverage | Code Coverage | ≥ 75% |
| Lint | Pylint Score | ≥ 7.5/10 |
| Security | High Severity Issues | 0 |

---

## Notes

- All stages use **Ubuntu-latest** runner
- Python version: **3.10**
- Pipeline does NOT support parallel execution - stages run sequentially
- Placeholder tests ensure pipeline works even before implementation
- ALL code and ALL tests are scanned automatically using recursive patterns

---

## Future Enhancements

- Add deployment stage for production releases
- Integrate code review automation
- Add performance testing stage
- Implement automated dependency updates
- Add notification integrations (Slack, email)
