# Copilot Instructions for OEN-Project_MUx1

## Architecture Overview

Flask authentication server with **dual communication protocols**:
- **REST API** (`/api/*`) - HTTP endpoints for signup, login, email verification
- **Socket.IO** - Real-time bidirectional messaging for authenticated users

**Client interfaces**: 
- CLI (`client/client.py`) - Python command-line client
- Web GUI (`server/static/index.html` served at `/`) - Form-based interface
- Web Terminal (`server/static/terminal.html` served at `/terminal`) - MUD-style xterm.js interface

Key files: `server/app.py` (Flask+SocketIO), `client/client.py` (CLI), `server/email_service.py` (SMTP/console)

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

## Quick Commands

```bash
# Server (auto-creates venv on Unix)
./start_server.sh  # or: cd server && python app.py

# Client  
./start_client.sh  # or: cd client && python client.py

# Docker
docker-compose up -d && docker-compose logs -f

# Test API
curl http://localhost:5000/api/health
curl -X POST http://localhost:5000/api/signup -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"pass123"}'
```

## Code Patterns

### Adding REST Endpoint
```python
# In server/app.py - follow existing JSON response pattern
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    data = request.get_json()
    if not data or not data.get('required_field'):
        return jsonify({'error': 'Missing required fields'}), 400
    # ... logic ...
    return jsonify({'message': 'Success', 'data': result}), 200
```

### Adding Socket.IO Event
```python
@socketio.on('event_name')
def handle_event(data):
    # Validate, process, emit response
    emit('response_event', {'result': data})
```

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `SECRET_KEY` | Random | Set in production |
| `DATABASE_URL` | `sqlite:///auth.db` | Use `postgresql://...` for prod |
| `SMTP_USERNAME/PASSWORD` | None | Triggers console fallback if unset |
| `SERVER_URL` | `http://localhost:5000` | Client target |

## Project-Specific Constraints

- **No automated tests** - manual testing only (adding pytest is high priority)
- **CORS wide open** (`cors_allowed_origins="*"`) - restrict in production
- **Stateless auth** - no persistent sessions/tokens yet
- Windows: Use `venv\Scripts\activate` instead of shell scripts

## Troubleshooting

- **Port 5000 busy**: `lsof -i :5000` then kill process (macOS: AirPlay may use 5000)
- **Database locked/corrupt**: Delete `server/auth.db`, restart server
- **Verification code not found**: Check server console, not client output
