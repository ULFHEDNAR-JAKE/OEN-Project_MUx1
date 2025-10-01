import socketio
import requests
import os
import getpass
from typing import Optional

class AuthClient:
    def __init__(self, server_url: str = None):
        self.server_url = server_url or os.environ.get('SERVER_URL', 'http://localhost:5000')
        self.api_url = f"{self.server_url}/api"
        self.sio = socketio.Client()
        self.authenticated = False
        self.current_user = None
        
        # Setup Socket.IO event handlers
        self.setup_socketio_handlers()
    
    def setup_socketio_handlers(self):
        @self.sio.on('connected')
        def on_connected(data):
            print(f"✓ Connected to server: {data.get('message')}")
        
        @self.sio.on('auth_success')
        def on_auth_success(data):
            self.authenticated = True
            self.current_user = data.get('user')
            print(f"✓ Authentication successful! Welcome, {self.current_user['username']}")
        
        @self.sio.on('auth_error')
        def on_auth_error(data):
            print(f"✗ Authentication error: {data.get('error')}")
        
        @self.sio.on('message')
        def on_message(data):
            print(f"Message from server: {data}")
    
    def connect(self):
        """Connect to the server via Socket.IO"""
        try:
            print(f"Connecting to {self.server_url}...")
            self.sio.connect(self.server_url)
            return True
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        if self.sio.connected:
            self.sio.disconnect()
            print("Disconnected from server")
    
    def signup(self, username: str, email: str, password: str) -> bool:
        """Sign up a new user"""
        try:
            response = requests.post(
                f"{self.api_url}/signup",
                json={
                    'username': username,
                    'email': email,
                    'password': password
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                print(f"✓ {data['message']}")
                return True
            else:
                error = response.json().get('error', 'Unknown error')
                print(f"✗ Signup failed: {error}")
                return False
        
        except Exception as e:
            print(f"✗ Signup error: {e}")
            return False
    
    def verify_email(self, email: str, code: str) -> bool:
        """Verify email with the provided code"""
        try:
            response = requests.post(
                f"{self.api_url}/verify-email",
                json={
                    'email': email,
                    'code': code
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {data['message']}")
                return True
            else:
                error = response.json().get('error', 'Unknown error')
                print(f"✗ Verification failed: {error}")
                return False
        
        except Exception as e:
            print(f"✗ Verification error: {e}")
            return False
    
    def login_http(self, username: str, password: str) -> bool:
        """Login via HTTP API"""
        try:
            response = requests.post(
                f"{self.api_url}/login",
                json={
                    'username': username,
                    'password': password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_user = data['user']
                print(f"✓ {data['message']}")
                print(f"Welcome, {self.current_user['username']}!")
                return True
            else:
                error = response.json().get('error', 'Unknown error')
                print(f"✗ Login failed: {error}")
                return False
        
        except Exception as e:
            print(f"✗ Login error: {e}")
            return False
    
    def authenticate_socketio(self, username: str, password: str):
        """Authenticate via Socket.IO"""
        if not self.sio.connected:
            print("✗ Not connected to server. Please connect first.")
            return False
        
        self.sio.emit('authenticate', {
            'username': username,
            'password': password
        })
        return True
    
    def send_message(self, message: str):
        """Send a message via Socket.IO"""
        if not self.sio.connected:
            print("✗ Not connected to server")
            return False
        
        self.sio.emit('message', message)
        return True
    
    def resend_verification(self, email: str) -> bool:
        """Resend verification code"""
        try:
            response = requests.post(
                f"{self.api_url}/resend-verification",
                json={'email': email}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {data['message']}")
                return True
            else:
                error = response.json().get('error', 'Unknown error')
                print(f"✗ Failed: {error}")
                return False
        
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

def interactive_menu():
    """Interactive menu for the client"""
    client = AuthClient()
    
    print("=" * 50)
    print("Authentication Client")
    print("=" * 50)
    
    while True:
        print("\nMenu:")
        print("1. Sign Up")
        print("2. Verify Email")
        print("3. Login (HTTP)")
        print("4. Connect via Socket.IO")
        print("5. Authenticate via Socket.IO")
        print("6. Send Message via Socket.IO")
        print("7. Resend Verification Code")
        print("8. Exit")
        
        choice = input("\nSelect an option: ").strip()
        
        if choice == '1':
            print("\n--- Sign Up ---")
            username = input("Username: ").strip()
            email = input("Email: ").strip()
            password = getpass.getpass("Password: ")
            client.signup(username, email, password)
        
        elif choice == '2':
            print("\n--- Verify Email ---")
            email = input("Email: ").strip()
            code = input("Verification Code: ").strip()
            client.verify_email(email, code)
        
        elif choice == '3':
            print("\n--- Login ---")
            username = input("Username: ").strip()
            password = getpass.getpass("Password: ")
            client.login_http(username, password)
        
        elif choice == '4':
            print("\n--- Connect Socket.IO ---")
            client.connect()
        
        elif choice == '5':
            print("\n--- Authenticate Socket.IO ---")
            username = input("Username: ").strip()
            password = getpass.getpass("Password: ")
            client.authenticate_socketio(username, password)
        
        elif choice == '6':
            print("\n--- Send Message ---")
            message = input("Message: ").strip()
            client.send_message(message)
        
        elif choice == '7':
            print("\n--- Resend Verification Code ---")
            email = input("Email: ").strip()
            client.resend_verification(email)
        
        elif choice == '8':
            print("\nExiting...")
            client.disconnect()
            break
        
        else:
            print("Invalid option. Please try again.")

if __name__ == '__main__':
    interactive_menu()
