from django.urls import path
from .views import *

urlpatterns = [
    path('account/', AccountView.as_view(), name='account'),
    path('deposit/', DepositView.as_view(), name='deposit'),
    path('withdraw/', WithdrawView.as_view(), name='withdraw'),
    path('withdraw-limited/', LimitedWithdrawalView.as_view(), name='withdraw-limited'),
    path('transfer/', TransferView.as_view(), name='transfer'),
    path('transaction-history/', TransactionHistoryView.as_view(), name='transaction-history'),
    path('transaction-history/filter/', FilteredTransactionHistoryView.as_view(), name='filtered-transaction-history'),
    path('monthly-statement/<int:year>/<int:month>/', MonthlyStatementView.as_view(), name='monthly-statement'),
    path('admin/user/<int:user_id>/transactions/', AdminUserTransactionHistoryView.as_view(), name='admin-user-transactions'),
    path('admin/transactions/<int:pk>/approve/', ApproveTransactionView.as_view(), name='approve-transaction'),
    path('notifications/', NotificationView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(), name='mark-notification-read'),
]
