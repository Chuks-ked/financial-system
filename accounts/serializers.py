from rest_framework import serializers
from .models import *

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'username', 'balance']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'account', 'amount', 'transaction_type', 'created_at']

class TransferSerializer(serializers.Serializer):
    recipient_account_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, data):
        user = self.context['request'].user
        account = Account.objects.get(user=user)
        recipient_account = Account.objects.filter(id=data['recipient_account_id']).first()

        if not recipient_account:
            raise serializers.ValidationError("Recipient account does not exist.")
        if account.id == recipient_account.id:
            raise serializers.ValidationError("You cannot transfer money to your own account.")
        if account.balance < data['amount']:
            raise serializers.ValidationError("Insufficient balance for this transfer.")

        return data

# class TransactionHistorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Transaction
#         fields = ['id', 'amount', 'transaction_type', 'recipient_account', 'created_at']
#         depth = 1  # Includes related model details (e.g., recipient account)

class TransactionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'transaction_type', 'status', 'recipient_account', 'created_at']


class ApproveTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'status']

    def validate_status(self, value):
        if value not in ['Approved', 'Rejected']:
            raise serializers.ValidationError("Invalid status. Use 'Approved' or 'Rejected'.")
        return value


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'created_at']
