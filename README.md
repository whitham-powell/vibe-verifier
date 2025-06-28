# Vibe Verifier

A comprehensive, language-agnostic tool for analyzing, verifying, and testing codebases. Vibe Verifier performs complexity analysis, formal verification, and automated testing to validate the claims and capabilities of any given repository.

## Core Philosophy: Trust But Verify

Vibe Verifier operates on the principle that **documentation is only a starting point**. The tool:
- **Never trusts documentation blindly** - all claims must be verified through code analysis
- **Treats documentation as hypotheses** to be tested against actual implementation
- **Assumes nothing works** until proven by tests and analysis
- **Only generates findings** based on verifiable evidence from the codebase itself

This approach ensures that you get an accurate picture of what a codebase actually does, not just what it claims to do.

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Understanding Your Report](#understanding-your-report)
- [Command Line Options](#command-line-options)
- [Supported Languages](#supported-languages)
- [Output Formats](#output-formats)
- [Troubleshooting](#troubleshooting)

## Quick Start

```bash
# Install from PyPI
pip install vibe-verifier

# Analyze your repository
vibe-verifier /path/to/your/repo

# View the generated reports in ./reports/
```

## Installation

### Requirements

- Python 3.8 or higher
- pip package manager

### Install from PyPI

```bash
pip install vibe-verifier
```

### Install from Source

```bash
git clone https://github.com/vibes/vibe-verifier.git
cd vibe-verifier
pip install -e .
```

### Optional Dependencies

Some language-specific analysis tools need to be installed separately:

```bash
# For enhanced Python analysis
pip install crosshair-tool hypothesis

# For JavaScript/TypeScript projects
npm install -g eslint typescript

# For Go projects
go install github.com/securego/gosec/v2/cmd/gosec@latest
go install honnef.co/go/tools/cmd/staticcheck@latest

# For Java projects
# Install Maven or Gradle based on your project
```

## Basic Usage

### Analyze a Repository

Simply point Vibe Verifier at your repository:

```bash
vibe-verifier /path/to/your/repo
```

This will:
1. Detect programming languages used
2. Extract claims from documentation
3. Analyze code complexity
4. Run static analysis and security checks
5. Execute existing tests
6. Verify documentation claims against implementation
7. Generate comprehensive reports

### Quick Analysis

For a faster, less thorough analysis:

```bash
vibe-verifier /path/to/your/repo --quick
```

### Specific Output Format

Generate only the report format you need:

```bash
# Generate only HTML report
vibe-verifier /path/to/your/repo --output-format html

# Generate only JSON for automation
vibe-verifier /path/to/your/repo --output-format json
```

## Understanding Your Report

After analysis, you'll find reports in the `./reports/` directory:

### Report Files

- **`report_[repo]_[timestamp].html`** - Interactive HTML report (recommended for viewing)
- **`report_[repo]_[timestamp].md`** - Markdown report for documentation
- **`report_[repo]_[timestamp].json`** - Machine-readable results for automation
- **`report_[repo]_[timestamp].pdf`** - Executive summary PDF
- **`verification_steps_[repo]_[timestamp].md`** - Manual verification guide

### Key Metrics

#### Health Score (0-100)
- **90-100**: Excellent - Well-maintained, tested, and documented code
- **70-89**: Good - Minor issues that should be addressed
- **50-69**: Fair - Several issues requiring attention
- **Below 50**: Poor - Significant problems need immediate attention

#### Complexity Ratings
- **A (1-5)**: Simple, easy to understand
- **B (6-10)**: Moderate complexity
- **C (11-20)**: Complex, consider refactoring
- **D (21-30)**: Very complex, refactoring recommended
- **E (31-40)**: Extremely complex, refactoring required
- **F (41+)**: Unmaintainable, must be refactored

#### Issue Severity
- **Critical**: Immediate action required (security vulnerabilities, broken tests)
- **High**: Should be fixed soon (failing documentation claims, high complexity)
- **Medium**: Plan to address (type errors, missing tests)
- **Low**: Nice to fix (style issues, minor warnings)

### Reading the HTML Report

The HTML report provides:
1. **Executive Summary** with overall health score
2. **Language Breakdown** showing technologies used
3. **Critical Issues** requiring immediate attention
4. **Test Results** with pass/fail rates
5. **Security Findings** from vulnerability scans
6. **Recommendations** prioritized by importance

### Using the Verification Steps

The `verification_steps_*.md` file provides commands to manually verify our findings:

```bash
# Example: Verify complexity analysis
radon cc -s /path/to/your/repo --total-average

# Example: Run security checks
bandit -r /path/to/your/repo
```

**Important**: These verification steps allow you to independently confirm our analysis. We encourage you to run these commands yourself, as Vibe Verifier's philosophy is to never trust claims without verification - including our own findings!

## Command Line Options

```bash
vibe-verifier [OPTIONS] REPO_PATH
```

### Options

- `--output-format {all,markdown,html,json,pdf}` - Choose report format(s) (default: all)
- `--skip-tests` - Skip test execution phase
- `--skip-verification` - Skip formal verification phase
- `--quick` - Quick analysis (skip time-consuming checks)
- `--output-dir PATH` - Directory for reports (default: ./reports)
- `--config FILE` - Configuration file path
- `--verbose, -v` - Enable verbose output
- `--help, -h` - Show help message

### Examples

```bash
# Analyze with specific output directory
vibe-verifier /my/project --output-dir /tmp/analysis

# Skip tests for faster analysis
vibe-verifier /my/project --skip-tests

# Use configuration file
vibe-verifier /my/project --config my-config.json

# Verbose output for debugging
vibe-verifier /my/project -v
```

## Supported Languages

Vibe Verifier automatically detects and analyzes:

- **Python** - Complexity, type checking (mypy), security (bandit), tests (pytest, unittest)
- **JavaScript/TypeScript** - Linting (ESLint), type checking (tsc), tests (Jest, Mocha)
- **Java** - Build analysis (Maven/Gradle), tests (JUnit, TestNG)
- **Go** - Security (gosec), static analysis (staticcheck), tests (go test)
- **C/C++** - Static analysis (cppcheck), formal verification (CBMC)
- **Rust** - Verification (Prusti, Kani), tests (cargo test)
- **Ruby** - Tests (RSpec, Minitest)
- **PHP** - Tests (PHPUnit)
- And more...

## Output Formats

### HTML Report
Best for human consumption. Interactive with:
- Collapsible sections
- Color-coded severity levels
- Searchable content
- Links to specific issues

### Markdown Report
Ideal for:
- Including in project documentation
- Sharing via GitHub/GitLab
- Converting to other formats

### JSON Report
Perfect for:
- CI/CD integration
- Custom automation
- Feeding into other tools
- Tracking metrics over time

### PDF Report
Suitable for:
- Executive summaries
- Formal documentation
- Offline viewing

## Configuration

Create a `vibe-verifier.json` file:

```json
{
  "output_format": "all",
  "output_dir": "./verification-reports",
  "skip_tests": false,
  "skip_verification": false,
  "quick_mode": false,
  "save_raw_results": true,
  "complexity_threshold": 20,
  "min_test_coverage": 80
}
```

## Troubleshooting

### "No tests found"
- Ensure your test files follow common naming conventions (test_*.py, *.test.js, etc.)
- Check that test frameworks are installed in your project

### "Language not detected"
- Verify file extensions are standard (.py, .js, .java, etc.)
- Ensure source files aren't in excluded directories (node_modules, venv, etc.)

### "Analysis takes too long"
- Use `--quick` mode for faster analysis
- Use `--skip-tests` if test execution is slow
- Analyze specific subdirectories instead of entire monorepos

### "Permission denied errors"
- Ensure you have read access to all files in the repository
- Check for symbolic links pointing to restricted directories

### "Tool not found" warnings
- Install optional language-specific tools for deeper analysis
- These warnings don't prevent basic analysis from completing

## Exit Codes

- `0` - Success: All checks passed
- `1` - Test failures detected
- `2` - Documentation claims failed verification
- `3` - Analysis error occurred

## Privacy & Security

Vibe Verifier:
- Runs entirely locally - no code is sent to external services
- Does not modify your code
- Only reads files necessary for analysis
- Saves reports only to your specified directory

## Getting Help

- **Issues**: https://github.com/vibes/vibe-verifier/issues
- **Documentation**: https://github.com/vibes/vibe-verifier/wiki
- **Examples**: See the `examples/` directory in the repository

## License

MIT License - see LICENSE file for details