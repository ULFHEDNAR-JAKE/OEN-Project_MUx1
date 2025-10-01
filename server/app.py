from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import os
from datetime import datetime, timedelta
from email_service import send_verification_email

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///auth.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

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
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_verification_code(self):
        self.verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.verification_code_expires = datetime.utcnow() + timedelta(hours=24)
        return self.verification_code

# Serve web interface
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# REST API Endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Server is running'})

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
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
    
    # Send verification email
    send_verification_email(user.email, verification_code)
    
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
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    if not user.is_verified:
        return jsonify({'error': 'Email not verified. Please verify your email first.'}), 403
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200

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
    
    send_verification_email(user.email, verification_code)
    
    return jsonify({'message': 'Verification code sent'}), 200

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('connected', {'message': 'Connected to server', 'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('authenticate')
def handle_authenticate(data):
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        emit('auth_error', {'error': 'Missing credentials'})
        return
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        emit('auth_error', {'error': 'Invalid credentials'})
        return
    
    if not user.is_verified:
        emit('auth_error', {'error': 'Email not verified'})
        return
    
    emit('auth_success', {
        'message': 'Authentication successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    })

@socketio.on('message')
def handle_message(data):
    print(f"Received message: {data}")
    emit('message', {'echo': data}, broadcast=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
