# Copilot Instructions for OEN-Project_MUx1

## Project Overview

OEN-Project_MUx1 is a comprehensive client-server authentication system with email verification, supporting both HTTP REST API and Socket.IO real-time communication. The application includes SSH tunnel support for secure remote access and Docker integration for seamless deployment.

**Tech Stack:**
- **Backend**: Flask 3.1.2, Flask-SocketIO 5.5.1, SQLAlchemy 3.1.1
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Authentication**: Werkzeug password hashing, email verification codes
- **Real-time**: Socket.IO with bidirectional messaging
- **Deployment**: Docker Compose, native Python 3.11+

## Architecture Overview

Flask authentication server with **dual communication protocols**:
- **REST API** (`/api/*`) - HTTP endpoints for signup, login, email verification
- **Socket.IO** - Real-time bidirectional messaging for authenticated users

**Client interfaces**: 
- CLI (`client/client.py`) - Python command-line client
- Web GUI (`server/static/index.html` served at `/`) - Form-based interface
- Web Terminal (`server/static/terminal.html` served at `/terminal`) - MUD-style xterm.js interface

**Key files**: 
- `server/app.py` - Flask+SocketIO server with API endpoints and database models
- `client/client.py` - Python CLI client with Socket.IO support
- `server/email_service.py` - Email sending (SMTP/console fallback)
- `server/static/` - Web interfaces (index.html, terminal.html)

## Critical Development Knowledge

### Email Verification Gotcha
When SMTP credentials are not configured, verification codes print to the **server console only** (not the client). Check `docker-compose logs` or server terminal output during testing.

### Authentication Flow (Must Understand)
1. `/api/signup` → creates user with `is_verified=False`, generates 6-digit code (24hr expiry)
2. `/api/verify-email` → validates code, sets `is_verified=True`
3. `/api/login` → **rejects unverified users with HTTP 403**
4. Socket.IO `authenticate` → same verification requirement

### Database Behavior
- **No migrations configured** - schema changes require deleting `auth.db`
- Database file created in working directory where server runs (typically `server/`)
- Password hashing: `user.set_password()` / `user.check_password()` via Werkzeug

## Build, Run, and Test Commands

### Development Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Server (auto-creates venv on Unix)
./start_server.sh  # or: cd server && python app.py

# Client  
./start_client.sh  # or: cd client && python client.py

# Docker (recommended for production)
docker-compose up -d              # Start services
docker-compose logs -f            # View logs
docker-compose down               # Stop services
docker-compose run --rm client    # Run client interactively
```

### Testing
```bash
# Health check
curl http://localhost:5000/api/health

# Sign up new user
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"pass123"}'

# Verify email (check server console for code)
curl -X POST http://localhost:5000/api/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}'

# Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"pass123"}'
```

**Note**: No automated test suite currently exists. Manual testing required for all changes.

## Development Workflows

### Adding New API Endpoints
```python
# In server/app.py - follow existing JSON response pattern
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    """Brief description of endpoint purpose"""
    data = request.get_json()
    if not data or not data.get('required_field'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Your logic here
        result = process_data(data)
        return jsonify({'message': 'Success', 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Adding Socket.IO Events
```python
# In server/app.py
@socketio.on('event_name')
def handle_event(data):
    """Handle Socket.IO event"""
    # Validate input
    if not data:
        emit('error', {'message': 'Invalid data'})
        return
    
    # Process and respond
    emit('response_event', {'result': data})
```

### Database Model Changes
```python
# Add column to User model in server/app.py
class User(db.Model):
    # ... existing fields ...
    new_field = db.Column(db.String(100))  # Add new column

# Then delete database and restart (no migrations configured)
# rm server/auth.db && cd server && python app.py
```

**Important**: Schema changes require deleting `auth.db` - no migrations exist.

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `SECRET_KEY` | Random | Set in production |
| `DATABASE_URL` | `sqlite:///auth.db` | Use `postgresql://...` for prod |
| `SMTP_USERNAME/PASSWORD` | None | Triggers console fallback if unset |
| `SERVER_URL` | `http://localhost:5000` | Client target |

## Project-Specific Constraints

- **No automated tests** - Manual testing only. Adding pytest infrastructure is high priority.
- **No database migrations** - Schema changes require deleting `auth.db` and restarting server.
- **CORS wide open** (`cors_allowed_origins="*"`) - Restrict in production to specific domains.
- **Stateless auth** - No JWT/session tokens yet. Each API call requires credentials.
- **SQLite limitations** - Single-writer bottleneck. Use PostgreSQL for production.
- **Email in dev mode** - Verification codes print to **server console only** when SMTP not configured.
- **Windows compatibility** - Shell scripts won't work. Use `venv\Scripts\activate` and run Python directly.

## Code Style and Conventions

### Python
- Follow PEP 8 style guidelines
- Use type hints for function parameters: `def function(param: str) -> bool:`
- Add docstrings to public functions and classes
- Use existing patterns: JSON responses, error handling with try/except
- Password handling: Use `user.set_password()` and `user.check_password()` methods

### Database
- Models defined in `server/app.py` using SQLAlchemy ORM
- Password hashing via Werkzeug's `generate_password_hash`/`check_password_hash`
- Verification codes: 6 digits, 24-hour expiry, generated with `secrets.randbelow(10)`
- Database file location: `server/auth.db` (working directory where server runs)

### API Design
- All endpoints under `/api/` prefix
- Return JSON with `{'message': '...', 'data': {...}}` for success
- Return JSON with `{'error': '...'}` for failures with appropriate HTTP status codes
- POST for state-changing operations, GET for read-only
- Use appropriate status codes: 200 (OK), 201 (Created), 400 (Bad Request), 403 (Forbidden), 404 (Not Found), 500 (Server Error)

## Security Best Practices

### Password Security
- **NEVER** store passwords in plain text
- Always use `user.set_password(password)` to hash passwords with Werkzeug
- Verify passwords with `user.check_password(password)`
- Password complexity enforcement should be added client-side and server-side

### Email Verification
- 6-digit codes generated with `secrets.randbelow(10)` for cryptographic randomness
- Codes expire after 24 hours (`verification_code_expires`)
- Codes must be cleared after successful verification (`verification_code = None`)
- Unverified users are blocked from login with HTTP 403

### Environment Variables
- Store sensitive config in `.env` file (never commit to git)
- Required for production: `SECRET_KEY`, `DATABASE_URL`, SMTP credentials
- Use strong random `SECRET_KEY` in production: `secrets.token_hex(32)`

### Common Security Issues to Avoid
- **SQL Injection**: Use SQLAlchemy ORM, never raw SQL with user input
- **XSS**: Sanitize user input in web interfaces, use Content-Security-Policy headers
- **CSRF**: Implement CSRF tokens for state-changing operations
- **Rate Limiting**: Not implemented - add for production (429 Too Many Requests)
- **HTTPS**: Required for production to encrypt credentials in transit

## Troubleshooting Guide

### Port 5000 Already in Use
```bash
# Find process using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Note: On macOS, AirPlay Receiver uses port 5000 by default
# Disable: System Preferences > Sharing > AirPlay Receiver
```

### Database Issues
```bash
# Database locked or corrupt
rm server/auth.db
cd server && python app.py

# Schema changes not reflecting
# Delete database (no migrations configured)
rm server/auth.db
cd server && python app.py
```

### Email Verification Code Not Received
- **Development mode**: Code prints to **server console**, not client
- Check `docker-compose logs -f` for Docker deployments
- Check terminal running `python app.py` for local development
- **Production**: Configure SMTP environment variables in `.env`

### Connection Refused / Server Not Accessible
```bash
# Verify server is running
curl http://localhost:5000/api/health

# Check firewall settings
# Ensure SERVER_URL matches in client configuration

# For Docker: ensure containers are on same network
docker-compose ps
docker network ls
```

### Socket.IO Connection Failures
- Verify server is running and accessible
- Check CORS settings (currently allows all origins)
- Inspect browser console for WebSocket errors
- Ensure client uses correct URL (http:// not https:// in dev)

### Import Errors After Dependency Updates
```bash
# Reinstall dependencies
pip install -r requirements.txt

# If issues persist, recreate virtual environment
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Additional Resources

- **README.md** - Comprehensive project documentation and features
- **ARCHITECTURE.md** - Detailed system architecture and design decisions
- **QUICKSTART.md** - Quick setup guide for new users
- **CONTRIBUTING.md** - Contribution guidelines and code of conduct
- **SECURITY.md** - Security policy and vulnerability reporting
- **Docker Documentation** - See `docker-compose.yml` for service configuration

## Common Pitfalls to Avoid

1. **Don't commit `.env` files** - Contains sensitive credentials
2. **Don't modify database schema without deleting auth.db** - No migrations configured
3. **Don't forget to verify email before login** - Login fails with 403 for unverified users
4. **Don't look for verification codes in client output** - They're in server console (dev mode)
5. **Don't use SQLite for production** - Use PostgreSQL for concurrent access
6. **Don't skip manual testing** - No automated tests exist yet
7. **Don't hardcode credentials** - Use environment variables via `.env` file
