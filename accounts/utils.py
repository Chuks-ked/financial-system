from django.core.mail import send_mail
from threading import Thread

class EmailThread(Thread):
    def __init__(self, subject, message, recipient_list):
        self.subject = subject
        self.message = message
        self.recipient_list = recipient_list
        super().__init__()

    def run(self):
        send_mail(
            subject=self.subject,
            message=self.message,
            from_email="noreply@financialsystem.com",
            recipient_list=self.recipient_list,
        )
