# Architecture Documentation

## System Overview

The OEN-Project_MUx1 is a client-server authentication system designed with security, scalability, and ease of deployment in mind. It supports multiple client types (web browser, Python CLI) and provides both HTTP REST API and real-time Socket.IO communication.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
├──────────────┬──────────────────────┬──────────────────────┤
│ Web Browser  │   Python CLI Client  │   External Clients   │
│  (HTML/JS)   │   (client/client.py) │   (via REST API)     │
└──────┬───────┴──────────┬───────────┴──────────┬───────────┘
       │                  │                       │
       │ HTTP/WS          │ HTTP/Socket.IO        │ HTTP/HTTPS
       │                  │                       │
┌──────▼──────────────────▼───────────────────────▼───────────┐
│                   Server Layer                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Flask Application (server/app.py)           │    │
│  │  ┌────────────────┐  ┌─────────────────────────┐   │    │
│  │  │  REST API      │  │  Socket.IO Handler      │   │    │
│  │  │  Endpoints     │  │  (Real-time Events)     │   │    │
│  │  └────────────────┘  └─────────────────────────┘   │    │
│  │                                                      │    │
│  │  ┌────────────────────────────────────────────┐    │    │
│  │  │     Email Service (email_service.py)       │    │    │
│  │  │  - SMTP Configuration                      │    │    │
│  │  │  - Verification Code Delivery              │    │    │
│  │  └────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                   Data Layer                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         SQLAlchemy ORM                              │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │  User Model                                   │  │    │
│  │  │  - id, username, email, password_hash        │  │    │
│  │  │  - is_verified, verification_code            │  │    │
│  │  │  - verification_code_expires, created_at     │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Database (SQLite/PostgreSQL)                │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Server Application (`server/app.py`)

**Responsibilities:**
- Handle HTTP REST API requests
- Manage Socket.IO WebSocket connections
- User authentication and session management
- Database operations via SQLAlchemy ORM
- Email verification coordination

**Key Features:**
- Flask web framework
- CORS enabled for cross-origin requests
- RESTful API endpoints
- Real-time bidirectional communication via Socket.IO
- Password hashing with Werkzeug
- SQLite database (configurable to PostgreSQL)

**API Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serve web interface |
| `/api/health` | GET | Health check |
| `/api/signup` | POST | Register new user |
| `/api/verify-email` | POST | Verify email with code |
| `/api/login` | POST | Authenticate user |
| `/api/resend-verification` | POST | Resend verification code |

**Socket.IO Events:**

| Event | Direction | Purpose |
|-------|-----------|---------|
| `connect` | Server→Client | Connection established |
| `connected` | Server→Client | Send connection info |
| `authenticate` | Client→Server | Authenticate via WebSocket |
| `auth_success` | Server→Client | Authentication successful |
| `auth_error` | Server→Client | Authentication failed |
| `message` | Bidirectional | Send/receive messages |
| `disconnect` | Server→Client | Connection closed |

### 2. Email Service (`server/email_service.py`)

**Responsibilities:**
- Send verification emails via SMTP
- Format email content (text and HTML)
- Handle SMTP configuration
- Fallback to console output in development

**Configuration:**
- SMTP server and port
- Authentication credentials
- From email address
- Development mode detection

### 3. Web Client (`server/static/index.html`)

**Features:**
- Single-page application (SPA)
- Responsive design
- Tab-based interface (Sign Up, Login, Verify, Chat)
- Real-time status indicators
- Socket.IO client integration

**UI Components:**
- Sign Up form with validation
- Login form
- Email verification form
- Real-time chat interface
- Status indicator (connected/disconnected)
- Success/error message display

### 4. Python CLI Client (`client/client.py`)

**Features:**
- Interactive menu-driven interface
- HTTP API client
- Socket.IO client
- Secure password input (hidden)
- User-friendly command-line experience

**Capabilities:**
- Sign up new users
- Verify email addresses
- Login via HTTP
- Connect via Socket.IO
- Authenticate via Socket.IO
- Send real-time messages
- Resend verification codes

### 5. SSH Tunnel Support (`config/ssh_tunnel.py`)

**Purpose:**
Enable secure access to the server through SSH tunneling for:
- Remote server access
- Encrypted communication
- Port forwarding
- Secure deployment scenarios

**Features:**
- SSH key-based authentication
- Configurable local/remote ports
- Process management
- Status monitoring

## Data Flow

### Sign Up Flow

```
┌─────────┐                ┌────────┐               ┌──────────┐
│ Client  │                │ Server │               │ Database │
└────┬────┘                └───┬────┘               └────┬─────┘
     │                         │                         │
     │ POST /api/signup        │                         │
     │ {username, email, pwd}  │                         │
     ├────────────────────────>│                         │
     │                         │                         │
     │                         │ Validate input          │
     │                         │ Generate hash           │
     │                         │ Create verification code│
     │                         │                         │
     │                         │ INSERT user             │
     │                         ├────────────────────────>│
     │                         │                         │
     │                         │<────────────────────────┤
     │                         │                         │
     │                         │ Send verification email │
     │                         │ (via SMTP/console)      │
     │                         │                         │
     │ 201 Created             │                         │
     │ {message, user_id}      │                         │
     │<────────────────────────┤                         │
     │                         │                         │
```

### Login Flow

```
┌─────────┐                ┌────────┐               ┌──────────┐
│ Client  │                │ Server │               │ Database │
└────┬────┘                └───┬────┘               └────┬─────┘
     │                         │                         │
     │ POST /api/login         │                         │
     │ {username, password}    │                         │
     ├────────────────────────>│                         │
     │                         │                         │
     │                         │ SELECT user             │
     │                         ├────────────────────────>│
     │                         │                         │
     │                         │<────────────────────────┤
     │                         │                         │
     │                         │ Verify password hash    │
     │                         │ Check is_verified       │
     │                         │                         │
     │ 200 OK                  │                         │
     │ {message, user}         │                         │
     │<────────────────────────┤                         │
     │                         │                         │
```

### Socket.IO Authentication Flow

```
┌─────────┐                ┌────────┐               ┌──────────┐
│ Client  │                │ Server │               │ Database │
└────┬────┘                └───┬────┘               └────┬─────┘
     │                         │                         │
     │ Socket.IO Connect       │                         │
     ├────────────────────────>│                         │
     │                         │                         │
     │ 'connected' event       │                         │
     │<────────────────────────┤                         │
     │                         │                         │
     │ 'authenticate' event    │                         │
     │ {username, password}    │                         │
     ├────────────────────────>│                         │
     │                         │                         │
     │                         │ SELECT user             │
     │                         ├────────────────────────>│
     │                         │                         │
     │                         │<────────────────────────┤
     │                         │                         │
     │                         │ Verify credentials      │
     │                         │                         │
     │ 'auth_success' event    │                         │
     │ {message, user}         │                         │
     │<────────────────────────┤                         │
     │                         │                         │
```

## Security Considerations

### Password Security
- Passwords are hashed using Werkzeug's `generate_password_hash`
- Uses PBKDF2-SHA256 algorithm
- Passwords are never stored in plain text
- Password validation on both client and server

### Email Verification
- 6-digit random verification codes
- Codes expire after 24 hours
- One-time use (cleared after verification)
- Secure random number generation

### Communication Security
- CORS configured (should be restricted in production)
- HTTPS recommended for production
- SSH tunnel support for encrypted channels
- Environment variables for sensitive configuration

### Session Management
- No persistent sessions stored
- Stateless authentication
- Client-side session management
- Socket.IO session isolation per connection

## Deployment Options

### 1. Local Development
```bash
./start_server.sh
./start_client.sh
```

### 2. Docker Compose
```bash
docker-compose up -d
```

### 3. Production Deployment
- Use production WSGI server (gunicorn/uwsgi)
- Configure PostgreSQL database
- Set up reverse proxy (nginx/apache)
- Enable HTTPS with SSL/TLS certificates
- Configure real SMTP server
- Set strong SECRET_KEY
- Implement rate limiting
- Set up monitoring and logging

## Database Schema

### User Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary Key | Unique user identifier |
| username | String(80) | Unique, Not Null | User's login name |
| email | String(120) | Unique, Not Null | User's email address |
| password_hash | String(255) | Not Null | Hashed password |
| is_verified | Boolean | Default: False | Email verification status |
| verification_code | String(6) | Nullable | Current verification code |
| verification_code_expires | DateTime | Nullable | Code expiration time |
| created_at | DateTime | Default: now() | Account creation timestamp |

## Configuration Management

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SECRET_KEY | random | Flask secret key |
| PORT | 5000 | Server port |
| DATABASE_URL | sqlite:///auth.db | Database connection |
| SMTP_SERVER | smtp.gmail.com | SMTP server address |
| SMTP_PORT | 587 | SMTP server port |
| SMTP_USERNAME | - | SMTP username |
| SMTP_PASSWORD | - | SMTP password |
| FROM_EMAIL | - | Sender email address |
| SSH_HOST | - | SSH tunnel host |
| SSH_PORT | 22 | SSH tunnel port |
| SSH_USER | - | SSH username |
| SSH_KEY_PATH | - | SSH private key path |

## Scalability Considerations

### Current Architecture
- Single server instance
- SQLite database
- In-memory sessions
- No load balancing

### Production Scaling Options
1. **Horizontal Scaling**
   - Multiple server instances
   - Load balancer (nginx/HAProxy)
   - Session persistence (Redis)
   - Database replication

2. **Database**
   - PostgreSQL for production
   - Connection pooling
   - Read replicas
   - Database clustering

3. **Caching**
   - Redis for session storage
   - Cache API responses
   - Rate limiting with Redis

4. **Message Queue**
   - Async email sending
   - Task queue (Celery)
   - Background jobs

## Testing Strategy

### Unit Tests
- Model validation
- Password hashing
- Verification code generation
- API endpoint logic

### Integration Tests
- HTTP API endpoints
- Socket.IO events
- Database operations
- Email service

### End-to-End Tests
- Complete user flows
- Web interface interactions
- Client application functionality

## Monitoring and Logging

### Recommended Monitoring
- Application performance (response times)
- Error rates and exceptions
- Database query performance
- Active connections
- Resource usage (CPU, memory)

### Logging Strategy
- Application logs (Flask)
- Access logs (nginx)
- Error logs
- Audit logs (authentication events)
- Debug logs (development only)

## Future Enhancements

1. **Authentication**
   - OAuth2 integration
   - Two-factor authentication (2FA)
   - Password reset functionality
   - Remember me / persistent sessions

2. **Features**
   - User profiles
   - Role-based access control (RBAC)
   - API rate limiting
   - Account deactivation

3. **Infrastructure**
   - Kubernetes deployment
   - Auto-scaling
   - CDN integration
   - Multi-region support

4. **Security**
   - CAPTCHA integration
   - Brute force protection
   - IP whitelisting/blacklisting
   - Security headers

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   - Check for existing server process
   - Use different port via PORT environment variable

2. **Database Locked**
   - SQLite limitation with concurrent access
   - Consider PostgreSQL for production

3. **Email Not Sending**
   - Check SMTP credentials
   - Verify firewall rules
   - Check console output in development

4. **Socket.IO Connection Failed**
   - Verify server is running
   - Check CORS configuration
   - Inspect browser console for errors

## License

Apache License 2.0 - See LICENSE file for details
