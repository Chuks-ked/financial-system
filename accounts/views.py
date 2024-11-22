from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from django.db.models import Sum
from django.core.mail import send_mail
from datetime import datetime, date
import decimal
from accounts.utils import EmailThread
from .models import *
from .serializers import *


class AccountView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AccountSerializer

    def get_object(self):
        return Account.objects.get(username=self.request.user)

# class DepositView(generics.CreateAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = TransactionSerializer

#     def create(self, request, *args, **kwargs):
#         account = Account.objects.get(username=request.user)
#         amount = request.data.get('amount', 0)
#         amount_decimal = decimal.Decimal(str(amount))
#         transaction = Transaction.objects.create(
#             account=account,
#             amount=amount_decimal,
#             transaction_type='Deposit'
#         )
#         account.balance += amount_decimal
#         account.save()
#         return Response({"message": "Deposit successful", "balance": account.balance}, status=status.HTTP_200_OK)
    
class DepositView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        account = Account.objects.get(user=user)
        amount = serializer.validated_data['amount']

        # Create a Pending transaction
        transaction = Transaction.objects.create(
            account=account,
            amount=amount,
            transaction_type='Deposit',
            status='Pending'
        )

        return Response({
            "message": "Deposit request submitted. Awaiting admin approval.",
            "transaction_id": transaction.id,
        }, status=status.HTTP_201_CREATED)


# class WithdrawView(generics.CreateAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = TransactionSerializer

#     def create(self, request, *args, **kwargs):
#         account = Account.objects.get(username=request.user)
#         amount = request.data.get('amount', 0)
#         amount_decimal = decimal.Decimal(str(amount))
#         if account.balance < amount_decimal:
#             return Response({"error": "Insufficient funds"}, status=status.HTTP_400_BAD_REQUEST)
#         transaction = Transaction.objects.create(
#             account=account,
#             amount=amount,
#             transaction_type='Withdraw'
#         )
#         account.balance -= amount_decimal
#         account.save()
#         return Response({"message": "Withdrawal successful", "balance": account.balance}, status=status.HTTP_200_OK)

class WithdrawView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        account = Account.objects.get(user=user)
        amount = serializer.validated_data['amount']

        if account.balance < amount:
            return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

        # Create a Pending transaction
        transaction = Transaction.objects.create(
            account=account,
            amount=amount,
            transaction_type='Withdraw',
            status='Pending'
        )

        return Response({
            "message": "Withdrawal request submitted. Awaiting admin approval.",
            "transaction_id": transaction.id,
        }, status=status.HTTP_201_CREATED)
    


class ApproveTransactionView(generics.UpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ApproveTransactionSerializer
    queryset = Transaction.objects.filter(status='Pending')

    def update(self, request, *args, **kwargs):
        transaction = self.get_object()
        status = request.data.get('status')
        rejection_reason = request.data.get('rejection_reason', None)

        # logic for rejection
        if status == 'Rejected' and not rejection_reason:
            return Response({"error": "Rejection reason is required for rejected transactions."}, status=status.HTTP_400_BAD_REQUEST)

        if status == 'Rejected':
            transaction.rejection_reason = rejection_reason

        # Existing logic for approval/rejection...
        if status == 'Approved':
            # Update the account balance
            if transaction.transaction_type == 'Deposit':
                transaction.account.balance += transaction.amount
            elif transaction.transaction_type == 'Withdraw':
                transaction.account.balance -= transaction.amount

            transaction.account.save()

            # Send approval email
            subject = "Transaction Approved"
            message = f"Your {transaction.transaction_type.lower()} of ${transaction.amount} has been approved."
        elif status == 'Rejected':
            # Send rejection email
            subject = "Transaction Rejected"
            message = f"Your {transaction.transaction_type.lower()} of ${transaction.amount} has been rejected."
        else:
            return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        # Create in-app notification
        notification_message = f"Your {transaction.transaction_type.lower()} of ${transaction.amount} has been {status.lower()}."
        Notification.objects.create(user=user, message=notification_message)


        # Update the transaction status
        transaction.status = status
        transaction.save()


        # Send email notification
        EmailThread(subject, message, [user_email]).start()

        return Response({
            "message": f"Transaction {transaction.id} has been {status.lower()}."
        }, status=status.HTTP_200_OK)



class TransferView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransferSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        sender_account = Account.objects.get(user=user)
        recipient_account = Account.objects.get(id=serializer.validated_data['recipient_account_id'])
        amount = serializer.validated_data['amount']

        # Perform the transfer
        sender_account.balance -= amount
        recipient_account.balance += amount

        sender_account.save()
        recipient_account.save()

        # Log the transaction
        Transaction.objects.create(
            account=sender_account,
            recipient_account=recipient_account,
            amount=amount,
            transaction_type='Transfer'
        )

        # Send email notification
        send_mail(
            subject="Transfer Confirmation",
            message=f"You have successfully transferred ${amount} to account {recipient_account.id}.",
            from_email="noreply@financialsystem.com",
            recipient_list=[request.user.email],
        )

        return Response({
            "message": "Transfer successful",
            "sender_balance": sender_account.balance
        }, status=status.HTTP_200_OK)

class TransactionHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionHistorySerializer

    def get_queryset(self):
        user = self.request.user
        account = Account.objects.get(user=user)
        return Transaction.objects.filter(account=account).order_by('-created_at')


class TransactionFilter(filters.FilterSet):
    transaction_type = filters.CharFilter(field_name='transaction_type', lookup_expr='iexact')
    start_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    end_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'start_date', 'end_date']

class FilteredTransactionHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionHistorySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TransactionFilter
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']  # Default ordering

    def get_queryset(self):
        user = self.request.user
        account = Account.objects.get(user=user)
        return Transaction.objects.filter(account=account)

class MonthlyStatementView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year, month):
        user = request.user
        account = Account.objects.get(user=user)

        transactions = Transaction.objects.filter(
            account=account,
            created_at__year=year,
            created_at__month=month
        )

        summary = {
            "total_deposits": transactions.filter(transaction_type='Deposit').aggregate(Sum('amount'))['amount__sum'] or 0.00,
            "total_withdrawals": transactions.filter(transaction_type='Withdraw').aggregate(Sum('amount'))['amount__sum'] or 0.00,
            "total_transfers": transactions.filter(transaction_type='Transfer').aggregate(Sum('amount'))['amount__sum'] or 0.00,
            "transaction_count": transactions.count()
        }

        return Response({
            "month": f"{year}-{month:02d}",
            "summary": summary,
            "transactions": TransactionHistorySerializer(transactions, many=True).data
        }, status=status.HTTP_200_OK)


class AdminUserTransactionHistoryView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = TransactionHistorySerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        account = Account.objects.get(user_id=user_id)
        return Transaction.objects.filter(account=account)


class LimitedWithdrawalView(WithdrawView):
    def create(self, request, *args, **kwargs):
        user = request.user
        account = Account.objects.get(user=user)

        today = date.today()
        daily_total = Transaction.objects.filter(
            account=account,
            transaction_type='Withdraw',
            created_at__date=today
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00

        max_limit = 5000.00  # Example limit
        if daily_total + float(request.data['amount']) > max_limit:
            return Response({"error": "Daily withdrawal limit exceeded."}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)


class NotificationView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return self.request.user.notifications.order_by("-created_at")


class MarkNotificationReadView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        if notification.user != request.user:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)
