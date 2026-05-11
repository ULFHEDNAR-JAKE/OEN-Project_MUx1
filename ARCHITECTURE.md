# Architecture Documentation

## System Overview

OEN-Project_MUx1 is a **MUD-style multi-user experience server** (MUx = Multi-User eXperience). It provides the core infrastructure for a persistent, real-time multi-user world: account registration with email verification, named in-world characters, a browser-based xterm.js terminal with classic MUD commands, and both REST API and Socket.IO communication channels.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
├──────────────┬──────────────┬──────────────┬───────────────┤
│ Web Auth UI  │  MUD Terminal│ Python CLI   │ External APIs │
│  /           │ /terminal    │ client.py    │ (REST)        │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬────────┘
       │              │              │              │
       │ HTTP/WS      │ Socket.IO    │ HTTP/WS      │ HTTP
       │                                            │
┌──────▼──────────────────────────────────────────▼──────────┐
│                   Server Layer                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Flask Application (server/app.py)            │  │
│  │  ┌─────────────────┐  ┌──────────────────────────┐  │  │
│  │  │  REST API        │  │  Socket.IO Handler       │  │  │
│  │  │  /api/*          │  │  connect / authenticate  │  │  │
│  │  │                 │  │  message / command        │  │  │
│  │  └─────────────────┘  └──────────────────────────┘  │  │
│  │                                                       │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │     Email Service (email_service.py)         │   │  │
│  │  │  - SMTP / console fallback                   │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                   Data Layer                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         SQLAlchemy ORM                               │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐ │  │
│  │  │  User Model          │  │  Character Model      │ │  │
│  │  │  - id, username      │  │  - id, name          │ │  │
│  │  │  - email             │  │  - description       │ │  │
│  │  │  - password_hash     │  │  - level             │ │  │
│  │  │  - is_verified       │  │  - user_id (FK)      │ │  │
│  │  │  - verification_code │  │  - is_active         │ │  │
│  │  └──────────────────────┘  └──────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Database (SQLite dev / PostgreSQL prod)      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Server Application (`server/app.py`)

**Responsibilities:**
- Handle HTTP REST API requests
- Manage Socket.IO WebSocket connections
- User authentication and session management
- Character management (create, list)
- In-memory connected-session tracking
- Database operations via SQLAlchemy ORM
- Email verification coordination

**Key Features:**
- Flask web framework
- CORS enabled for cross-origin requests
- RESTful API endpoints
- Real-time bidirectional communication via Socket.IO
- Password hashing with PBKDF2-SHA256 (Python standard library)
- SQLite database (configurable to PostgreSQL)

**API Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serve web auth UI |
| `/terminal` | GET | Serve MUD-style xterm.js terminal |
| `/api/health` | GET | Health check |
| `/api/server-status` | GET | Uptime, connected users, registered users |
| `/api/signup` | POST | Register new user |
| `/api/verify-email` | POST | Verify email with code |
| `/api/login` | POST | Authenticate user (returns characters + server status) |
| `/api/resend-verification` | POST | Resend verification code |
| `/api/characters` | GET | List characters for a user (`?user_id=`) |
| `/api/characters` | POST | Create a new character |

**Socket.IO Events:**

| Event | Direction | Purpose |
|-------|-----------|---------|
| `connect` | Client→Server | Client lifecycle event; server registers session and sends status |
| `connected` | Server→Client | Send connection info |
| `authenticate` | Client→Server | Authenticate via WebSocket |
| `auth_success` | Server→Client | Auth successful (user, characters, server status) |
| `auth_error` | Server→Client | Authentication failed |
| `message` | Bidirectional | Send/receive messages (echo) |
| `command` | Client→Server | Terminal MUD command |
| `cmd_response` | Server→Client | Terminal command output |
| `disconnect` | Server→Client | Connection closed |

**Terminal commands** (sent via `command` Socket.IO event):

| Command | Requires login | Description |
|---------|---------------|-------------|
| `who` | No | List connected users |
| `server_info` | No | Show uptime and user counts |
| `characters` | Yes | List your characters |
| `create <name> [desc]` | Yes | Create a new character |

### 2. Email Service (`server/email_service.py`)

**Responsibilities:**
- Send verification emails via SMTP
- Format email content (text and HTML)
- Handle SMTP configuration
- Fallback to console output in development when SMTP credentials are absent

### 3. Web Auth UI (`server/static/index.html`)

**Features:**
- Single-page application served at `/`
- Tab-based interface: Sign Up, Login, Email Verify, Chat (Socket.IO message echo)
- Real-time status indicators
- Socket.IO client integration

### 4. MUD-style Terminal (`server/static/terminal.html`)

**Features:**
- Full-screen xterm.js terminal served at `/terminal`
- Socket.IO real-time communication
- ANSI colour output for menus and tables
- MUD-style commands: `who`, `server_info`, `characters`, `create`
- Authentication flow built into the terminal

### 5. Python CLI Client (`client/client.py`)

**Features:**
- Interactive menu-driven interface
- HTTP API client and Socket.IO client
- Sign up, verify, login, send messages

### 6. SSH Tunnel Support (`config/ssh_tunnel.py`)

**Purpose:** Enable secure access to the server through SSH port forwarding for remote and encrypted deployments.

## Data Flow

### Sign Up Flow

```
Client → POST /api/signup {username, email, password}
       → Server validates, creates User (is_verified=False)
       → Generates 6-digit code (24hr expiry)
       → Sends email (SMTP) or prints to console (dev)
       ← 201 {message, user_id}
```

### Login Flow

```
Client → POST /api/login {username, password}
       → Server looks up user, checks password hash
       → Rejects with 403 if is_verified=False
       ← 200 {user, characters[], server_status}
```

### Socket.IO Authentication Flow

```
Client → socket.connect()
       ← 'connected' {server_status}
Client → emit('authenticate', {username, password})
       ← 'auth_success' {user, characters[], server_status}
    or ← 'auth_error'   {error}
```

### Terminal Command Flow

```
Client → emit('command', {cmd: 'who', args: []})
       ← 'cmd_response' {output: [...ANSI lines...], error: null}
```

## Security Considerations

- Passwords hashed with PBKDF2-SHA256 (Python standard library)
- 6-digit verification codes generated via `secrets.randbelow` (cryptographically random)
- Codes expire after 24 hours and are cleared after use
- CORS currently wide-open (`*`) — restrict to specific origins in production
- HTTPS strongly recommended for production
- SSH tunnel support for encrypted remote channels
- Sensitive config via environment variables (`.env`, never committed)

## Database Schema

### User Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary Key | Unique user identifier |
| username | String(80) | Unique, Not Null | Login name |
| email | String(120) | Unique, Not Null | Email address |
| password_hash | String(255) | Not Null | PBKDF2-SHA256 password hash |
| is_verified | Boolean | Default: False | Email verification status |
| verification_code | String(6) | Nullable | Active verification code |
| verification_code_expires | DateTime | Nullable | Code expiration |
| created_at | DateTime | Default: now() | Account creation time |

### Character Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary Key | Character ID |
| user_id | Integer | FK → User, Not Null | Owning account |
| name | String(80) | Unique, Not Null | Character name |
| description | String(255) | Default: '' | Short description |
| level | Integer | Default: 1 | Character level |
| created_at | DateTime | Default: now() | Creation time |
| last_login | DateTime | Nullable | Last play time |
| is_active | Boolean | Default: True | Soft-delete flag |

> **Note**: No migrations are configured. Schema changes require deleting `server/auth.db` and restarting.

## Configuration Management

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SECRET_KEY | random | Flask secret key |
| PORT | 5000 | Server port |
| DATABASE_URL | sqlite:///auth.db | Database connection string |
| SMTP_SERVER | smtp.gmail.com | SMTP server address |
| SMTP_PORT | 587 | SMTP server port |
| SMTP_USERNAME | - | SMTP username |
| SMTP_PASSWORD | - | SMTP password |
| FROM_EMAIL | - | Sender email address |
| SSH_HOST | - | SSH tunnel host |
| SSH_PORT | 22 | SSH tunnel port |
| SSH_USER | - | SSH username |
| SSH_KEY_PATH | - | SSH private key path |
| SERVER_URL | http://localhost:5000 | Client target URL |

## Deployment Options

### 1. Local Development
```bash
./start_server.sh  # starts server at http://localhost:5000
./start_client.sh  # starts Python CLI client
```

### 2. Docker Compose
```bash
docker-compose up -d
```

### 3. Production Recommendations
- Use production WSGI server (gunicorn)
- Configure PostgreSQL database
- Set up reverse proxy (nginx) with HTTPS
- Restrict CORS to specific origins
- Set a strong random `SECRET_KEY`
- Configure real SMTP credentials
- Add rate limiting

## Scalability Considerations

### Current Architecture
- Single server instance
- SQLite database (single-writer)
- In-memory session tracking (lost on restart)

### Production Scaling Options
1. **Database**: PostgreSQL with connection pooling
2. **Horizontal scaling**: Multiple instances + Redis for shared session state
3. **Async email**: Celery task queue
4. **Caching**: Redis for rate limiting and response caching

## Future Enhancements

1. **Game features**: Rooms/zones, items, combat, quests
2. **Authentication**: OAuth2, 2FA, password reset, persistent sessions (JWT)
3. **RBAC**: Roles, admin commands, character permissions
4. **Infrastructure**: Kubernetes, auto-scaling, CDN
5. **Security**: Rate limiting, CAPTCHA, brute-force protection

## License

Apache License 2.0 — see LICENSE file for details

