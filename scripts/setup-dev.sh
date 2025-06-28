#!/bin/bash
# Development environment setup script

set -e  # Exit on error

echo "Setting up Vibe Verifier development environment..."

# Detect Python version
PYTHON_CMD=""
if command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
elif command -v python3.8 &> /dev/null; then
    PYTHON_CMD="python3.8"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc) -eq 1 ]]; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.8 or higher is required but not found."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

echo "Using Python: $PYTHON_CMD ($(${PYTHON_CMD} --version))"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing production dependencies..."
pip install -r requirements.txt

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

# Install package in editable mode
echo "Installing vibe-verifier in editable mode..."
pip install -e .

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Run initial checks
echo "Running initial checks..."
echo "- Python version: $(python --version)"
echo "- pip version: $(pip --version)"
echo "- Installed packages: $(pip list | wc -l) packages"

# Test import
python -c "import src; print(f'✓ Vibe Verifier {src.__version__} imported successfully')"

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Or install direnv for automatic activation:"
echo "  brew install direnv  # macOS"
echo "  sudo apt install direnv  # Ubuntu/Debian"
echo "  echo 'eval \"\$(direnv hook bash)\"' >> ~/.bashrc"