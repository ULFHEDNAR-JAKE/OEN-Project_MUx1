#!/bin/bash
# Startup script for the Authentication Server

set -e

echo "====================================="
echo "Authentication Server Startup"
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

# Start the server
echo ""
echo "Starting server..."
echo "Access the web interface at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

cd server
python app.py
