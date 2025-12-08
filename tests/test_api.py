"""
Unit tests for the authentication system
"""
import pytest
import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from app import app, db, User, validate_email_format, validate_username, validate_password_strength


@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


class TestValidation:
    """Test input validation functions"""
    
    def test_validate_email_valid(self):
        """Test email validation with valid email"""
        valid, result = validate_email_format('test@example.com')
        assert valid is True
        assert result == 'test@example.com'
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid email"""
        valid, result = validate_email_format('invalid-email')
        assert valid is False
    
    def test_validate_username_valid(self):
        """Test username validation with valid username"""
        valid, result = validate_username('testuser123')
        assert valid is True
        assert result == 'testuser123'
    
    def test_validate_username_too_short(self):
        """Test username validation with too short username"""
        valid, result = validate_username('ab')
        assert valid is False
        assert 'must be 3-20' in result
    
    def test_validate_username_too_long(self):
        """Test username validation with too long username"""
        valid, result = validate_username('a' * 21)
        assert valid is False
    
    def test_validate_username_invalid_chars(self):
        """Test username validation with invalid characters"""
        valid, result = validate_username('test@user')
        assert valid is False
    
    def test_validate_password_valid(self):
        """Test password validation with valid password"""
        valid, result = validate_password_strength('TestPass123')
        assert valid is True
    
    def test_validate_password_too_short(self):
        """Test password validation with too short password"""
        valid, result = validate_password_strength('Test1')
        assert valid is False
        assert 'at least 8 characters' in result
    
    def test_validate_password_no_uppercase(self):
        """Test password validation without uppercase"""
        valid, result = validate_password_strength('testpass123')
        assert valid is False
        assert 'uppercase' in result
    
    def test_validate_password_no_lowercase(self):
        """Test password validation without lowercase"""
        valid, result = validate_password_strength('TESTPASS123')
        assert valid is False
        assert 'lowercase' in result
    
    def test_validate_password_no_number(self):
        """Test password validation without number"""
        valid, result = validate_password_strength('TestPassword')
        assert valid is False
        assert 'number' in result


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check returns healthy status"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert data['database'] == 'healthy'


class TestSignupEndpoint:
    """Test signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful user signup"""
        response = client.post('/api/signup', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert 'user_id' in data
        assert 'message' in data
    
    def test_signup_missing_fields(self, client):
        """Test signup with missing fields"""
        response = client.post('/api/signup', json={
            'username': 'testuser'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_signup_invalid_email(self, client):
        """Test signup with invalid email"""
        response = client.post('/api/signup', json={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'TestPass123'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'email' in data['error'].lower()
    
    def test_signup_weak_password(self, client):
        """Test signup with weak password"""
        response = client.post('/api/signup', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'weak'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'password' in data['error'].lower()
    
    def test_signup_duplicate_username(self, client):
        """Test signup with duplicate username"""
        # Create first user
        client.post('/api/signup', json={
            'username': 'testuser',
            'email': 'test1@example.com',
            'password': 'TestPass123'
        })
        
        # Try to create with same username
        response = client.post('/api/signup', json={
            'username': 'testuser',
            'email': 'test2@example.com',
            'password': 'TestPass123'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'already exists' in data['error']


class TestLoginEndpoint:
    """Test login endpoint"""
    
    def test_login_unverified_user(self, client):
        """Test login with unverified email"""
        # Create user
        client.post('/api/signup', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123'
        })
        
        # Try to login
        response = client.post('/api/login', json={
            'username': 'testuser',
            'password': 'TestPass123'
        })
        assert response.status_code == 403
        data = response.get_json()
        assert 'not verified' in data['error'].lower()
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/api/login', json={
            'username': 'nonexistent',
            'password': 'WrongPass123'
        })
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data


class TestUserModel:
    """Test User model methods"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        user = User(username='test', email='test@example.com')
        user.set_password('TestPass123')
        
        assert user.password_hash is not None
        assert user.password_hash != 'TestPass123'
        assert user.check_password('TestPass123') is True
        assert user.check_password('WrongPass') is False
    
    def test_verification_code_generation(self):
        """Test verification code generation"""
        user = User(username='test', email='test@example.com')
        code = user.generate_verification_code()
        
        assert len(code) == 6
        assert code.isdigit()
        assert user.verification_code is not None
        assert user.verification_code_expires is not None
    
    def test_verification_code_hashing(self):
        """Test that verification codes are hashed"""
        user = User(username='test', email='test@example.com')
        code = user.generate_verification_code()
        
        # Verification code should be hashed
        assert user.verification_code != code
        # Should be able to verify with original code
        assert user.verify_code(code) is True
        assert user.verify_code('000000') is False
    
    def test_account_lockout(self):
        """Test account lockout mechanism"""
        user = User(username='test', email='test@example.com')
        
        # Account should not be locked initially
        assert user.is_locked() is False
        
        # Increment failed attempts
        for _ in range(5):
            user.increment_failed_attempts()
        
        # Account should be locked after 5 attempts
        assert user.is_locked() is True
        
        # Reset should unlock
        user.reset_failed_attempts()
        assert user.is_locked() is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
