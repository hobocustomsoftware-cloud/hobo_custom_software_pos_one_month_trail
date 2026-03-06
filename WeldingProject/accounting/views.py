from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta, datetime
from .models import ExpenseCategory, Expense, Transaction
from .serializers import (
    ExpenseCategorySerializer, ExpenseSerializer, TransactionSerializer,
    PnLSummarySerializer, ProfitMarginAnalysisSerializer
)
from .services import (
    calculate_net_profit, calculate_profit_from_sales,
    get_profit_trend, get_pnl_by_outlet, analyze_profit_margin_shrinkage
)
from core.permissions import IsAdminOrHigher
from core.outlet_utils import filter_queryset_by_outlet, get_request_outlet_id


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """Expense Category CRUD"""
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAuthenticated]


class ExpenseViewSet(viewsets.ModelViewSet):
    """Expense CRUD"""
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Auto-set created_by and outlet (branch lock) for non-owners"""
        from core.outlet_utils import is_owner
        user = self.request.user
        kwargs = {'created_by': user}
        if not is_owner(user) and getattr(user, 'primary_outlet_id', None):
            kwargs['outlet_id'] = user.primary_outlet_id
        serializer.save(**kwargs)
    
    def get_queryset(self):
        """Filter by outlet (branch lock) and optional date range"""
        queryset = super().get_queryset()
        queryset = filter_queryset_by_outlet(queryset, self.request)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(expense_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(expense_date__lte=end_date)
        return queryset.order_by('-expense_date', '-created_at')


class TransactionListView(generics.ListAPIView):
    """List all transactions with filtering (outlet-scoped for non-owners)"""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from core.outlet_utils import get_request_outlet_id, is_owner
        queryset = super().get_queryset()
        outlet_id = get_request_outlet_id(self.request)
        if outlet_id is not None:
            # Filter: income from sale_transaction.outlet, expense from expense.outlet
            from django.db.models import Q
            queryset = queryset.filter(
                Q(sale_transaction__outlet_id=outlet_id) | Q(expense__outlet_id=outlet_id)
            )
        elif not is_owner(self.request.user):
            queryset = queryset.none()
        transaction_type = self.request.query_params.get('type')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if start_date:
            queryset = queryset.filter(transaction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_date__lte=end_date)
        return queryset.order_by('-transaction_date', '-created_at')


class PnLSummaryView(generics.RetrieveAPIView):
    """Get P&L Summary for a date range (role-based: outlet-scoped for non-owner)."""
    permission_classes = [IsAuthenticated]
    serializer_class = PnLSummarySerializer
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        outlet_id = get_request_outlet_id(request)
        if start_date:
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            from datetime import datetime
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        pnl_data = calculate_net_profit(start_date, end_date, outlet_id=outlet_id)
        serializer = self.get_serializer(pnl_data)
        return Response(serializer.data)


class ProfitFromSalesView(generics.RetrieveAPIView):
    """Get profit from sales only (gross profit); outlet-scoped for non-owner."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        outlet_id = get_request_outlet_id(request)
        if start_date:
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            from datetime import datetime
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        profit_data = calculate_profit_from_sales(start_date, end_date, outlet_id=outlet_id)
        return Response(profit_data)


class ProfitTrendView(generics.RetrieveAPIView):
    """Get daily profit trend"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        trend = get_profit_trend(days)
        return Response({'trend': trend})


class ProfitMarginAnalysisView(generics.RetrieveAPIView):
    """Analyze profit margin shrinkage and USD inflation impact"""
    permission_classes = [IsAuthenticated]
    serializer_class = ProfitMarginAnalysisSerializer
    
    def get(self, request):
        analysis = analyze_profit_margin_shrinkage()
        serializer = self.get_serializer(analysis)
        return Response(serializer.data)


class OwnerSummaryView(APIView):
    """
    Owner / AI Agent: တစ်ခါခေါ်ပြီး Sales + P&L summary ရရန်.
    GET /api/accounting/owner-summary/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    Default: last 30 days.
    """
    permission_classes = [IsAuthenticated, IsAdminOrHigher]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        end_dt = timezone.now().date()
        start_dt = end_dt - timedelta(days=30)
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                pass

        pnl = calculate_net_profit(start_dt, end_dt)
        profit_from_sales = calculate_profit_from_sales(start_dt, end_dt)
        trend = get_profit_trend(min(30, (end_dt - start_dt).days or 1))

        def dec(v):
            return str(v) if hasattr(v, '__float__') else v

        trend_serialized = [
            {
                'date': str(d['date']),
                'income': dec(d['income']),
                'expenses': dec(d['expenses']),
                'net_profit': dec(d['net_profit']),
                'profit_margin_percent': dec(d['profit_margin_percent']),
            }
            for d in trend[:30]
        ]

        pl_by_outlet = get_pnl_by_outlet(start_dt, end_dt)
        pl_by_outlet_serialized = [
            {
                'outlet_id': o['outlet_id'],
                'outlet_name': o['outlet_name'],
                'total_income': dec(o['total_income']),
                'total_expenses': dec(o['total_expenses']),
                'net_profit': dec(o['net_profit']),
            }
            for o in pl_by_outlet
        ]

        return Response({
            'period': {
                'start_date': str(start_dt),
                'end_date': str(end_dt),
            },
            'pl_by_outlet': pl_by_outlet_serialized,
            'pnl': {
                'total_income': dec(pnl['total_income']),
                'total_expenses': dec(pnl['total_expenses']),
                'net_profit': dec(pnl['net_profit']),
                'profit_margin_percent': dec(pnl['profit_margin_percent']),
                'transaction_count': pnl['transaction_count'],
            },
            'profit_from_sales': {
                'total_revenue': dec(profit_from_sales['total_revenue']),
                'total_cost': dec(profit_from_sales['total_cost']),
                'gross_profit': dec(profit_from_sales['gross_profit']),
                'gross_profit_margin_percent': dec(profit_from_sales['gross_profit_margin_percent']),
            },
            'trend_days': trend_serialized,
        })
