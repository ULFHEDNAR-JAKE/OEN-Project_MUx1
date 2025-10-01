# Quick Start Guide

Get up and running with the Authentication Application in minutes!

## 🚀 Quick Start with Docker

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/ULFHEDNAR-JAKE/OEN-Project_MUx1.git
cd OEN-Project_MUx1

# Start the server
docker-compose up -d server

# Open your browser
open http://localhost:5000
```

That's it! You now have a fully functional authentication server running.

## 💻 Quick Start without Docker

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Start the Server

```bash
cd server
python app.py
```

### 3. Access the Application

**Web Interface:** Open http://localhost:5000 in your browser

**Python Client:** Run the interactive client
```bash
cd client
python client.py
```

## 🔑 First Steps

### Using the Web Interface

1. **Sign Up**
   - Click on "Sign Up" tab
   - Enter username, email, and password
   - Click "Sign Up"
   - Check console output for verification code (in development mode)

2. **Verify Email**
   - Click on "Verify" tab
   - Enter your email and the 6-digit code
   - Click "Verify Email"

3. **Login**
   - Click on "Login" tab
   - Enter your username and password
   - Click "Login"

4. **Chat**
   - Click on "Chat" tab
   - Type a message and click "Send"
   - The server will echo your message back

### Using the Python Client

```bash
cd client
python client.py
```

Follow the interactive menu:
1. Select option 1 to Sign Up
2. Enter your credentials
3. Check the server console for verification code
4. Select option 2 to Verify Email
5. Select option 3 to Login
6. Select option 4 to Connect via Socket.IO
7. Select option 6 to Send Messages

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy the example
cp .env.example .env

# Edit with your settings
nano .env
```

### Email Configuration (Optional)

For production use with real email:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

**Note:** In development mode (without SMTP configuration), verification codes are printed to the server console.

## 🌐 SSH Tunnel Setup

To access the server through an SSH tunnel:

```bash
# Set environment variables
export SSH_HOST=your-server.com
export SSH_USER=username
export SSH_KEY_PATH=/path/to/ssh/key

# Start the tunnel
python config/ssh_tunnel.py
```

Then connect your client to `http://localhost:5000`

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/signup` | POST | Create new user |
| `/api/verify-email` | POST | Verify email with code |
| `/api/login` | POST | Login user |
| `/api/resend-verification` | POST | Resend verification code |

## 🧪 Testing

### Quick API Test

```bash
# Health check
curl http://localhost:5000/api/health

# Sign up
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# Check server logs for verification code, then verify
curl -X POST http://localhost:5000/api/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}'

# Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild images
docker-compose build

# Run client interactively
docker-compose run --rm client
```

## 🔐 Security Notes

- **Development Mode**: Verification codes are printed to console
- **Production Mode**: Configure SMTP to send real emails
- **Passwords**: Automatically hashed using Werkzeug
- **Database**: SQLite by default (configure DATABASE_URL for production)

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>
```

### Database Issues
```bash
# Remove database to start fresh
rm server/instance/auth.db
```

### Connection Issues
- Ensure server is running: `curl http://localhost:5000/api/health`
- Check firewall settings
- Verify correct port in configuration

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API endpoints
- Configure production email settings
- Set up SSH tunnels for remote access
- Deploy with Docker in production

## 🤝 Need Help?

- Check the [README.md](README.md) for detailed documentation
- Review API documentation
- Open an issue on GitHub

Happy coding! 🎉
