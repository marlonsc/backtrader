#!/bin/bash
# Create Python virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install required packages if not already installed
echo "Checking and installing required packages..."
pip install -q backtrader pandas numpy matplotlib psycopg2-binary

# Show installed packages and environment info
echo -e "\nPython environment setup complete!"
echo "Python version: $(python --version)"
echo "Environment location: $(which python)"
echo -e "\nTo activate this environment in the future, run:\nsource .venv/bin/activate"
