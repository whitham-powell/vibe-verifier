# Developer Guide for Vibe Verifier

This guide is for developers and testers working on the Vibe Verifier project itself.

## Core Philosophy and Design Principles

### Trust But Verify

Vibe Verifier is built on a fundamental principle: **documentation is only a starting point, never the truth**. When developing features for this tool, always remember:

1. **Assume Nothing Works** - The tool must verify every claim through actual code analysis
2. **Documentation is Untrusted** - Treat all documentation (README, comments, docstrings) as hypotheses to be tested
3. **Evidence-Based Analysis** - Only report findings that can be verified through:
   - Static code analysis
   - Test execution results
   - Formal verification proofs
   - Security scanning outputs
4. **No Assumptions** - Never assume a feature works because documentation says so
5. **Verification Over Trust** - Always provide methods for users to independently verify our findings

### Implementation Guidelines

When adding new analyzers or features:
- Extract claims from documentation but mark them as "unverified"
- Implement verification methods for each type of claim
- Generate verification steps that users can run independently
- Report discrepancies between claims and implementation
- Never skip verification even if documentation seems authoritative

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Running Tests](#running-tests)
- [Adding New Features](#adding-new-features)
- [Contributing Guidelines](#contributing-guidelines)
- [Debugging Tips](#debugging-tips)
- [Performance Considerations](#performance-considerations)

## Development Setup

### Prerequisites

- Python 3.8+
- Git

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/vibes/vibe-verifier.git
cd vibe-verifier
```

2. Create a virtual environment and install:
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

That's it! The tool is now installed with all dependencies.

### Verify Setup

```bash
# Check Python version (should be 3.8+)
python --version

# Check vibe-verifier is installed
vibe-verifier --version

# Run tests
pytest
```

## Project Structure

```
vibe-verifier/
├── src/                      # Main source code
│   ├── __init__.py
│   ├── main.py              # CLI entry point and orchestrator
│   ├── analyzers/           # Analysis modules
│   │   ├── complexity.py    # Code complexity analysis
│   │   └── documentation_analyzer.py  # Documentation claim extraction
│   ├── verifiers/           # Verification modules
│   │   ├── static_analyzer.py  # Static analysis and linting
│   │   └── formal_verifier.py  # Formal verification integration
│   ├── testers/             # Test discovery and execution
│   │   └── test_runner.py   # Universal test runner
│   ├── reporters/           # Report generation
│   │   └── report_generator.py  # Multi-format report generation
│   └── utils/               # Utility functions
├── tests/                   # Test suite
│   ├── conftest.py         # Pytest fixtures and configuration
│   ├── test_*.py           # Unit tests for each module
│   └── test_integration.py # Integration tests
├── docs/                    # Documentation
├── examples/                # Example configurations and projects
├── requirements.txt         # Production dependencies
├── setup.py                # Package configuration
├── pyproject.toml          # Modern Python project configuration
├── Makefile                # Development automation
└── .github/workflows/      # CI/CD configuration
```

## Architecture Overview

### Design Philosophy in Practice

The architecture reflects our "trust but verify" philosophy:

1. **Documentation Analyzer** - Extracts claims but marks ALL as unverified
2. **Claim Verifier** - Attempts to verify each claim through code analysis
3. **Report Generator** - Clearly distinguishes verified facts from unverified claims
4. **Verification Steps** - Provides commands for manual verification of ALL findings

### Core Components

1. **VibeVerifier (main.py)**
   - Orchestrates the entire analysis pipeline
   - Manages configuration and phases
   - Handles error reporting and exit codes

2. **Analyzers**
   - `ComplexityAnalyzer`: Calculates cyclomatic complexity, LOC, maintainability
   - `LanguageDetector`: Identifies programming languages
   - `DocumentationAnalyzer`: Extracts claims from docs and docstrings
   - `ClaimVerifier`: Verifies extracted claims against implementation

3. **Verifiers**
   - `StaticAnalyzer`: Integrates linters, type checkers, security scanners
   - `FormalVerifier`: Integrates formal verification tools (Prusti, CBMC, etc.)

4. **Test Runner**
   - `UniversalTestRunner`: Discovers and executes tests across frameworks
   - Supports 15+ test frameworks across multiple languages

5. **Report Generator**
   - `ReportGenerator`: Creates reports in MD, HTML, JSON, PDF
   - `SummaryReporter`: Generates console summaries

### Analysis Pipeline

```
1. Language Detection
   ↓
2. Documentation Analysis → Extract Claims
   ↓
3. Complexity Analysis → Calculate Metrics
   ↓
4. Static Analysis → Lint, Type Check, Security
   ↓
5. Formal Verification → Run Verification Tools
   ↓
6. Test Execution → Discover & Run Tests
   ↓
7. Claim Verification → Verify Documentation
   ↓
8. Report Generation → Create Output Files
```

## Running Tests

### Quick Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run only unit tests
pytest -k "not integration"

# Run only integration tests
pytest tests/test_integration.py

# Run specific test file
pytest tests/test_complexity_analyzer.py -v

# Run specific test
pytest tests/test_complexity_analyzer.py::TestComplexityAnalyzer::test_analyze_python_project -v
```

### Test Categories

1. **Unit Tests** (`test_*.py`)
   - Test individual components in isolation
   - Mock external dependencies
   - Fast execution

2. **Integration Tests** (`test_integration.py`)
   - Test complete workflows
   - Test CLI interface
   - May be slower

### Writing Tests

When writing tests, remember our core philosophy - verify everything:

```python
def test_documentation_claims_are_not_trusted(self):
    """Test that documentation claims are marked as unverified until proven."""
    analyzer = DocumentationAnalyzer("/path/to/repo")
    results = analyzer.analyze()

    # All claims should start as unverified
    for claim in results["claims"]:
        assert claim["verified"] is False
        assert claim["verification_method"] is not None
```

Example test structure:

```python
import pytest
from unittest.mock import patch, MagicMock

class TestNewFeature:
    """Test new feature functionality."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for tests."""
        return {"key": "value"}

    def test_basic_functionality(self, sample_data):
        """Test basic feature behavior."""
        # Arrange
        feature = NewFeature()

        # Act
        result = feature.process(sample_data)

        # Assert
        assert result["status"] == "success"

    @patch('subprocess.run')
    def test_external_tool_integration(self, mock_run):
        """Test integration with external tools."""
        mock_run.return_value = MagicMock(
            stdout='{"result": "ok"}',
            returncode=0
        )

        feature = NewFeature()
        result = feature.run_external_tool()

        assert result["result"] == "ok"
        mock_run.assert_called_once()
```

### Test Fixtures

Key fixtures in `conftest.py`:

- `temp_dir`: Temporary directory for test files
- `sample_python_project`: Complete Python project with tests
- `sample_javascript_project`: JavaScript project with package.json
- `sample_multi_language_project`: Multi-language project
- `mock_subprocess_run`: Mocks external tool calls

## Adding New Features

### Adding a New Language

1. Update `LanguageDetector` in `complexity.py`:
```python
LANGUAGE_EXTENSIONS = {
    # Add new language
    ".ext": "NewLanguage",
}
```

2. Add test framework support in `test_runner.py`:
```python
TEST_FRAMEWORKS = {
    "newlang": {
        "framework_name": {
            "indicators": ["config.file", "test_*.ext"],
            "command": ["test-runner", "command"],
            "config_files": ["config.file"]
        }
    }
}
```

3. Add verification tools in `formal_verifier.py`:
```python
def _check_newlang_verification(self) -> Dict[str, bool]:
    return {
        "tool1": shutil.which("tool1") is not None,
        "files": any(self.repo_path.rglob("*.ext"))
    }
```

4. Add tests for the new language support

### Adding a New Analysis Type

1. Create analyzer in `src/analyzers/`:
```python
class NewAnalyzer:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.results = {}

    def analyze(self) -> Dict[str, Any]:
        # Implement analysis logic
        return self.results
```

2. Integrate into main pipeline (`main.py`):
```python
# In VibeVerifier.run_analysis()
new_analyzer = NewAnalyzer(str(self.repo_path))
new_results = new_analyzer.analyze()
self.results["new_analysis"] = new_results
```

3. Update report generation to include new results

4. Add comprehensive tests

### Adding a New Report Format

1. Add template in `report_generator.py`:
```python
def _get_templates(self) -> Dict[str, str]:
    return {
        # Existing templates...
        "new_format": """Template content here..."""
    }
```

2. Add generation method:
```python
def _generate_new_format_report(self, report_data: Dict[str, Any]) -> Path:
    template = self.jinja_env.get_template("new_format")
    content = template.render(**report_data)

    filename = f"report_{report_data['metadata']['repository']}_new.ext"
    filepath = self.results_dir / filename

    with open(filepath, 'w') as f:
        f.write(content)

    return filepath
```

3. Update `generate_report()` to call new method

## Contributing Guidelines

### Code Style

1. Follow PEP 8:
```bash
# Format code
black src/ tests/
isort src/ tests/

# Check linting
pylint src/
flake8 src/
mypy src/
```

2. Type hints are required:
```python
def process_data(data: List[Dict[str, Any]],
                config: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Process data with optional configuration."""
    pass
```

3. Docstrings for all public functions:
```python
def analyze(self) -> Dict[str, Any]:
    """Analyze repository and return results.

    Returns:
        Dict containing analysis results with keys:
        - 'summary': Overall summary statistics
        - 'details': Detailed findings

    Raises:
        AnalysisError: If analysis fails
    """
```

### Commit Messages

Follow conventional commits:
- `feat: Add support for Ruby language`
- `fix: Handle empty test results gracefully`
- `docs: Update developer documentation`
- `test: Add tests for security analyzer`
- `refactor: Simplify complexity calculation`

### Pull Request Process

1. Create feature branch: `git checkout -b feature/your-feature`
2. Write tests for new functionality
3. Ensure all tests pass: `make test`
4. Update documentation if needed
5. Create PR with clear description
6. Address review feedback

## Debugging Tips

### Enable Verbose Logging

```python
# In your code
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use in functions
logger.debug(f"Processing file: {file_path}")
logger.info(f"Found {len(issues)} issues")
logger.error(f"Failed to analyze: {error}")
```

### Debug Specific Components

```python
# Test individual analyzer
from src.analyzers.complexity import ComplexityAnalyzer

analyzer = ComplexityAnalyzer("/path/to/test/repo")
result = analyzer.analyze()
print(json.dumps(result, indent=2))
```

### Common Issues

1. **External tool not found**
   - Check `shutil.which("tool")` returns path
   - Verify tool is in PATH
   - Mock in tests if optional

2. **Test failures on CI**
   - Check OS-specific paths
   - Verify external tool mocking
   - Check file encoding issues

3. **Slow test execution**
   - Use `pytest -x` to stop on first failure
   - Run specific tests during development
   - Mock time-consuming operations

### Performance Profiling

```python
import cProfile
import pstats

# Profile specific function
profiler = cProfile.Profile()
profiler.enable()

# Run analysis
verifier = VibeVerifier("/large/repo")
verifier.run_analysis()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

## Performance Considerations

### Optimization Strategies

1. **Parallel Processing**
   - Use `concurrent.futures` for independent analyses
   - Process files in batches
   - Cache repeated calculations

2. **Memory Management**
   - Stream large files instead of loading entirely
   - Clear results after writing reports
   - Use generators for file iteration

3. **Skip Unnecessary Work**
   - Check file timestamps for caching
   - Skip excluded directories early
   - Use quick mode for large repos

### Example Optimization

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def analyze_files_parallel(self, files: List[Path]) -> Dict[str, Any]:
    results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_file = {
            executor.submit(self._analyze_single_file, f): f
            for f in files
        }

        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                results[str(file_path)] = result
            except Exception as e:
                results[str(file_path)] = {"error": str(e)}

    return results
```

## Advanced Testing

### Testing External Tool Integration

```python
@patch('subprocess.run')
def test_tool_integration(mock_run):
    # Setup mock response
    mock_run.return_value = MagicMock(
        stdout=json.dumps({"status": "ok"}),
        stderr="",
        returncode=0
    )

    # Test the integration
    analyzer = ToolAnalyzer()
    result = analyzer.run_analysis()

    # Verify correct command was called
    mock_run.assert_called_with(
        ["tool", "--json", "--input", ANY],
        capture_output=True,
        text=True
    )
```

### Property-Based Testing

```python
from hypothesis import given, strategies as st

@given(
    complexity=st.integers(min_value=1, max_value=100),
    loc=st.integers(min_value=0, max_value=10000)
)
def test_health_score_bounds(complexity, loc):
    """Test health score is always between 0 and 100."""
    score = calculate_health_score(complexity, loc)
    assert 0 <= score <= 100
```

## Common Commands

```bash
# Install for development
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/

# Type check
mypy src/

# Run linting
pylint src/
flake8 src/

# Build package
python -m build

# Clean up
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release PR
4. After merge, tag release: `git tag v1.2.3`
5. Push tag: `git push origin v1.2.3`
6. Build and publish: `python -m build && twine upload dist/*`

## Getting Help

- **Development Chat**: [Discord/Slack channel]
- **Architecture Decisions**: See `docs/architecture/`
- **API Documentation**: Generated with `make docs`
- **Core Team**: @maintainer1, @maintainer2

Remember:
- When in doubt, write a test!
- When analyzing, verify everything!
- Documentation is a hypothesis, not a fact!
