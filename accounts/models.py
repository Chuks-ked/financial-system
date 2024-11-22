from django.contrib.auth.models import User, AbstractUser
from django.db import models

class Account(AbstractUser):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


class Transaction(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    recipient_account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name='received_transactions', null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(
        max_length=10,
        choices=(('Deposit', 'Deposit'), ('Withdraw', 'Withdraw'), ('Transfer', 'Transfer')),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    rejection_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.account.username} performs a {self.transaction_type} of (${self.amount})"


class Notification(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
