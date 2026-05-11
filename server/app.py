from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from threading import Thread, Lock
import hashlib
import secrets
import os
import time
from datetime import datetime, timedelta
from email_service import send_verification_email

# Track connected sessions: {sid: {'user_id': id, 'username': str, 'connected_at': datetime}}
connected_sessions = {}

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///auth.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,   # Discard stale connections before use
    'pool_recycle': 3600,    # Recycle connections after 1 hour to avoid timeout drops
}

CORS(app)
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

_PBKDF2_ITERATIONS = 600000

def _hash_password(password: str) -> str:
    """Hash a password using PBKDF2-SHA256 with a random salt."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, _PBKDF2_ITERATIONS)
    return f'pbkdf2:sha256:{_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}'

def _verify_password(password_hash: str, password: str) -> bool:
    """Verify a password against a stored PBKDF2-SHA256 hash."""
    try:
        if password_hash.count('$') != 2:
            return False
        prefix, salt_hex, stored_hex = password_hash.split('$')
        _, algo, iterations_str = prefix.split(':')
        if algo != 'sha256':
            return False
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac(algo, password.encode('utf-8'), salt, iterations)
        return secrets.compare_digest(dk.hex(), stored_hex)
    except (ValueError, AttributeError):
        return False

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6))
    verification_code_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = _hash_password(password)

    def check_password(self, password):
        return _verify_password(self.password_hash, password)

    def generate_verification_code(self):
        self.verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.verification_code_expires = datetime.utcnow() + timedelta(hours=24)
        return self.verification_code


class Character(db.Model):
    """Character model - users can have multiple characters"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), default='')
    level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship back to user
    user = db.relationship('User', backref=db.backref('characters', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'level': self.level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


# Server start time for uptime tracking
SERVER_START_TIME = time.time()

# Simple time-based cache for the User count so we avoid a full table-scan on
# every Socket.IO connect, login request, and server_info command.
_user_count_cache = {'count': 0, 'expires_at': 0.0}
_user_count_lock = Lock()


def get_server_status():
    """Get current server status information"""
    uptime_seconds = int(time.time() - SERVER_START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    now = time.time()
    with _user_count_lock:
        if now >= _user_count_cache['expires_at']:
            _user_count_cache['count'] = User.query.count()
            _user_count_cache['expires_at'] = now + 60.0  # refresh every 60 seconds
        total_users = _user_count_cache['count']

    return {
        'uptime': f'{hours:02d}:{minutes:02d}:{seconds:02d}',
        'uptime_seconds': uptime_seconds,
        'connected_users': len(connected_sessions),
        'total_users': total_users,
        'status': 'online'
    }


def authenticate_request_user():
    """Authenticate a request using HTTP Basic auth"""
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return None, (jsonify({'error': 'Authentication required'}), 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    
    user = User.query.filter_by(username=auth.username).first()
    if not user or not user.check_password(auth.password):
        return None, (jsonify({'error': 'Invalid credentials'}), 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    
    if not user.is_verified:
        return None, (jsonify({'error': 'Email not verified. Please verify your email first.'}), 403)
    
    return user, None


# Serve web interface
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# Serve terminal interface
@app.route('/terminal')
def terminal():
    return send_from_directory('static', 'terminal.html')

# REST API Endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Server is running'})

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists (single query instead of two)
    existing = User.query.filter(
        or_(User.username == data['username'], User.email == data['email'])
    ).first()
    if existing:
        if existing.username == data['username']:
            return jsonify({'error': 'Username already exists'}), 400
        return jsonify({'error': 'Email already registered'}), 400
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    verification_code = user.generate_verification_code()
    
    db.session.add(user)
    db.session.commit()
    
    # Send verification email in a background thread so SMTP latency doesn't
    # block the HTTP response. Non-daemon so an in-flight email isn't lost if
    # the server shuts down immediately after responding.
    Thread(
        target=send_verification_email,
        args=(user.email, verification_code),
        daemon=False
    ).start()
    
    return jsonify({
        'message': 'User created successfully. Please check your email for verification code.',
        'user_id': user.id
    }), 201

@app.route('/api/verify-email', methods=['POST'])
def verify_email():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('code'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.is_verified:
        return jsonify({'message': 'Email already verified'}), 200
    
    if not user.verification_code or user.verification_code != data['code']:
        return jsonify({'error': 'Invalid verification code'}), 400
    
    if user.verification_code_expires < datetime.utcnow():
        return jsonify({'error': 'Verification code expired'}), 400
    
    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires = None
    db.session.commit()
    
    return jsonify({'message': 'Email verified successfully'}), 200

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    user = User.query.options(joinedload(User.characters)).filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    if not user.is_verified:
        return jsonify({'error': 'Email not verified. Please verify your email first.'}), 403
    
    # Get user's characters
    characters = [char.to_dict() for char in user.characters if char.is_active]
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'characters': characters,
        'server_status': get_server_status()
    }), 200


@app.route('/api/server-status', methods=['GET'])
def server_status():
    """Get server status - ping endpoint with detailed info"""
    return jsonify(get_server_status()), 200


@app.route('/api/characters', methods=['GET'])
def get_characters():
    """Get characters for the authenticated user"""
    user, error_response = authenticate_request_user()
    if error_response:
        return error_response
    
    characters = Character.query.filter_by(user_id=user.id, is_active=True).all()
    return jsonify({'characters': [char.to_dict() for char in characters]}), 200


@app.route('/api/characters', methods=['POST'])
def create_character():
    """Create a new character for the authenticated user"""
    user, error_response = authenticate_request_user()
    if error_response:
        return error_response
    
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Missing required fields (name)'}), 400
    
    # Check if character name is taken
    if Character.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Character name already taken'}), 400
    
    character = Character(
        user_id=user.id,
        name=data['name'],
        description=data.get('description', '')
    )
    
    db.session.add(character)
    db.session.commit()
    
    return jsonify({
        'message': 'Character created successfully',
        'character': character.to_dict()
    }), 201

@app.route('/api/resend-verification', methods=['POST'])
def resend_verification():
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.is_verified:
        return jsonify({'message': 'Email already verified'}), 200
    
    verification_code = user.generate_verification_code()
    db.session.commit()
    
    Thread(
        target=send_verification_email,
        args=(user.email, verification_code),
        daemon=False
    ).start()
    
    return jsonify({'message': 'Verification code sent'}), 200

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    # Add to connected sessions as anonymous until authenticated
    connected_sessions[request.sid] = {
        'user_id': None,
        'username': 'guest',
        'connected_at': datetime.utcnow()
    }
    emit('connected', {
        'message': 'Connected to server',
        'sid': request.sid,
        'server_status': get_server_status()
    })

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    # Remove from connected sessions
    if request.sid in connected_sessions:
        del connected_sessions[request.sid]

@socketio.on('authenticate')
def handle_authenticate(data):
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        emit('auth_error', {'error': 'Missing credentials'})
        return
    
    user = User.query.options(joinedload(User.characters)).filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        emit('auth_error', {'error': 'Invalid credentials'})
        return
    
    if not user.is_verified:
        emit('auth_error', {'error': 'Email not verified'})
        return
    
    # Update connected session with user info
    connected_sessions[request.sid] = {
        'user_id': user.id,
        'username': user.username,
        'connected_at': datetime.utcnow()
    }
    
    # Get user's characters
    characters = [char.to_dict() for char in user.characters if char.is_active]
    
    emit('auth_success', {
        'message': 'Authentication successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'characters': characters,
        'server_status': get_server_status()
    })

@socketio.on('message')
def handle_message(data):
    print(f"Received message: {data}")
    emit('message', {'echo': data}, broadcast=False)

# Terminal command handler - processes text commands from terminal UI
@socketio.on('command')
def handle_command(data):
    """Handle commands from terminal interface"""
    cmd = data.get('cmd', '').lower()
    args = data.get('args', [])
    
    response = {'output': [], 'error': None}
    
    if cmd == 'who':
        # List connected users
        response['output'] = [
            '',
            '\x1b[33m╔════════════════════════════════════════╗\x1b[0m',
            '\x1b[33m║\x1b[0m         \x1b[1mCONNECTED USERS\x1b[0m              \x1b[33m║\x1b[0m',
            '\x1b[33m╠════════════════════════════════════════╣\x1b[0m'
        ]
        
        if connected_sessions:
            for sid, session in connected_sessions.items():
                username = session.get('username', 'guest')
                connected_at = session.get('connected_at')
                if connected_at:
                    duration = datetime.utcnow() - connected_at
                    mins = int(duration.total_seconds() // 60)
                    time_str = f'{mins}m' if mins > 0 else '<1m'
                else:
                    time_str = '?'
                
                # Mark current user
                marker = ' \x1b[32m<- you\x1b[0m' if sid == request.sid else ''
                response['output'].append(
                    f'\x1b[33m║\x1b[0m  \x1b[36m{username:<20}\x1b[0m ({time_str}){marker}'
                )
        else:
            response['output'].append('\x1b[33m║\x1b[0m  No users connected')
        
        response['output'].extend([
            '\x1b[33m╚════════════════════════════════════════╝\x1b[0m',
            f'  Total: {len(connected_sessions)} user(s) online',
            ''
        ])
        
    elif cmd == 'server_info':
        status = get_server_status()
        response['output'] = [
            '',
            '\x1b[33m╔════════════════════════════════════════╗\x1b[0m',
            '\x1b[33m║\x1b[0m        \x1b[1mSERVER INFORMATION\x1b[0m            \x1b[33m║\x1b[0m',
            '\x1b[33m╠════════════════════════════════════════╣\x1b[0m',
            f'\x1b[33m║\x1b[0m  Status:     \x1b[32m{status["status"].upper():<24}\x1b[0m\x1b[33m║\x1b[0m',
            f'\x1b[33m║\x1b[0m  Uptime:     {status["uptime"]:<24}\x1b[33m║\x1b[0m',
            f'\x1b[33m║\x1b[0m  Online:     {status["connected_users"]} user(s){" " * 17}\x1b[33m║\x1b[0m',
            f'\x1b[33m║\x1b[0m  Registered: {status["total_users"]} user(s){" " * 17}\x1b[33m║\x1b[0m',
            '\x1b[33m╚════════════════════════════════════════╝\x1b[0m',
            ''
        ]
    
    elif cmd == 'characters':
        # Get current user's characters
        session = connected_sessions.get(request.sid, {})
        user_id = session.get('user_id')
        
        if not user_id:
            response['error'] = 'You must be logged in to view characters.'
        else:
            characters = Character.query.filter_by(user_id=user_id, is_active=True).all()
            response['output'] = [
                '',
                '\x1b[33m╔════════════════════════════════════════╗\x1b[0m',
                '\x1b[33m║\x1b[0m          \x1b[1mYOUR CHARACTERS\x1b[0m             \x1b[33m║\x1b[0m',
                '\x1b[33m╠════════════════════════════════════════╣\x1b[0m'
            ]
            
            if characters:
                for char in characters:
                    response['output'].append(
                        f'\x1b[33m║\x1b[0m  \x1b[36m{char.name:<15}\x1b[0m Lv.{char.level:<3} {char.description[:15]}'
                    )
            else:
                response['output'].append('\x1b[33m║\x1b[0m  No characters yet. Use \x1b[36mcreate <name>\x1b[0m')
            
            response['output'].extend([
                '\x1b[33m╚════════════════════════════════════════╝\x1b[0m',
                ''
            ])
    
    elif cmd == 'create' and args:
        # Create a new character
        session = connected_sessions.get(request.sid, {})
        user_id = session.get('user_id')
        
        if not user_id:
            response['error'] = 'You must be logged in to create a character.'
        else:
            char_name = args[0]
            description = ' '.join(args[1:]) if len(args) > 1 else ''
            
            # Check if name is taken
            if Character.query.filter_by(name=char_name).first():
                response['error'] = f'Character name "{char_name}" is already taken.'
            else:
                character = Character(
                    user_id=user_id,
                    name=char_name,
                    description=description
                )
                db.session.add(character)
                db.session.commit()
                
                response['output'] = [
                    '',
                    f'\x1b[32m✓ Character "{char_name}" created successfully!\x1b[0m',
                    ''
                ]
    else:
        response['error'] = f'Unknown server command: {cmd}'
    
    emit('cmd_response', response)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
