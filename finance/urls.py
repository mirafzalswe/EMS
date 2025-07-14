from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import FuturePaymentListCreateView, FuturePaymentStatusUpdateView, FuturePaymentDeleteOldView, monthly_income

router = DefaultRouter()
router.register(r'prices', views.PriceViewSet, basename='price')
router.register(r'discounts', views.DiscountViewSet, basename='discount')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'expense-categories', views.ExpenseCategoryViewSet, basename='expense-category')
router.register(r'expenses', views.ExpenseViewSet, basename='expense')
router.register(r'teacher-salaries', views.TeacherSalaryViewSet, basename='teacher-salary')

urlpatterns = [
    path('', include(router.urls)),
    
    # Финансовый модуль - список студентов с балансом
    path('student-payments/', views.student_payments_list, name='student_payments_list'),
    
    # Добавление платежа
    path('add-payment/<int:student_id>/', views.add_payment, name='add_payment'),
    
    # История платежей студента
    path('payment-history/<int:student_id>/', views.payment_history, name='payment_history'),
    
    # Ручное списание средств
    path('manual-withdraw/<int:student_id>/', views.manual_withdraw, name='manual_withdraw'),
    
    # Генерация чека
    path('generate-receipt/<int:payment_id>/', views.generate_receipt, name='generate_receipt'),
    
    # Автоматическое списание
    path('auto-withdraw/', views.auto_withdraw_view, name='auto_withdraw'),
    
    path('future-payments/', FuturePaymentListCreateView.as_view(), name='future_payments_list_create'),
    path('future-payments/<int:student_id>/', FuturePaymentListCreateView.as_view(), name='future_payments_by_student'),
    path('future-payments/status/<int:pk>/', FuturePaymentStatusUpdateView.as_view(), name='future_payment_status_update'),
    path('future-payments/delete-old/', FuturePaymentDeleteOldView.as_view(), name='future_payments_delete_old'),
    path('api/monthly-income/', monthly_income, name='monthly_income'),
] 