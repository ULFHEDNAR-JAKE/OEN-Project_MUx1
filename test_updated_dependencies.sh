#!/bin/bash
#
# Test script for updated Python dependencies
# This script should be run after installing updated dependencies
#

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "==============================================="
echo "Testing Updated Python Dependencies"
echo "==============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        return 1
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Step 1: Install updated dependencies
echo "Step 1: Installing updated dependencies..."
echo "-------------------------------------------"
pip install -r requirements.txt --upgrade
print_status $? "Dependencies installed"
echo ""

# Step 2: Verify installed versions
echo "Step 2: Verifying installed versions..."
echo "-------------------------------------------"
python3 << 'EOF'
import sys

expected_versions = {
    'Flask': '3.1.2',
    'Flask-SocketIO': '5.5.1',
    'Flask-SQLAlchemy': '3.1.1',
    'Flask-Cors': '6.0.1',
    'python-socketio': '5.14.3',
    'Werkzeug': '3.1.3',
    'requests': '2.32.5',
    'python-engineio': '4.12.3'
}

import importlib.metadata
all_correct = True

for package, expected_version in expected_versions.items():
    try:
        actual_version = importlib.metadata.version(package)
        if actual_version == expected_version:
            print(f"✓ {package:25} {actual_version}")
        else:
            print(f"✗ {package:25} {actual_version} (expected {expected_version})")
            all_correct = False
    except importlib.metadata.PackageNotFoundError:
        print(f"✗ {package:25} NOT INSTALLED")
        all_correct = False

sys.exit(0 if all_correct else 1)
EOF
print_status $? "All package versions correct"
echo ""

# Step 3: Test basic imports
echo "Step 3: Testing basic imports..."
echo "-------------------------------------------"
python3 << 'EOF'
import sys

modules = [
    'flask',
    'flask_socketio',
    'flask_sqlalchemy',
    'flask_cors',
    'socketio',
    'werkzeug',
    'requests',
    'engineio'
]

all_imported = True
for module in modules:
    try:
        __import__(module)
        print(f"✓ Successfully imported {module}")
    except ImportError as e:
        print(f"✗ Failed to import {module}: {e}")
        all_imported = False

sys.exit(0 if all_imported else 1)
EOF
print_status $? "All modules imported successfully"
echo ""

# Step 4: Test server startup
echo "Step 4: Testing server startup..."
echo "-------------------------------------------"
print_info "Starting server in background..."

cd server
timeout 15 python app.py > /tmp/server_test.log 2>&1 &
SERVER_PID=$!
cd ..

# Wait for server to start
sleep 5

# Test health endpoint
if curl -s --max-time 10 http://localhost:5000/api/health > /dev/null 2>&1; then
    print_status 0 "Server started successfully"
    HEALTH_RESPONSE=$(curl -s http://localhost:5000/api/health)
    echo "   Health check response: $HEALTH_RESPONSE"
else
    print_status 1 "Server failed to start"
    echo "   Server logs:"
    cat /tmp/server_test.log | head -20
fi

# Stop server
kill $SERVER_PID 2>/dev/null || true
sleep 2
echo ""

# Step 5: Test API endpoints
echo "Step 5: Testing API endpoints..."
echo "-------------------------------------------"

cd server
timeout 15 python app.py > /tmp/server_api_test.log 2>&1 &
SERVER_PID=$!
cd ..
sleep 5

# Test signup endpoint
print_info "Testing signup endpoint..."
SIGNUP_RESPONSE=$(curl -s -X POST http://localhost:5000/api/signup \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser'"$(date +%s)"'","email":"test'"$(date +%s)"'@example.com","password":"testpass123"}' \
    2>/dev/null || echo "FAILED")

if [[ "$SIGNUP_RESPONSE" == *"User created successfully"* ]]; then
    print_status 0 "Signup endpoint working"
else
    print_status 1 "Signup endpoint failed"
    echo "   Response: $SIGNUP_RESPONSE"
fi

kill $SERVER_PID 2>/dev/null || true
echo ""

# Step 6: Test Socket.IO connectivity
echo "Step 6: Testing Socket.IO connectivity..."
echo "-------------------------------------------"

cd server
timeout 15 python app.py > /tmp/server_socketio_test.log 2>&1 &
SERVER_PID=$!
cd ..
sleep 5

python3 << 'EOF'
import socketio
import time

try:
    sio = socketio.Client()
    connected = False
    
    @sio.on('connected')
    def on_connected(data):
        global connected
        connected = True
        print("✓ Socket.IO connection successful")
    
    sio.connect('http://localhost:5000', wait_timeout=5)
    time.sleep(2)
    sio.disconnect()
    
    exit(0 if connected else 1)
except Exception as e:
    print(f"✗ Socket.IO connection failed: {e}")
    exit(1)
EOF
SOCKETIO_STATUS=$?

kill $SERVER_PID 2>/dev/null || true

if [ $SOCKETIO_STATUS -eq 0 ]; then
    print_status 0 "Socket.IO connectivity verified"
else
    print_status 1 "Socket.IO connectivity test failed"
fi
echo ""

# Summary
echo "==============================================="
echo "Test Summary"
echo "==============================================="
echo ""
echo "All critical functionality has been tested."
echo "If all tests passed, the dependency update is successful!"
echo ""
echo "For manual testing, you can:"
echo "  1. Start the server: cd server && python app.py"
echo "  2. Start the client: cd client && python client.py"
echo "  3. Test the web interface: http://localhost:5000"
echo ""
