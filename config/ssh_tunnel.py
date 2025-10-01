"""
SSH Tunnel Configuration for Client-Server Communication

This module provides utilities to establish SSH tunnels for secure
communication between client and server applications.
"""

import subprocess
import os
import time
from typing import Optional

class SSHTunnel:
    def __init__(
        self,
        ssh_host: str,
        ssh_port: int = 22,
        ssh_user: str = None,
        local_port: int = 5000,
        remote_port: int = 5000,
        ssh_key_path: Optional[str] = None
    ):
        """
        Initialize SSH Tunnel configuration
        
        Args:
            ssh_host: SSH server hostname or IP
            ssh_port: SSH server port (default: 22)
            ssh_user: SSH username
            local_port: Local port to forward (default: 5000)
            remote_port: Remote port on SSH server (default: 5000)
            ssh_key_path: Path to SSH private key (optional)
        """
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user or os.environ.get('SSH_USER', 'root')
        self.local_port = local_port
        self.remote_port = remote_port
        self.ssh_key_path = ssh_key_path or os.environ.get('SSH_KEY_PATH')
        self.tunnel_process = None
    
    def start_tunnel(self) -> bool:
        """
        Start SSH tunnel using subprocess
        
        Returns:
            bool: True if tunnel started successfully, False otherwise
        """
        try:
            # Build SSH command
            ssh_cmd = [
                'ssh',
                '-N',  # Don't execute remote command
                '-L', f'{self.local_port}:localhost:{self.remote_port}',  # Local port forwarding
                '-p', str(self.ssh_port),
            ]
            
            # Add SSH key if provided
            if self.ssh_key_path and os.path.exists(self.ssh_key_path):
                ssh_cmd.extend(['-i', self.ssh_key_path])
            
            # Add user@host
            ssh_cmd.append(f'{self.ssh_user}@{self.ssh_host}')
            
            print(f"Starting SSH tunnel: {' '.join(ssh_cmd)}")
            
            # Start tunnel process
            self.tunnel_process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it a moment to establish connection
            time.sleep(2)
            
            # Check if process is still running
            if self.tunnel_process.poll() is None:
                print(f"✓ SSH tunnel established on localhost:{self.local_port}")
                return True
            else:
                stderr = self.tunnel_process.stderr.read().decode()
                print(f"✗ SSH tunnel failed: {stderr}")
                return False
        
        except Exception as e:
            print(f"✗ Error starting SSH tunnel: {e}")
            return False
    
    def stop_tunnel(self):
        """Stop the SSH tunnel"""
        if self.tunnel_process and self.tunnel_process.poll() is None:
            self.tunnel_process.terminate()
            self.tunnel_process.wait()
            print("✓ SSH tunnel stopped")
    
    def is_active(self) -> bool:
        """Check if tunnel is active"""
        return self.tunnel_process is not None and self.tunnel_process.poll() is None


def create_tunnel_from_env() -> Optional[SSHTunnel]:
    """
    Create SSH tunnel from environment variables
    
    Environment variables:
        SSH_HOST: SSH server hostname
        SSH_PORT: SSH server port (default: 22)
        SSH_USER: SSH username
        SSH_KEY_PATH: Path to SSH private key
        LOCAL_PORT: Local port to forward (default: 5000)
        REMOTE_PORT: Remote port (default: 5000)
    
    Returns:
        SSHTunnel instance or None if required vars not set
    """
    ssh_host = os.environ.get('SSH_HOST')
    
    if not ssh_host:
        return None
    
    return SSHTunnel(
        ssh_host=ssh_host,
        ssh_port=int(os.environ.get('SSH_PORT', 22)),
        ssh_user=os.environ.get('SSH_USER'),
        local_port=int(os.environ.get('LOCAL_PORT', 5000)),
        remote_port=int(os.environ.get('REMOTE_PORT', 5000)),
        ssh_key_path=os.environ.get('SSH_KEY_PATH')
    )


if __name__ == '__main__':
    # Example usage
    print("SSH Tunnel Configuration Example")
    print("=" * 50)
    
    tunnel = create_tunnel_from_env()
    
    if tunnel:
        print("\nStarting tunnel...")
        if tunnel.start_tunnel():
            print("\nTunnel is active. Press Ctrl+C to stop.")
            try:
                # Keep the tunnel alive
                while tunnel.is_active():
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping tunnel...")
                tunnel.stop_tunnel()
    else:
        print("SSH_HOST environment variable not set.")
        print("\nExample usage:")
        print("  export SSH_HOST=your-server.com")
        print("  export SSH_USER=username")
        print("  export SSH_KEY_PATH=/path/to/key")
        print("  python ssh_tunnel.py")
