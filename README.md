# OEN-Project_MUx1 - Client/Server Authentication Application

A comprehensive client-server authentication system with email verification, supporting both HTTP REST API and Socket.IO real-time communication. The application includes SSH tunnel support for secure remote access and Docker integration for seamless deployment.

## Features

- **User Authentication**: Sign up, login with email verification
- **Email Verification**: Authentication codes sent via email
- **Dual Communication**: REST API and Socket.IO support
- **SSH Tunnel Support**: Secure remote access through SSH tunnels
- **Docker Integration**: Seamless deployment with Docker Compose
- **Database**: SQLite with SQLAlchemy ORM
- **Security**: Password hashing with Werkzeug

## Documentation

- **[Implementation Plan](IMPLEMENTATION_PLAN.md)**: Project roadmap and development plan
- **[Architecture](ARCHITECTURE.md)**: Detailed system architecture and design
- **[Quick Start](QUICKSTART.md)**: Get started quickly
- **[Contributing](CONTRIBUTING.md)**: Contribution guidelines
- **[Security](SECURITY.md)**: Security policies and reporting

## Architecture

```
├── server/               # Server application
│   ├── app.py           # Flask server with Socket.IO
│   └── email_service.py # Email verification service
├── client/              # Client application
│   └── client.py        # Interactive client with Socket.IO
├── config/              # Configuration
│   └── ssh_tunnel.py    # SSH tunnel utilities
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
  "user": {
    "id": 1,
    "username": "user123",
    "email": "user@example.com"
  }
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

### Socket.IO Events

#### Connect
- **Event**: `connect`
- **Description**: Establish WebSocket connection
- **Response**: `connected` event with connection details

#### Authenticate
- **Event**: `authenticate`
- **Payload**: 
  ```json
  {
    "username": "user123",
    "password": "securepassword"
  }
  ```
- **Response**: `auth_success` or `auth_error`

#### Send Message
- **Event**: `message`
- **Payload**: Any message string
- **Response**: `message` event with echo

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
  app.py              # Main Flask application
  email_service.py    # Email sending functionality

client/
  client.py           # Interactive client application

config/
  ssh_tunnel.py       # SSH tunnel utilities
```

### Testing the Application

1. **Start the server**
2. **Run the client**
3. **Follow the interactive menu:**
   - Sign up with username, email, password
   - Check console/email for verification code
   - Verify email with the code
   - Login with credentials
   - Connect via Socket.IO
   - Authenticate via Socket.IO
   - Send messages

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
