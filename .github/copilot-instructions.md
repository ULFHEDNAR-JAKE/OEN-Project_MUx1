# Copilot Instructions for OEN-Project_MUx1

## Project Overview

OEN-Project_MUx1 is a comprehensive client-server authentication system with email verification, supporting both HTTP REST API and Socket.IO real-time communication. The application includes SSH tunnel support for secure remote access and Docker integration for seamless deployment.

### Key Features
- User authentication with email verification
- Dual communication protocols (REST API and Socket.IO)
- SSH tunnel support for secure remote access
- Docker integration for containerized deployment
- SQLite database with SQLAlchemy ORM
- Password hashing with Werkzeug

## Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: Flask 3.0.0
- **Real-time Communication**: Flask-SocketIO 5.3.5, python-socketio 5.10.0
- **Database**: SQLite (via Flask-SQLAlchemy 3.1.1), extensible to PostgreSQL (requires psycopg2-binary and DATABASE_URL)
- **Security**: Werkzeug 3.0.1 for password hashing
- **CORS**: Flask-CORS 4.0.0
- **HTTP Client**: requests 2.31.0
- **Deployment**: Docker and Docker Compose

## Project Structure

```
├── server/               # Server application
│   ├── app.py           # Flask server with Socket.IO and API endpoints
│   ├── email_service.py # Email verification service
│   └── static/          # Web interface files
├── client/              # Client application
│   └── client.py        # Interactive Python CLI client
├── config/              # Configuration utilities
│   └── ssh_tunnel.py    # SSH tunnel support
├── .github/             # GitHub configuration
├── docker-compose.yml   # Docker orchestration
├── Dockerfile.server    # Server Docker image
├── Dockerfile.client    # Client Docker image
├── requirements.txt     # Python dependencies
├── start_server.sh      # Server startup script
├── start_client.sh      # Client startup script
└── *.md                 # Documentation files
```

## Development Guidelines

### Setup and Running

1. **Local Development**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ./start_server.sh  # or: cd server && python app.py
   ./start_client.sh  # or: cd client && python client.py
   ```

2. **Docker Development**:
   ```bash
   docker-compose up -d
   docker-compose logs -f
   ```

### Code Style and Conventions

- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Add docstrings for functions and classes
- Keep functions focused and single-purpose
- Use type hints where appropriate
- Maintain consistent indentation (4 spaces)

### API Endpoints

Key REST API endpoints in `server/app.py`:
- `GET /` - Serve web interface
- `GET /api/health` - Health check
- `POST /api/signup` - Register new user
- `POST /api/verify-email` - Verify email with code
- `POST /api/login` - User login
- `POST /api/resend-code` - Resend verification code

### Socket.IO Events

Real-time events handled in `server/app.py`:
- `connect` - Client connection
- `disconnect` - Client disconnection
- `authenticate` - Socket.IO authentication
- `send_message` - Send message to server
- `receive_message` - Receive message from server

### Database Schema

The User model in `server/app.py` includes:
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email address
- `password_hash` - Hashed password (never plain text)
- `is_verified` - Email verification status
- `verification_code` - 6-digit verification code
- `verification_code_expires` - Code expiration timestamp
- `created_at` - Account creation timestamp

### Security Considerations

- **Always hash passwords** using Werkzeug's `generate_password_hash`
- **Never store plain text passwords**
- Use environment variables for sensitive configuration (SMTP credentials, secret keys)
- Verification codes are 6-digit random numbers with 24-hour expiration
- CORS is enabled (should be restricted in production)
- HTTPS is recommended for production deployments

### Environment Variables

Key configuration via environment variables:
- `SECRET_KEY` - Flask secret key for session management
- `PORT` - Server port (default: 5000)
- `DATABASE_URL` - Database connection string (default: sqlite:///auth.db)
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` - Email configuration
- `FROM_EMAIL` - Sender email address
- `SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_KEY_PATH` - SSH tunnel configuration
- `SERVER_URL` - Client server URL (default: http://localhost:5000)

### Testing Approach

**Current State**: The project currently uses manual testing. There are no automated unit tests yet.

**Manual Testing Checklist**:
1. Start the server
2. Test sign up with new user
3. Check verification code in console (development mode)
4. Test email verification
5. Test login functionality
6. Test Socket.IO connection
7. Test message sending via Socket.IO
8. Test API endpoints with curl or HTTP client

**Testing Commands**:
```bash
# Health check
curl http://localhost:5000/api/health

# Sign up
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"securepass123"}'
```

**High Priority Testing Needs** (see CONTRIBUTING.md):
- Unit tests for server endpoints
- Integration tests for auth flow
- Email verification testing
- Socket.IO connection testing

### Documentation

When making changes, update relevant documentation:
- **README.md** - Feature documentation, installation, configuration
- **QUICKSTART.md** - Getting started guide, quick setup instructions
- **ARCHITECTURE.md** - System design, component details, data flow
- **CONTRIBUTING.md** - Contribution guidelines, coding standards
- **SECURITY.md** - Security policies and vulnerability reporting
- **Code comments** - Inline documentation for complex logic

### Priority Areas for Contribution

**High Priority**:
- Unit tests for server endpoints
- Integration tests for auth flow
- Password reset functionality
- Two-factor authentication (2FA)
- Rate limiting for API endpoints
- CAPTCHA integration

**Medium Priority**:
- User profile management
- OAuth2 integration (Google, GitHub)
- Persistent sessions with tokens
- PostgreSQL migration and setup (requires psycopg2-binary driver)
- Kubernetes deployment guide

**Nice to Have**:
- Mobile app client
- Desktop application
- Admin dashboard
- Usage analytics
- Internationalization (i18n)

### Common Tasks

**Adding a new API endpoint**:
1. Add route decorator and function in `server/app.py`
2. Follow existing patterns for error handling
3. Return JSON responses with appropriate status codes
4. Update API documentation in ARCHITECTURE.md
5. Add manual testing instructions

**Adding a new Socket.IO event**:
1. Add event handler with `@socketio.on('event_name')` in `server/app.py`
2. Use `emit()` to send responses
3. Handle errors gracefully
4. Document the event in ARCHITECTURE.md

**Database schema changes**:
1. Modify the User model in `server/app.py`
2. Consider migration strategy (SQLAlchemy migrations not yet configured)
3. Update documentation
4. Test with fresh database

### Deployment Considerations

**Development**:
- Uses SQLite database
- Verification codes printed to console
- CORS enabled for all origins

**Production**:
- Consider PostgreSQL database (requires psycopg2-binary driver: `pip install psycopg2-binary`, then set `DATABASE_URL` to PostgreSQL connection string, e.g., `postgresql://user:password@localhost/dbname`)
- Configure real SMTP server for email delivery
- Set strong `SECRET_KEY`
- Restrict CORS origins
- Use production WSGI server (gunicorn/uwsgi)
- Set up reverse proxy (nginx/apache)
- Enable HTTPS with SSL/TLS certificates
- Implement rate limiting
- Set up monitoring and logging

### Troubleshooting

**Port Already in Use**:
```bash
lsof -i :5000
kill -9 <PID>
```

**Database Issues**:
```bash
rm auth.db  # Start fresh (database created in directory where server runs)
```

**Connection Issues**:
- Ensure server is running: `curl http://localhost:5000/api/health`
- Check firewall settings
- Verify correct port in configuration

**Email Not Sending**:
- Check SMTP credentials
- In development, codes are printed to console
- For Gmail, use app-specific passwords

## License

This project is licensed under the Apache License 2.0. By contributing, you agree that your contributions will be licensed under the same license.

## Additional Resources

- **Repository**: https://github.com/ULFHEDNAR-JAKE/OEN-Project_MUx1
- **Issue Tracker**: GitHub Issues
- **Documentation**: See README.md, QUICKSTART.md, ARCHITECTURE.md, CONTRIBUTING.md
