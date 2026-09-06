#!/bin/bash

PORT=${1:-8000}

# Add ~/.local/bin to PATH if not already present
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install Pipenv if not installed
if ! command -v pipenv >/dev/null 2>&1; then
    echo "Pipenv not found. Installing..."
    python3 -m pip install --user pipenv

    # Refresh PATH after installation
    export PATH="$HOME/.local/bin:$PATH"
fi

# Go to the sso backend directory
cd "$(dirname "$0")" || exit 1

# Install dependencies if the Pipenv environment doesn't exist
if ! pipenv --venv >/dev/null 2>&1; then
    echo "Creating virtual environment and installing dependencies..."
    pipenv install
else
    echo "Virtual environment already exists."
fi

echo "Starting FastAPI on port $PORT..."

pipenv run uvicorn app.main:app \
    --host localhost \
    --port "$PORT" \
    --reload