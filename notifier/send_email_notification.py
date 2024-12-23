import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailSender:
    def __init__(self, sender_email: str, receiver_email: str, smtp_server: str, smtp_port: int, password: str):
        self.sender_email = sender_email
        self.receiver_email = receiver_email
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.password = password

    def send_email(self, subject: str, body: str):
        "Send email using mime text"
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = self.receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.send_message(message)
            print("Email sent successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")
