# Contributing to OEN-Project_MUx1

Thank you for your interest in contributing to the OEN-Project_MUx1 authentication system! This document provides guidelines and instructions for contributing.

## Before You Start

Please review the [Implementation Plan](IMPLEMENTATION_PLAN.md) to understand the project roadmap, current status, and planned features. This will help you identify areas where contributions are most needed.

## Getting Started

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/OEN-Project_MUx1.git
   cd OEN-Project_MUx1
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   ./start_server.sh
   ```

## Project Structure

```
├── server/              # Server application
│   ├── app.py          # Main Flask application
│   ├── email_service.py # Email verification service
│   └── static/         # Web interface files
├── client/             # Client application
│   └── client.py       # Python CLI client
├── config/             # Configuration utilities
│   └── ssh_tunnel.py   # SSH tunnel support
├── *.md                # Documentation
└── *.sh                # Startup scripts
```

## How to Contribute

### Reporting Bugs

When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages and stack traces

### Suggesting Features

Feature suggestions are welcome! Please:
- Check existing issues first
- Provide clear use case
- Explain expected behavior
- Consider implementation impact

### Pull Requests

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow coding standards
   - Add tests if applicable
   - Update documentation

3. **Test Your Changes**
   ```bash
   # Test the server
   cd server && python app.py
   
   # Test the client
   cd client && python client.py
   
   # Test API endpoints
   curl http://localhost:5000/api/health
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Python Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and concise

### Example:
```python
def send_verification_email(to_email: str, verification_code: str) -> bool:
    """
    Send verification email to user
    
    Args:
        to_email: Recipient email address
        verification_code: 6-digit verification code
        
    Returns:
        bool: True if email sent successfully
    """
    # Implementation
    pass
```

### JavaScript Style
- Use ES6+ features
- Use camelCase for variables
- Add comments for complex logic
- Keep functions small and focused

### HTML/CSS Style
- Use semantic HTML5 elements
- Keep styles in `<style>` tags or separate CSS files
- Use meaningful class names
- Ensure responsive design

## Testing

### Manual Testing Checklist

- [ ] Server starts without errors
- [ ] Web interface loads correctly
- [ ] Sign up creates new user
- [ ] Email verification works
- [ ] Login authenticates user
- [ ] Socket.IO connection establishes
- [ ] Client application works
- [ ] API endpoints return correct responses

### API Testing

```bash
# Health check
curl http://localhost:5000/api/health

# Sign up
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"pass123"}'

# Verify email (use code from console)
curl -X POST http://localhost:5000/api/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}'

# Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"pass123"}'
```

## Documentation

When making changes, update relevant documentation:
- README.md - Feature documentation
- QUICKSTART.md - Getting started guide
- ARCHITECTURE.md - System design docs
- Code comments - Inline documentation

## Areas for Contribution

### High Priority
- [ ] Unit tests for server endpoints
- [ ] Integration tests for auth flow
- [ ] Password reset functionality
- [ ] Two-factor authentication (2FA)
- [ ] Rate limiting for API endpoints
- [ ] CAPTCHA integration

### Medium Priority
- [ ] User profile management
- [ ] OAuth2 integration (Google, GitHub)
- [ ] Persistent sessions with tokens
- [ ] PostgreSQL support documentation
- [ ] Kubernetes deployment guide

### Nice to Have
- [ ] Mobile app client
- [ ] Desktop application
- [ ] Admin dashboard
- [ ] Usage analytics
- [ ] Internationalization (i18n)

## Code Review Process

All contributions go through code review:
1. Automated checks (if configured)
2. Manual review by maintainer
3. Feedback and iteration
4. Approval and merge

## Questions?

- Open an issue for questions
- Check existing documentation
- Review closed issues/PRs

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Code of Conduct

### Our Pledge
- Be respectful and inclusive
- Welcome newcomers
- Focus on what's best for the project
- Show empathy towards others

### Unacceptable Behavior
- Harassment or discrimination
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information

## Recognition

Contributors will be:
- Listed in git history
- Mentioned in release notes
- Credited in README (for significant contributions)

Thank you for contributing! 🎉
