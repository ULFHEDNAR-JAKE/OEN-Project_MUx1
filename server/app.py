from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
import secrets
import os
import re
import logging
from datetime import datetime, timedelta
from email_service import send_verification_email
import jwt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///auth.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CORS Configuration - restrict origins in production
allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5000').split(',')
if app.debug:
    # Development mode - allow localhost
    allowed_origins = ['http://localhost:3000', 'http://localhost:5000', 'http://127.0.0.1:3000', 'http://127.0.0.1:5000']

CORS(app, origins=allowed_origins, supports_credentials=True)

db = SQLAlchemy(app)

# Socket.IO with restricted CORS
socketio = SocketIO(app, cors_allowed_origins=allowed_origins)

# Rate Limiter Configuration
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Constants
VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_EXPIRY_HOURS = 24
JWT_EXPIRY_HOURS = 24

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(255))  # Hashed verification code
    verification_code_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_verification_code(self):
        """Generate and hash verification code"""
        code = ''.join([str(secrets.randbelow(10)) for _ in range(VERIFICATION_CODE_LENGTH)])
        self.verification_code = generate_password_hash(code)
        self.verification_code_expires = datetime.utcnow() + timedelta(hours=VERIFICATION_CODE_EXPIRY_HOURS)
        return code  # Return unhashed for email
    
    def verify_code(self, code):
        """Verify hashed verification code"""
        if not self.verification_code:
            return False
        return check_password_hash(self.verification_code, code)
    
    def is_locked(self):
        """Check if account is locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def increment_failed_attempts(self):
        """Increment failed login attempts and lock if needed"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            # Lock account for 15 minutes
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
            logger.warning(f"Account locked for user: {self.username}")
    
    def reset_failed_attempts(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
        self.locked_until = None

# Validation Functions
def validate_email_format(email):
    """Validate email format"""
    try:
        # Validate email
        valid = validate_email(email)
        return True, valid.email
    except EmailNotValidError as e:
        return False, str(e)

def validate_username(username):
    """Validate username (alphanumeric and underscore, 3-20 chars)"""
    if not username or not isinstance(username, str):
        return False, "Username is required"
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return False, "Username must be 3-20 alphanumeric characters or underscores"
    return True, username

def validate_password_strength(password):
    """Validate password strength"""
    if not password or not isinstance(password, str):
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, password

def generate_jwt_token(user_id, username):
    """Generate JWT token for authenticated user"""
    try:
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        return token
    except Exception as e:
        logger.error(f"Error generating JWT token: {str(e)}")
        return None

# Security Headers Middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if not app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Content-Type Validation Middleware
@app.before_request
def validate_content_type():
    """Validate Content-Type for POST requests"""
    if request.method == 'POST' and request.path.startswith('/api/'):
        if request.content_type and 'application/json' not in request.content_type:
            return jsonify({'error': 'Content-Type must be application/json'}), 415

# Serve web interface
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# REST API Endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with database connectivity test"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = 'unhealthy'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'message': 'Server is running',
        'database': db_status
    })

@app.route('/api/signup', methods=['POST'])
@limiter.limit("3 per hour")
def signup():
    """Register a new user with validation and rate limiting"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validate required fields
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({'error': 'Missing required fields: username, email, password'}), 400
        
        # Validate username
        valid, result = validate_username(username)
        if not valid:
            logger.warning(f"Signup failed - invalid username: {result}")
            return jsonify({'error': result}), 400
        username = result
        
        # Validate email
        valid, result = validate_email_format(email)
        if not valid:
            logger.warning(f"Signup failed - invalid email: {result}")
            return jsonify({'error': f'Invalid email format: {result}'}), 400
        email = result
        
        # Validate password
        valid, result = validate_password_strength(password)
        if not valid:
            logger.warning(f"Signup failed - weak password")
            return jsonify({'error': result}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            logger.warning(f"Signup failed - username already exists: {username}")
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            logger.warning(f"Signup failed - email already registered: {email}")
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        user = User(
            username=username,
            email=email
        )
        user.set_password(password)
        verification_code = user.generate_verification_code()
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        send_verification_email(user.email, verification_code)
        
        logger.info(f"New user registered: {username}")
        
        return jsonify({
            'message': 'User created successfully. Please check your email for verification code.',
            'user_id': user.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Signup error: {str(e)}")
        return jsonify({'error': 'An error occurred during signup'}), 500

@app.route('/api/verify-email', methods=['POST'])
@limiter.limit("10 per hour")
def verify_email():
    """Verify email with hashed verification code"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({'error': 'Missing required fields: email, code'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.warning(f"Email verification failed - user not found: {email}")
            return jsonify({'error': 'User not found'}), 404
        
        if user.is_verified:
            return jsonify({'message': 'Email already verified'}), 200
        
        if not user.verification_code:
            logger.warning(f"Email verification failed - no code set: {email}")
            return jsonify({'error': 'No verification code found. Please request a new one.'}), 400
        
        if user.verification_code_expires < datetime.utcnow():
            logger.warning(f"Email verification failed - code expired: {email}")
            return jsonify({'error': 'Verification code expired. Please request a new one.'}), 400
        
        if not user.verify_code(code):
            logger.warning(f"Email verification failed - invalid code: {email}")
            return jsonify({'error': 'Invalid verification code'}), 400
        
        user.is_verified = True
        user.verification_code = None
        user.verification_code_expires = None
        db.session.commit()
        
        logger.info(f"Email verified successfully: {email}")
        
        return jsonify({'message': 'Email verified successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Email verification error: {str(e)}")
        return jsonify({'error': 'An error occurred during verification'}), 500

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Login with account lockout protection and JWT token"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Missing required fields: username, password'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            logger.warning(f"Login failed - user not found: {username}")
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Check if account is locked
        if user.is_locked():
            logger.warning(f"Login failed - account locked: {username}")
            return jsonify({'error': 'Account is temporarily locked due to multiple failed login attempts. Please try again later.'}), 403
        
        if not user.check_password(password):
            user.increment_failed_attempts()
            db.session.commit()
            logger.warning(f"Login failed - invalid password for user: {username} (attempt {user.failed_login_attempts})")
            return jsonify({'error': 'Invalid username or password'}), 401
        
        if not user.is_verified:
            logger.warning(f"Login failed - email not verified: {username}")
            return jsonify({'error': 'Email not verified. Please verify your email first.'}), 403
        
        # Reset failed attempts on successful login
        user.reset_failed_attempts()
        db.session.commit()
        
        # Generate JWT token
        token = generate_jwt_token(user.id, user.username)
        
        logger.info(f"Successful login: {username}")
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'An error occurred during login'}), 500

@app.route('/api/resend-verification', methods=['POST'])
@limiter.limit("3 per hour")
def resend_verification():
    """Resend verification code with rate limiting"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.warning(f"Resend verification failed - user not found: {email}")
            return jsonify({'error': 'User not found'}), 404
        
        if user.is_verified:
            return jsonify({'message': 'Email already verified'}), 200
        
        verification_code = user.generate_verification_code()
        db.session.commit()
        
        send_verification_email(user.email, verification_code)
        
        logger.info(f"Verification code resent: {email}")
        
        return jsonify({'message': 'Verification code sent'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Resend verification error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    """Handle Socket.IO connection"""
    try:
        logger.info(f'Client connected: {request.sid}')
        emit('connected', {'message': 'Connected to server', 'sid': request.sid})
    except Exception as e:
        logger.error(f"Socket.IO connect error: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle Socket.IO disconnection"""
    try:
        logger.info(f'Client disconnected: {request.sid}')
    except Exception as e:
        logger.error(f"Socket.IO disconnect error: {str(e)}")

@socketio.on('authenticate')
def handle_authenticate(data):
    """Authenticate user via Socket.IO"""
    try:
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            emit('auth_error', {'error': 'Missing credentials'})
            return
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            logger.warning(f"Socket.IO auth failed - user not found: {username}")
            emit('auth_error', {'error': 'Invalid credentials'})
            return
        
        # Check if account is locked
        if user.is_locked():
            logger.warning(f"Socket.IO auth failed - account locked: {username}")
            emit('auth_error', {'error': 'Account is temporarily locked'})
            return
        
        if not user.check_password(password):
            user.increment_failed_attempts()
            db.session.commit()
            logger.warning(f"Socket.IO auth failed - invalid password: {username}")
            emit('auth_error', {'error': 'Invalid credentials'})
            return
        
        if not user.is_verified:
            logger.warning(f"Socket.IO auth failed - email not verified: {username}")
            emit('auth_error', {'error': 'Email not verified'})
            return
        
        # Reset failed attempts on successful auth
        user.reset_failed_attempts()
        db.session.commit()
        
        logger.info(f"Socket.IO authentication successful: {username}")
        
        emit('auth_success', {
            'message': 'Authentication successful',
            'user': {
                'id': user.id,
                'username': user.username
            }
        })
    
    except Exception as e:
        logger.error(f"Socket.IO auth error: {str(e)}")
        emit('auth_error', {'error': 'Authentication failed'})

@socketio.on('message')
def handle_message(data):
    """Handle Socket.IO message"""
    try:
        logger.info(f"Received message: {data}")
        emit('message', {'echo': data}, broadcast=False)
    except Exception as e:
        logger.error(f"Socket.IO message error: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"Starting server on {host}:{port} (debug={debug_mode})")
    socketio.run(app, host=host, port=port, debug=debug_mode)
