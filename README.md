# OEN-Project_MUx1 - Multi-User Experience (MUx) Server

## Table of Contents

- [What is this?](#what-is-this)
- [Use Cases](#use-cases)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Email Verification](#email-verification)
- [Security Considerations](#security-considerations)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## What is this?

**OEN-Project_MUx1** is the foundation of a **MUD-style multi-user online experience server** (MUx = Multi-User eXperience). It provides the core infrastructure for running a persistent multi-user world where players can register accounts, create named characters, connect in real time, and interact through a browser-based terminal or a Python CLI client.

Think of it as the back-end engine for a text-based online game or interactive shared world: users sign up, verify their email, create characters, log in, and communicate with other connected players — all through a classic MUD-inspired terminal interface powered by [xterm.js](https://xtermjs.org/) and [Socket.IO](https://socket.io/).

## Use Cases

| Use Case | How this project helps |
|----------|----------------------|
| **Text-based online game (MUD/MUX)** | Provides the complete back-end: accounts, characters, real-time multi-user sessions, and a browser-based terminal |
| **Learning project** | Demonstrates Flask, Socket.IO, SQLAlchemy, Docker, and SSH tunnels in a single working codebase |
| **Prototype / Starter kit** | Ready-made auth + character system you can extend with game logic, rooms, items, quests, etc. |
| **Self-hosted chat / multi-user tool** | The Socket.IO layer and `who` / messaging commands can be repurposed for any shared real-time experience |
| **API integration testing** | A full REST API with signup / login / verification that can serve as a mock auth backend for other projects |

---

### Key capabilities

| Capability | Description |
|------------|-------------|
| **Account system** | Register, email-verify, and log in as a named user |
| **Character system** | Create and manage multiple characters per account |
| **Real-time terminal** | Browser-based xterm.js terminal with MUD-style commands |
| **Live user list** | `who` command shows all currently connected players |
| **REST API** | Full HTTP API for integration with any client |
| **Python CLI client** | Interactive command-line client with Socket.IO support |
| **SSH tunnel support** | Secure remote access through SSH tunnels |
| **Docker deployment** | One-command spin-up via Docker Compose |

## Features

- **User Authentication**: Sign up, login with email verification
- **Email Verification**: Authentication codes sent via email (or printed to console in dev mode)
- **Character Management**: Create and list named characters with levels and descriptions
- **MUD-style Terminal**: Browser-based xterm.js terminal at `/terminal` with commands: `who`, `server_info`, `characters`, `create <name>`
- **Web Auth UI**: Form-based sign-up/login interface at `/`
- **Dual Communication**: REST API (`/api/*`) and Socket.IO real-time events
- **Server Status**: Live uptime and connected-user count via `/api/server-status`
- **SSH Tunnel Support**: Secure remote access through SSH tunnels
- **Docker Integration**: Seamless deployment with Docker Compose
- **Database**: SQLite (dev) / PostgreSQL (prod) via SQLAlchemy ORM
- **Security**: Werkzeug password hashing, cryptographically random verification codes

## Architecture

```
├── server/               # Server application
│   ├── app.py           # Flask + Socket.IO server, REST API, database models
│   ├── email_service.py # Email verification service (SMTP / console fallback)
│   └── static/
│       ├── index.html   # Web auth UI  (served at /)
│       └── terminal.html # MUD-style xterm.js terminal (served at /terminal)
├── client/              # Python CLI client
│   └── client.py        # Interactive client with Socket.IO support
├── config/              # Configuration utilities
│   └── ssh_tunnel.py    # SSH tunnel helper
├── docker-compose.yml   # Docker orchestration
├── Dockerfile.server    # Server Docker image
├── Dockerfile.client    # Client Docker image
└── requirements.txt     # Python dependencies
```

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- SSH access (for SSH tunnel functionality)

## Installation

### Local Development

#### Quick Start (Unix/Linux/Mac)

Use the startup scripts for the easiest setup:

```bash
# Clone and navigate to repository
git clone https://github.com/ULFHEDNAR-JAKE/OEN-Project_MUx1.git
cd OEN-Project_MUx1

# Start server (auto-creates venv and installs dependencies)
./start_server.sh
```

In a new terminal:
```bash
# Start client
./start_client.sh
```

#### Manual Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ULFHEDNAR-JAKE/OEN-Project_MUx1.git
   cd OEN-Project_MUx1
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables (optional)**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Docker Deployment

1. **Build and start services**
   ```bash
   docker-compose up -d
   ```

2. **View logs**
   ```bash
   docker-compose logs -f
   ```

3. **Stop services**
   ```bash
   docker-compose down
   ```

## Usage

### Running the Server

**Local:**
```bash
cd server
python app.py
```

**Docker:**
```bash
docker-compose up server
```

The server will start on `http://localhost:5000`

| URL | Interface |
|-----|-----------|
| `http://localhost:5000/` | Web auth UI (sign up / login) |
| `http://localhost:5000/terminal` | MUD-style xterm.js terminal |
| `http://localhost:5000/api/health` | Health check endpoint |

### Running the Client

**Local:**
```bash
cd client
python client.py
```

**Docker:**
```bash
docker-compose run --rm client
```

### SSH Tunnel Configuration

To access the server through an SSH tunnel:

1. **Set environment variables:**
   ```bash
   export SSH_HOST=your-server.com
   export SSH_USER=username
   export SSH_KEY_PATH=/path/to/ssh/key
   export LOCAL_PORT=5000
   export REMOTE_PORT=5000
   ```

2. **Start SSH tunnel:**
   ```bash
   python config/ssh_tunnel.py
   ```

3. **Connect client to tunneled server:**
   ```bash
   export SERVER_URL=http://localhost:5000
   python client/client.py
   ```

## API Documentation

### REST API Endpoints

#### Health Check
```
GET /api/health
```
Response:
```json
{
  "status": "healthy",
  "message": "Server is running"
}
```

#### Sign Up
```
POST /api/signup
Content-Type: application/json

{
  "username": "user123",
  "email": "user@example.com",
  "password": "securepassword"
}
```
Response:
```json
{
  "message": "User created successfully. Please check your email for verification code.",
  "user_id": 1
}
```

#### Verify Email
```
POST /api/verify-email
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```
Response:
```json
{
  "message": "Email verified successfully"
}
```

#### Login
```
POST /api/login
Content-Type: application/json

{
  "username": "user123",
  "password": "securepassword"
}
```
Response:
```json
{
  "message": "Login successful",
  "user": { "id": 1, "username": "user123", "email": "user@example.com" },
  "characters": [...],
  "server_status": { "uptime": "00:12:34", "connected_users": 3, "total_users": 42, "status": "online" }
}
```

#### Resend Verification Code
```
POST /api/resend-verification
Content-Type: application/json

{
  "email": "user@example.com"
}
```
Response:
```json
{
  "message": "Verification code sent"
}
```

#### Server Status
```
GET /api/server-status
```
Response:
```json
{
  "uptime": "01:23:45",
  "uptime_seconds": 5025,
  "connected_users": 3,
  "total_users": 42,
  "status": "online"
}
```

#### List Characters
```
GET /api/characters?user_id=1
```
Response:
```json
{
  "characters": [
    { "id": 1, "name": "Thorin", "description": "Dwarf warrior", "level": 5, "created_at": "...", "last_login": "..." }
  ]
}
```

#### Create Character
```
POST /api/characters
Content-Type: application/json

{
  "user_id": 1,
  "name": "Thorin",
  "description": "A stout dwarf warrior"
}
```
Response:
```json
{
  "message": "Character created successfully",
  "character": { "id": 1, "name": "Thorin", "description": "A stout dwarf warrior", "level": 1, ... }
}
```

### Socket.IO Events

#### Connect
- **Event**: `connect`
- **Description**: Establish WebSocket connection
- **Response**: `connected` event with server status and connection details

#### Authenticate
- **Event**: `authenticate`
- **Payload**: 
  ```json
  { "username": "user123", "password": "securepassword" }
  ```
- **Response**: `auth_success` (with user info, characters, and server status) or `auth_error`

#### Send Message
- **Event**: `message`
- **Payload**: Any message string
- **Response**: `message` event with echo

#### Terminal Command
- **Event**: `command`
- **Payload**:
  ```json
  { "cmd": "who", "args": [] }
  ```
- **Response**: `cmd_response` event with formatted terminal output

### Terminal Commands

The browser-based terminal at `/terminal` supports the following MUD-style commands:

| Command | Description |
|---------|-------------|
| `who` | List all currently connected users |
| `server_info` | Display server uptime and stats |
| `characters` | List your characters (requires login) |
| `create <name> [description]` | Create a new character (requires login) |

## Configuration

### Environment Variables

#### Server Configuration
- `SECRET_KEY`: Flask secret key for session management
- `PORT`: Server port (default: 5000)
- `DATABASE_URL`: Database connection string (default: sqlite:///auth.db)

#### Email Configuration
- `SMTP_SERVER`: SMTP server address (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP port (default: 587)
- `SMTP_USERNAME`: SMTP username
- `SMTP_PASSWORD`: SMTP password (use app-specific password for Gmail)
- `FROM_EMAIL`: Sender email address

#### SSH Tunnel Configuration
- `SSH_HOST`: SSH server hostname
- `SSH_PORT`: SSH port (default: 22)
- `SSH_USER`: SSH username
- `SSH_KEY_PATH`: Path to SSH private key
- `LOCAL_PORT`: Local forwarding port
- `REMOTE_PORT`: Remote server port

#### Client Configuration
- `SERVER_URL`: Server URL (default: http://localhost:5000)

## Email Verification

The application supports email verification through SMTP. In development mode (when SMTP credentials are not configured), verification codes are printed to the console.

### Gmail Configuration

For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an app-specific password
3. Use the app password in `SMTP_PASSWORD`

Example:
```bash
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export FROM_EMAIL=your-email@gmail.com
```

## Security Considerations

- **Passwords**: Hashed using Werkzeug's `generate_password_hash`
- **Verification Codes**: 6-digit codes valid for 24 hours
- **Environment Variables**: Store sensitive data in `.env` file (not committed)
- **SSH Keys**: Use key-based authentication for SSH tunnels
- **CORS**: Configured to allow cross-origin requests (configure appropriately for production)

## Docker Networks

The application uses a Docker network (`auth_network`) for service communication. The server is accessible from the client using the service name `server`.

## Development

### Project Structure
```
server/
  app.py              # Main Flask application, REST API, Socket.IO events, database models
  email_service.py    # Email sending functionality (SMTP / console fallback)
  static/
    index.html        # Web auth UI (sign up / login / verify)
    terminal.html     # MUD-style xterm.js terminal interface

client/
  client.py           # Interactive Python CLI client

config/
  ssh_tunnel.py       # SSH tunnel utilities
```

### Database Models

| Model | Purpose | Key fields |
|-------|---------|-----------|
| `User` | Account record | `username`, `email`, `password_hash`, `is_verified` |
| `Character` | In-world character | `name`, `description`, `level`, `user_id` (FK → User) |

> **Note**: No migrations are configured. Any schema change requires deleting `server/auth.db` and restarting.

### Testing the Application

1. **Start the server**
2. **Open `http://localhost:5000`** in a browser (web UI) **or run the Python client** (`python client/client.py`)
3. **Follow the interactive flow:**
   - Sign up with username, email, password
   - Check server console (dev) or email inbox (prod) for verification code
   - Verify email with the 6-digit code
   - Login with credentials
   - Open `http://localhost:5000/terminal` to use the MUD-style terminal
   - Type `who` to see connected users, `characters` to list your characters, `create <name>` to make a new one

## Troubleshooting

### Connection Issues
- Ensure the server is running on the correct port
- Check firewall settings
- Verify `SERVER_URL` in client configuration

### Email Issues
- Check SMTP credentials
- For Gmail, ensure app-specific password is used
- In development, codes are printed to console

### SSH Tunnel Issues
- Verify SSH credentials and key permissions
- Ensure SSH service is running on remote server
- Check port forwarding configuration

### Docker Issues
- Ensure Docker daemon is running
- Check container logs: `docker-compose logs`
- Verify network connectivity between containers

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.
