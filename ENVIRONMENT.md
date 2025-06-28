# Python Environment Management

This document explains how Python environments are managed in the Vibe Verifier project.

## Recommended Approach: uv

We strongly recommend using [uv](https://github.com/astral-sh/uv) for Python package management. It's a drop-in replacement for pip that's 10-100x faster and provides better dependency resolution.

### Why uv?

- **Speed**: 10-100x faster than pip for installing packages
- **Reliability**: Better dependency resolution algorithm
- **Compatibility**: Works as a drop-in replacement for pip
- **Modern**: Written in Rust for maximum performance
- **Simple**: No configuration needed, just works

### Quick Start with uv

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup the project
git clone https://github.com/vibes/vibe-verifier.git
cd vibe-verifier
./scripts/setup-dev-uv.sh
```

## Environment Isolation

The project uses Python virtual environments to isolate dependencies from the system Python:

1. **Virtual Environment Location**: `.venv/` in the project root
2. **Python Version**: 3.10 (specified in `.python-version`)
3. **Minimum Version**: Python 3.8+ is required

## Dependency Files

- `requirements.txt` - Production dependencies only
- `requirements-dev.txt` - Development dependencies (includes production)
- `pyproject.toml` - Package metadata and tool configuration
- `.python-version` - Specifies Python version for pyenv users

## Setup Options

### 1. Automated Setup with uv (Recommended)

```bash
./scripts/setup-dev-uv.sh
```

This script:
- Installs uv if not present
- Creates a virtual environment
- Installs all dependencies using uv
- Sets up pre-commit hooks

### 2. Automated Setup with pip

```bash
./scripts/setup-dev.sh
```

This script:
- Uses system Python if 3.8+
- Creates a virtual environment
- Installs dependencies with pip
- Sets up pre-commit hooks

### 3. Manual Setup

```bash
# Create virtual environment
uv venv .venv --python 3.10  # or: python3 -m venv .venv

# Activate it
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements-dev.txt  # or: pip install -r requirements-dev.txt
uv pip install -e .  # or: pip install -e .
```

## Using direnv (Optional)

For automatic environment activation, you can use direnv:

1. Install direnv:
   ```bash
   brew install direnv  # macOS
   sudo apt install direnv  # Ubuntu
   ```

2. Add to your shell:
   ```bash
   echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
   ```

3. Allow the `.envrc`:
   ```bash
   direnv allow
   ```

Now the virtual environment activates automatically when you enter the project directory.

## Managing Dependencies

### Adding Dependencies

```bash
# Add a production dependency
uv pip install package_name
echo "package_name>=1.0.0" >> requirements.txt

# Add a development dependency
uv pip install package_name
echo "package_name>=1.0.0" >> requirements-dev.txt
```

### Updating Dependencies

```bash
# Update all packages
uv pip install --upgrade -r requirements-dev.txt

# Update specific package
uv pip install --upgrade package_name
```

### Checking Outdated Packages

```bash
uv pip list --outdated
```

## Common Commands

```bash
# Activate environment
source .venv/bin/activate

# Check Python version
python --version

# Install all dependencies
uv pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black src/ tests/

# Run linting
flake8 src/
```

## Troubleshooting

### "uv: command not found"

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Then restart your shell or run:
source ~/.cargo/env
```

### "Python version X.X not found"

The project requires Python 3.8+. Install it using:
- **pyenv**: `pyenv install 3.10.12`
- **apt**: `sudo apt install python3.10`
- **brew**: `brew install python@3.10`

### Virtual environment not activating

Make sure you're in the project directory and run:
```bash
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

### Permission denied errors

If you get permission errors, you might need to:
```bash
# Remove and recreate the virtual environment
rm -rf .venv/
uv venv .venv --python 3.10
```

## CI/CD Considerations

The GitHub Actions workflow automatically:
- Uses uv when available for faster CI builds
- Tests on Python 3.8, 3.9, 3.10, and 3.11
- Runs on Ubuntu, macOS, and Windows
- Caches dependencies for faster builds

## Best Practices

1. **Always use a virtual environment** - Never install packages globally
2. **Use uv for speed** - It's significantly faster than pip
3. **Pin dependencies** - Use specific versions in requirements files
4. **Keep dependencies minimal** - Only add what's necessary
5. **Update regularly** - Keep dependencies up to date for security
6. **Document new dependencies** - Add comments explaining why they're needed