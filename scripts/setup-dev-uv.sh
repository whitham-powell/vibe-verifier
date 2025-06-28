#!/bin/bash
# Development environment setup script using uv

set -e  # Exit on error

echo "Setting up Vibe Verifier development environment with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    
    # Detect OS and install uv
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install uv
        else
            curl -LsSf https://astral.sh/uv/install.sh | sh
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        # Windows
        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    else
        echo "Unsupported OS. Please install uv manually from: https://github.com/astral-sh/uv"
        exit 1
    fi
    
    # Add to PATH if needed
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "Using uv version: $(uv --version)"

# Create virtual environment with uv
echo "Creating virtual environment..."
uv venv .venv --python 3.10

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Install dependencies with uv
echo "Installing production dependencies..."
uv pip install -r requirements.txt

echo "Installing development dependencies..."
uv pip install -r requirements-dev.txt

# Install package in editable mode
echo "Installing vibe-verifier in editable mode..."
uv pip install -e .

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Run initial checks
echo "Running initial checks..."
echo "- Python version: $(python --version)"
echo "- uv version: $(uv --version)"
echo "- Installed packages: $(uv pip list | wc -l) packages"

# Test import
python -c "import src; print(f'✓ Vibe Verifier {src.__version__} imported successfully')"

echo ""
echo "✅ Development environment setup complete with uv!"
echo ""
echo "To activate the environment in the future, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To install new packages, use:"
echo "  uv pip install <package>"
echo ""
echo "Benefits of using uv:"
echo "  - 10-100x faster than pip"
echo "  - Better dependency resolution"
echo "  - Automatic version management"
echo "  - Built-in virtual environment support"