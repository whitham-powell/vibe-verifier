"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
import json


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def sample_python_project(temp_dir):
    """Create a sample Python project for testing."""
    project_dir = temp_dir / "python_project"
    project_dir.mkdir()
    
    # Create main module
    main_file = project_dir / "main.py"
    main_file.write_text('''"""Main module for sample project."""

def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers.
    
    This function always returns the correct sum.
    """
    return a + b

def complex_function(x, y, z):
    """A complex function for testing complexity analysis."""
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            else:
                return x + y - z
        else:
            if z > 0:
                return x - y + z
            else:
                return x - y - z
    else:
        if y > 0:
            if z > 0:
                return -x + y + z
            else:
                return -x + y - z
        else:
            if z > 0:
                return -x - y + z
            else:
                return -x - y - z

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, value: float) -> float:
        """Add a value to the result."""
        self.result += value
        return self.result
    
    def multiply(self, value: float) -> float:
        """Multiply the result by a value."""
        self.result *= value
        return self.result
''')
    
    # Create test file
    test_file = project_dir / "test_main.py"
    test_file.write_text('''"""Tests for main module."""

import pytest
from main import calculate_sum, Calculator

def test_calculate_sum():
    """Test the calculate_sum function."""
    assert calculate_sum(2, 3) == 5
    assert calculate_sum(-1, 1) == 0
    assert calculate_sum(0, 0) == 0

def test_calculator():
    """Test the Calculator class."""
    calc = Calculator()
    assert calc.add(5) == 5
    assert calc.multiply(2) == 10

def test_edge_cases():
    """Test edge cases."""
    assert calculate_sum(999999, 1) == 1000000
''')
    
    # Create README
    readme = project_dir / "README.md"
    readme.write_text('''# Sample Python Project

This project provides a simple calculator with the following features:

- **Fast calculations**: Can handle up to 1000 operations per second
- **Type safe**: All functions are fully typed
- **Well tested**: 100% code coverage
- **Secure**: No security vulnerabilities

## API

The `calculate_sum` function always returns the correct sum of two integers.

```python
result = calculate_sum(2, 3)  # Returns 5
```

The `Calculator` class supports addition and multiplication operations.

## Performance

This calculator is optimized for speed and can process complex calculations efficiently.
''')
    
    # Create requirements.txt
    requirements = project_dir / "requirements.txt"
    requirements.write_text("pytest>=7.0.0\n")
    
    # Create pytest.ini
    pytest_ini = project_dir / "pytest.ini"
    pytest_ini.write_text("""[pytest]
testpaths = .
python_files = test_*.py
""")
    
    return project_dir


@pytest.fixture
def sample_javascript_project(temp_dir):
    """Create a sample JavaScript project for testing."""
    project_dir = temp_dir / "javascript_project"
    project_dir.mkdir()
    
    # Create main JavaScript file
    main_js = project_dir / "index.js"
    main_js.write_text('''/**
 * Calculator module
 * @module calculator
 */

/**
 * Adds two numbers together
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} The sum of a and b
 */
function add(a, b) {
    return a + b;
}

/**
 * Multiplies two numbers
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} The product of a and b
 */
function multiply(a, b) {
    return a * b;
}

/**
 * A complex function with multiple branches
 */
function complexLogic(condition1, condition2, condition3) {
    if (condition1) {
        if (condition2) {
            if (condition3) {
                return 'all true';
            } else {
                return 'c3 false';
            }
        } else {
            return 'c2 false';
        }
    } else {
        return 'c1 false';
    }
}

module.exports = { add, multiply, complexLogic };
''')
    
    # Create test file
    test_js = project_dir / "index.test.js"
    test_js.write_text('''const { add, multiply, complexLogic } = require('./index');

describe('Calculator', () => {
    test('adds numbers correctly', () => {
        expect(add(2, 3)).toBe(5);
        expect(add(-1, 1)).toBe(0);
    });
    
    test('multiplies numbers correctly', () => {
        expect(multiply(3, 4)).toBe(12);
        expect(multiply(0, 5)).toBe(0);
    });
    
    test('handles complex logic', () => {
        expect(complexLogic(true, true, true)).toBe('all true');
        expect(complexLogic(false, true, true)).toBe('c1 false');
    });
});
''')
    
    # Create package.json
    package_json = project_dir / "package.json"
    package_json.write_text(json.dumps({
        "name": "sample-js-project",
        "version": "1.0.0",
        "description": "A sample JavaScript project for testing",
        "main": "index.js",
        "scripts": {
            "test": "jest"
        },
        "devDependencies": {
            "jest": "^29.0.0"
        }
    }, indent=2))
    
    # Create README
    readme = project_dir / "README.md"
    readme.write_text('''# Sample JavaScript Project

A high-performance calculator library that supports:

- Lightning fast arithmetic operations
- Zero dependencies
- Full TypeScript support (coming soon)
- 100% test coverage

## Features

- `add(a, b)` - Returns the sum of two numbers
- `multiply(a, b)` - Returns the product of two numbers
- Handles complex conditional logic

## Security

This library has been audited and contains no security vulnerabilities.
''')
    
    return project_dir


@pytest.fixture
def sample_multi_language_project(temp_dir):
    """Create a sample multi-language project for testing."""
    project_dir = temp_dir / "multi_language"
    project_dir.mkdir()
    
    # Python component
    python_dir = project_dir / "python"
    python_dir.mkdir()
    
    utils_py = python_dir / "utils.py"
    utils_py.write_text('''"""Utility functions."""

def validate_input(data: str) -> bool:
    """Validate input data for security."""
    # Simple validation - no SQL injection
    dangerous_chars = ["'", '"', ";", "--", "/*", "*/"]
    return not any(char in data for char in dangerous_chars)

def process_data(data: list) -> dict:
    """Process data with high performance."""
    return {"count": len(data), "data": data}
''')
    
    # Go component
    go_dir = project_dir / "go"
    go_dir.mkdir()
    
    main_go = go_dir / "main.go"
    main_go.write_text('''package main

import (
    "fmt"
    "crypto/sha256"
)

// HashPassword securely hashes a password
func HashPassword(password string) string {
    hash := sha256.Sum256([]byte(password))
    return fmt.Sprintf("%x", hash)
}

// ValidateToken checks if a token is valid
func ValidateToken(token string) bool {
    // Simplified validation
    return len(token) == 32
}

func main() {
    fmt.Println("Multi-language project")
}
''')
    
    main_test_go = go_dir / "main_test.go"
    main_test_go.write_text('''package main

import "testing"

func TestHashPassword(t *testing.T) {
    hash := HashPassword("test123")
    if len(hash) != 64 {
        t.Errorf("Expected hash length 64, got %d", len(hash))
    }
}

func TestValidateToken(t *testing.T) {
    if !ValidateToken("12345678901234567890123456789012") {
        t.Error("Valid token rejected")
    }
    if ValidateToken("short") {
        t.Error("Invalid token accepted")
    }
}
''')
    
    # Create go.mod
    go_mod = go_dir / "go.mod"
    go_mod.write_text('''module example.com/multiproject

go 1.19
''')
    
    # TypeScript component
    ts_dir = project_dir / "typescript"
    ts_dir.mkdir()
    
    api_ts = ts_dir / "api.ts"
    api_ts.write_text('''/**
 * API client for external services
 */

interface User {
    id: number;
    name: string;
    email: string;
}

export class ApiClient {
    private baseUrl: string;
    
    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }
    
    async getUser(id: number): Promise<User> {
        const response = await fetch(`${this.baseUrl}/users/${id}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch user: ${response.status}`);
        }
        return response.json();
    }
    
    async createUser(user: Omit<User, 'id'>): Promise<User> {
        const response = await fetch(`${this.baseUrl}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(user)
        });
        return response.json();
    }
}
''')
    
    # Create tsconfig.json
    tsconfig = ts_dir / "tsconfig.json"
    tsconfig.write_text(json.dumps({
        "compilerOptions": {
            "target": "ES2020",
            "module": "commonjs",
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True
        }
    }, indent=2))
    
    # Main README
    readme = project_dir / "README.md"
    readme.write_text('''# Multi-Language Project

A comprehensive project demonstrating multiple programming languages working together.

## Components

### Python Module
- **Secure input validation**: Prevents SQL injection and XSS attacks
- **High-performance data processing**: Handles up to 10,000 requests per second

### Go Service
- **Cryptographically secure**: Uses SHA-256 for password hashing
- **Token validation**: Implements secure token validation

### TypeScript API Client
- **Type-safe**: Full TypeScript support with strict mode
- **Async/await**: Modern asynchronous programming
- **Error handling**: Comprehensive error handling

## Security Features

1. Input sanitization in all languages
2. Secure password hashing
3. Token-based authentication
4. No known vulnerabilities

## Performance

- Python: O(n) complexity for data processing
- Go: Constant time token validation
- TypeScript: Async operations for non-blocking I/O

## Testing

All components have 100% test coverage.
''')
    
    return project_dir


@pytest.fixture
def mock_subprocess_run(monkeypatch):
    """Mock subprocess.run for testing external tool calls."""
    class MockResult:
        def __init__(self, stdout="", stderr="", returncode=0):
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = returncode
    
    def mock_run(*args, **kwargs):
        cmd = args[0]
        
        # Mock different tools
        if "pylint" in cmd:
            return MockResult(
                stdout=json.dumps([{
                    "type": "convention",
                    "module": "test",
                    "obj": "",
                    "line": 1,
                    "column": 0,
                    "path": "test.py",
                    "symbol": "missing-docstring",
                    "message": "Missing module docstring",
                    "message-id": "C0111"
                }]),
                returncode=0
            )
        elif "mypy" in cmd:
            return MockResult(
                stdout="test.py:10: error: Incompatible return value type\n",
                returncode=1
            )
        elif "bandit" in cmd:
            return MockResult(
                stdout=json.dumps({
                    "metrics": {
                        "SEVERITY.HIGH": 1,
                        "SEVERITY.MEDIUM": 2,
                        "SEVERITY.LOW": 3
                    },
                    "results": [{
                        "filename": "test.py",
                        "line_number": 5,
                        "issue_severity": "HIGH",
                        "issue_confidence": "HIGH",
                        "issue_text": "Possible hardcoded password",
                        "test_id": "B105"
                    }]
                }),
                returncode=0
            )
        elif "pytest" in cmd:
            return MockResult(
                stdout="3 passed, 0 failed",
                returncode=0
            )
        elif "npm" in cmd and "test" in cmd:
            return MockResult(
                stdout=json.dumps({
                    "numTotalTests": 3,
                    "numPassedTests": 3,
                    "numFailedTests": 0,
                    "numPendingTests": 0
                }),
                returncode=0
            )
        elif "go" in cmd and "test" in cmd:
            return MockResult(
                stdout="PASS\nok\texample.com/test\t0.001s\n",
                returncode=0
            )
        
        return MockResult()
    
    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run