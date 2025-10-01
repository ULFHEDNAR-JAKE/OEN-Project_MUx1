import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_verification_email(to_email, verification_code):
    """
    Send verification email to user
    """
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_username = os.environ.get('SMTP_USERNAME', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    from_email = os.environ.get('FROM_EMAIL', smtp_username)
    
    # If SMTP is not configured, print to console (dev mode)
    if not smtp_username or not smtp_password:
        print(f"\n{'='*50}")
        print(f"VERIFICATION EMAIL (Development Mode)")
        print(f"To: {to_email}")
        print(f"Verification Code: {verification_code}")
        print(f"{'='*50}\n")
        return True
    
    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = 'Email Verification Code'
        message['From'] = from_email
        message['To'] = to_email
        
        # Create email body
        text = f"""
        Welcome!
        
        Your verification code is: {verification_code}
        
        This code will expire in 24 hours.
        
        If you did not request this code, please ignore this email.
        """
        
        html = f"""
        <html>
          <body>
            <h2>Welcome!</h2>
            <p>Your verification code is: <strong>{verification_code}</strong></p>
            <p>This code will expire in 24 hours.</p>
            <p><em>If you did not request this code, please ignore this email.</em></p>
          </body>
        </html>
        """
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        
        print(f"Verification email sent to {to_email}")
        return True
    
    except Exception as e:
        print(f"Error sending email: {e}")
        # In development, still print the code
        print(f"\n{'='*50}")
        print(f"VERIFICATION EMAIL (Fallback)")
        print(f"To: {to_email}")
        print(f"Verification Code: {verification_code}")
        print(f"{'='*50}\n")
        return False
