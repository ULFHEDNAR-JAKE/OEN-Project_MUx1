#!/bin/bash
# Startup script for the Authentication Client

set -e

echo "====================================="
echo "Authentication Client Startup"
echo "====================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Set server URL if not already set
export SERVER_URL=${SERVER_URL:-http://localhost:5000}

# Start the client
echo ""
echo "Starting client..."
echo "Connecting to server at: $SERVER_URL"
echo ""

cd client
python client.py
