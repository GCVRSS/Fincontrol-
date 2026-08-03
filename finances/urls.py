from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TransactionViewSet, GoalViewSet, MonthlySummaryView, MonthlyReportPDFView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'goals', GoalViewSet, basename='goal')

urlpatterns = [
    path('summary/', MonthlySummaryView.as_view(), name='monthly-summary'),
    path('report/pdf/', MonthlyReportPDFView.as_view(), name='monthly-report-pdf'),
] + router.urls