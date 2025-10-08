# Increase timeout for slow networks (default is 30s)
$env:UV_HTTP_TIMEOUT = "120"

# Install multiple Python versions
uv python install 3.10 3.11 3.12 3.13

# Set Python version (change as needed)
$PYTHON_VERSION = "3.13"

# Create a virtual environment with the specified Python version
uv venv --python $PYTHON_VERSION

# Install AF and all dependencies
uv sync --dev

# Install all the tools and dependencies
uv run poe install

# Install pre-commit hooks
uv run poe pre-commit-install
