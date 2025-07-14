from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db.models import Sum, Q
from django.utils import timezone
from schools.permissions import IsSchoolStaff, IsSchoolAdmin
from .models import (
    Price, Discount, Invoice, InvoiceItem, Payment,
    ExpenseCategory, Expense, TeacherSalary,
    PaymentStatus, InvoiceStatus, StudentFinanceManager, Currency, PaymentMethod, FuturePayment, MonthlyIncomeStat
)
from .serializers import (
    PriceSerializer, DiscountSerializer, InvoiceSerializer,
    InvoiceItemSerializer, PaymentSerializer, ExpenseCategorySerializer,
    ExpenseSerializer, TeacherSalarySerializer, FuturePaymentSerializer
)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q
from users.models import User
from courses.models import Enrollment
from datetime import datetime, date
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.conf import settings
import os
from datetime import timedelta
import calendar
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, AllowAny
from django.db.models.functions import TruncMonth
from collections import defaultdict

class PriceViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления ценами.
    """
    serializer_class = PriceSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]
    
    def get_queryset(self):
        """
        Возвращает цены для текущего учебного центра.
        """
        user = self.request.user
        if user.is_superuser:
            return Price.objects.all()
        return Price.objects.filter(school=user.school)
    
    def perform_create(self, serializer):
        """
        Сохраняет создателя цены.
        """
        serializer.save(created_by=self.request.user)

class DiscountViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления скидками.
    """
    serializer_class = DiscountSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]
    
    def get_queryset(self):
        """
        Возвращает скидки для текущего учебного центра.
        """
        user = self.request.user
        if user.is_superuser:
            return Discount.objects.all()
        return Discount.objects.filter(school=user.school)
    
    def perform_create(self, serializer):
        """
        Сохраняет создателя скидки.
        """
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def apply_to_course(self, request, pk=None):
        """
        Применяет скидку к курсу.
        """
        discount = self.get_object()
        course_id = request.data.get('course_id')
        
        if not course_id:
            return Response(
                {"error": "Необходимо указать ID курса"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        discount.applies_to_courses.add(course_id)
        return Response({"status": "Скидка применена к курсу"})

class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления счетами.
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]
    
    def get_queryset(self):
        """
        Возвращает счета в зависимости от роли пользователя.
        """
        user = self.request.user
        if user.is_superuser:
            return Invoice.objects.all()
        elif user.is_teacher:
            return Invoice.objects.filter(
                Q(school=user.school) | Q(created_by=user)
            )
        else:
            return Invoice.objects.filter(
                Q(school=user.school) | Q(student=user.student)
            )
    
    def perform_create(self, serializer):
        """
        Сохраняет создателя счета и генерирует номер.
        """
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """
        Добавляет позицию в счет.
        """
        invoice = self.get_object()
        serializer = InvoiceItemSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(invoice=invoice)
            invoice.update_total()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def apply_discount(self, request, pk=None):
        """
        Применяет скидку к счету.
        """
        invoice = self.get_object()
        discount_id = request.data.get('discount_id')
        
        if not discount_id:
            return Response(
                {"error": "Необходимо указать ID скидки"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            discount = Discount.objects.get(id=discount_id)
            invoice.apply_discount(discount)
            return Response({"status": "Скидка применена"})
        except Discount.DoesNotExist:
            return Response(
                {"error": "Скидка не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )

class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления платежами.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]
    
    def get_queryset(self):
        """
        Возвращает платежи в зависимости от роли пользователя.
        """
        user = self.request.user
        if user.is_superuser:
            return Payment.objects.all()
        elif user.is_teacher:
            return Payment.objects.filter(
                Q(school=user.school) | Q(created_by=user)
            )
        else:
            return Payment.objects.filter(
                Q(school=user.school) | Q(invoice__student=user.student)
            )
    
    def perform_create(self, serializer):
        """
        Сохраняет создателя платежа и генерирует номер.
        """
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Обрабатывает платеж.
        """
        payment = self.get_object()
        if payment.status != PaymentStatus.PENDING:
            return Response(
                {"error": "Платеж уже обработан"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.status = PaymentStatus.COMPLETED
        payment.processed_by = request.user
        payment.save()
        
        # Обновляем статус счета
        payment.invoice.update_status()
        
        return Response({"status": "Платеж обработан"})

class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления категориями расходов.
    """
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]
    
    def get_queryset(self):
        """
        Возвращает категории расходов для текущего учебного центра.
        """
        user = self.request.user
        if user.is_superuser:
            return ExpenseCategory.objects.all()
        return ExpenseCategory.objects.filter(school=user.school)

class ExpenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления расходами.
    """
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]
    
    def get_queryset(self):
        """
        Возвращает расходы для текущего учебного центра.
        """
        user = self.request.user
        if user.is_superuser:
            return Expense.objects.all()
        return Expense.objects.filter(school=user.school)
    
    def perform_create(self, serializer):
        """
        Сохраняет создателя расхода.
        """
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Утверждает расход.
        """
        expense = self.get_object()
        if expense.is_approved:
            return Response(
                {"error": "Расход уже утвержден"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        expense.is_approved = True
        expense.approved_by = request.user
        expense.save()
        
        return Response({"status": "Расход утвержден"})

class TeacherSalaryViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления зарплатами преподавателей.
    """
    serializer_class = TeacherSalarySerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]
    
    def get_queryset(self):
        """
        Возвращает зарплаты в зависимости от роли пользователя.
        """
        user = self.request.user
        if user.is_superuser:
            return TeacherSalary.objects.all()
        elif user.is_teacher:
            return TeacherSalary.objects.filter(teacher=user)
        else:
            return TeacherSalary.objects.filter(school=user.school)
    
    def perform_create(self, serializer):
        """
        Сохраняет создателя зарплаты.
        """
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """
        Отмечает зарплату как выплаченную.
        """
        salary = self.get_object()
        if salary.is_paid:
            return Response(
                {"error": "Зарплата уже выплачена"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        salary.is_paid = True
        salary.payment_date = timezone.now().date()
        salary.save()
        
        return Response({"status": "Зарплата отмечена как выплаченная"})

@login_required
def student_payments_list(request):
    """
    Отображает список всех студентов с их балансом и будущими оплатами (через FuturePayment), сгруппированными по группам.
    """
    if not request.user.is_admin:
        messages.error(request, "У вас нет доступа к этой странице.")
        return redirect('admin_dashboard')

    students = User.objects.filter(user_type='student').order_by('first_name', 'last_name')
    students_data = []
    total_profit = 0
    total_debt = 0
    today = timezone.now().date()
    three_months_later = today + timedelta(days=92)
    for student in students:
        balance = StudentFinanceManager.get_balance(student)
        last_payment = StudentFinanceManager.get_last_payment(student)
        if balance >= 0:
            total_profit += balance
        else:
            total_debt += abs(balance)
        enrollments = student.enrollments.filter(is_active=True)
        grouped_payments = []
        today = date.today()
        month_start = today.replace(day=1)
        for enrollment in enrollments:
            group = enrollment.group
            price = group.course.price
            payments_rows = []
            for i in range(3):
                year = month_start.year + (month_start.month - 1 + i) // 12
                month = (month_start.month - 1 + i) % 12 + 1
                day = min(enrollment.enrollment_date.day, 28)
                try:
                    pay_date = month_start.replace(year=year, month=month, day=day)
                except ValueError:
                    pay_date = month_start.replace(year=year, month=month, day=1)
                fp = FuturePayment.objects.filter(student=student, group=group, payment_date=pay_date).first()
                if fp:
                    payments_rows.append(fp)
                else:
                    payments_rows.append(type('FakeFP', (), {
                        'payment_date': pay_date,
                        'amount': price,
                        'status': 'pending',
                        'id': None
                    })())
            grouped_payments.append({
                'group': group,
                'payments': payments_rows
            })
        students_data.append({
            'student': student,
            'balance': balance,
            'last_payment': last_payment,
            'is_positive': balance >= 0,
            'enrollments': enrollments,
            'grouped_payments': grouped_payments
        })
    context = {
        'students_data': students_data,
        'total_profit': total_profit,
        'total_debt': total_debt,
        'title': "Barcha to'lovlar"
    }
    return render(request, 'finance/student_payments_list.html', context)

@login_required
def add_payment(request, student_id):
    """
    Добавляет новый платеж для студента.
    """
    if not request.user.is_admin:
        messages.error(request, "У вас нет доступа к этой странице.")
        return redirect('admin_dashboard')
    
    student = get_object_or_404(User, id=student_id, user_type='student')
    
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount'))
            payment_method = request.POST.get('payment_method', PaymentMethod.CASH)
            notes = request.POST.get('notes', '')
            
            if amount <= 0:
                messages.error(request, "Сумма должна быть больше нуля.")
                return redirect('student_payments_list')
            
            # Создаем invoice и payment
            from courses.models import Course
            course = student.enrollments.first().group.course if student.enrollments.exists() else None
            
            invoice = Invoice.objects.create(
                invoice_number=f"PAY-{student.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                school=course.subject.school if course else None,
                student=student,
                course=course,
                total_amount=amount,
                paid_amount=amount,
                currency=Currency.UZS,
                status=InvoiceStatus.PAID,
                issue_date=timezone.now().date(),
                due_date=timezone.now().date(),
                description=f"Платеж: {notes}",
                created_by=request.user
            )
            
            payment = Payment.objects.create(
                payment_number=f"PAY-{student.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                invoice=invoice,
                amount=amount,
                currency=Currency.UZS,
                payment_date=timezone.now().date(),
                payment_method=payment_method,
                status=PaymentStatus.COMPLETED,
                notes=notes,
                processed_by=request.user,
                created_by=request.user
            )
            # --- Обновление статистики дохода по месяцам ---
            if payment.status == PaymentStatus.COMPLETED:
                pay_date = payment.payment_date or datetime.date.today()
                stat, created = MonthlyIncomeStat.objects.get_or_create(
                    year=pay_date.year,
                    month=pay_date.month,
                    defaults={'total_income': 0}
                )
                stat.total_income += payment.amount
                stat.save()
            # --- конец блока ---
            messages.success(request, f"Платеж на сумму {amount} сум успешно добавлен.")
            return redirect('student_payments_list')
            
        except (ValueError, TypeError):
            messages.error(request, "Неверная сумма платежа.")
            return redirect('student_payments_list')
    
    context = {
        'student': student,
        'payment_methods': PaymentMethod.choices,
        'today': date.today(),
        'title': f'Добавить платеж - {student.get_full_name()}'
    }
    return render(request, 'finance/add_payment.html', context)

@login_required
def payment_history(request, student_id):
    """
    Отображает историю платежей студента.
    """
    if not request.user.is_admin:
        messages.error(request, "У вас нет доступа к этой странице.")
        return redirect('admin_dashboard')
    
    student = get_object_or_404(User, id=student_id, user_type='student')
    payments = StudentFinanceManager.get_payment_history(student)
    balance = StudentFinanceManager.get_balance(student)
    
    context = {
        'student': student,
        'payments': payments,
        'balance': balance,
        'title': f'История платежей - {student.get_full_name()}'
    }
    return render(request, 'finance/payment_history.html', context)

@login_required
def manual_withdraw(request, student_id):
    """
    Ручное списание средств с баланса студента.
    """
    if not request.user.is_admin:
        messages.error(request, "У вас нет доступа к этой странице.")
        return redirect('admin_dashboard')
    
    student = get_object_or_404(User, id=student_id, user_type='student')
    
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount'))
            notes = request.POST.get('notes', 'Ручное списание админом')
            
            if amount <= 0:
                messages.error(request, "Сумма должна быть больше нуля.")
                return redirect('student_payments_list')
            
            # Выполняем списание
            payment = StudentFinanceManager.manual_withdraw(
                student=student,
                amount=amount,
                admin_user=request.user,
                note=notes,
                payment_method=PaymentMethod.CASH
            )
            
            messages.success(request, f"Списание на сумму {amount} сум успешно выполнено.")
            return redirect('student_payments_list')
            
        except (ValueError, TypeError):
            messages.error(request, "Неверная сумма списания.")
            return redirect('student_payments_list')
    
    context = {
        'student': student,
        'balance': StudentFinanceManager.get_balance(student),
        'today': date.today(),
        'title': f'Списание средств - {student.get_full_name()}'
    }
    return render(request, 'finance/manual_withdraw.html', context)

@login_required
def generate_receipt(request, payment_id):
    """
    Генерирует и возвращает минималистичный PDF чек для платежа (всё на одной странице).
    """
    if not request.user.is_admin:
        messages.error(request, "У вас нет доступа к этой странице.")
        return redirect('admin_dashboard')
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{payment.payment_number}.pdf"'
    
    from reportlab.platypus import Image
    from django.conf import settings
    import os
    doc = SimpleDocTemplate(response, pagesize=(400, 420), topMargin=18, bottomMargin=18, leftMargin=18, rightMargin=18)
    elements = []
    styles = getSampleStyleSheet()
    
    # Логотип
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'users', 'Logo-icon.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=44, height=44)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 6))
    
    # Название центра
    title_style = ParagraphStyle(
        'Title', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER, textColor=colors.black, fontName='Helvetica-Bold', spaceAfter=2
    )
    elements.append(Paragraph("DISCOVERY LC", title_style))
    
    # O'tkazma kvitansiyasi
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER, textColor=colors.black, fontName='Helvetica', spaceAfter=10
    )
    elements.append(Paragraph("O'tkazma kvitansiyasi", subtitle_style))
    
    # Основная информация
    info_style = ParagraphStyle(
        'Info', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.black, fontName='Helvetica', spaceAfter=6
    )
    
    # To'lovchi ismi
    elements.append(Paragraph(f"To'lovchi ismi: {payment.invoice.student.get_full_name()}", info_style))
    # To'lov turi (только латиница, иначе —)
    def is_ascii(s):
        try:
            s.encode('ascii')
            return True
        except Exception:
            return False
    payment_type_display = payment.get_payment_method_display() if hasattr(payment, 'get_payment_method_display') else None
    if not payment_type_display or not is_ascii(payment_type_display):
        payment_type_display = '—'
    elements.append(Paragraph(f"To'lov turi: {payment_type_display}", info_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("---------------------", info_style))
    elements.append(Spacer(1, 4))
    # Amaliyot sanasi
    elements.append(Paragraph(f"Amaliyot sanasi: {payment.payment_date.strftime('%d.%m.%Y')}", info_style))
    # Guruh (всегда)
    group_name = payment.invoice.group.name if payment.invoice.group else '—'
    elements.append(Paragraph(f"Guruh: {group_name}", info_style))
    elements.append(Spacer(1, 18))
    
    # Сумма (крупно)
    amount_style = ParagraphStyle(
        'Amount', parent=styles['Heading2'], fontSize=16, alignment=TA_CENTER, textColor=colors.black, fontName='Helvetica-Bold', spaceAfter=10
    )
    elements.append(Paragraph(f"{payment.amount:,.0f} {payment.currency}", amount_style))
    elements.append(Spacer(1, 10))
    
    # Сайт внизу
    site_style = ParagraphStyle(
        'Site', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#888888'), fontName='Helvetica', spaceAfter=0
    )
    elements.append(Paragraph("www.discoverylc.uz", site_style))
    
    doc.build(elements)
    return response

@login_required
def auto_withdraw_view(request):
    """
    Запускает автоматическое списание средств (для админов).
    """
    if not request.user.is_admin:
        messages.error(request, "У вас нет доступа к этой странице.")
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        try:
            # Выполняем автосписание
            StudentFinanceManager.auto_monthly_withdraw()
            messages.success(request, "Автоматическое списание выполнено успешно.")
        except Exception as e:
            messages.error(request, f"Ошибка при выполнении автосписания: {str(e)}")
        
        return redirect('student_payments_list')
    
    return redirect('student_payments_list')

class FuturePaymentListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, student_id=None):
        """
        Получить будущие оплаты для студента (или всех студентов).
        Фильтрация: только оплаты в пределах 3 месяцев от сегодня.
        """
        today = timezone.now().date()
        three_months_later = today + timedelta(days=92)
        qs = FuturePayment.objects.all()
        if student_id:
            qs = qs.filter(student_id=student_id)
        qs = qs.filter(payment_date__gte=today, payment_date__lte=three_months_later)
        serializer = FuturePaymentSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Создать будущую оплату (админ).
        """
        serializer = FuturePaymentSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            return Response({'status': instance.status}, status=201)
        return Response(serializer.errors, status=400)

class FuturePaymentStatusUpdateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        """
        Обновить статус оплаты (например, отметить как оплачено).
        """
        payment = get_object_or_404(FuturePayment, pk=pk)
        status_value = request.data.get('status')
        if status_value not in dict(FuturePayment.STATUS_CHOICES):
            return Response({'error': 'Некорректный статус'}, status=400)
        payment.status = status_value
        payment.save()
        return Response({'status': payment.status})

class FuturePaymentDeleteOldView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        Удалить оплаты старше 3 месяцев (cron или вручную).
        """
        today = timezone.now().date()
        three_months_ago = today - timedelta(days=92)
        deleted, _ = FuturePayment.objects.filter(payment_date__lt=three_months_ago).delete()
        return Response({'deleted': deleted})

@api_view(['GET'])
def monthly_income(request):
    from .models import Payment, PaymentStatus, Expense
    from django.db.models.functions import TruncMonth
    from django.db.models import Sum
    from collections import defaultdict
    import calendar

    # Доходы по месяцам
    income_qs = (
        Payment.objects
        .filter(status=PaymentStatus.COMPLETED)
        .annotate(month=TruncMonth('payment_date'))
        .values('month')
        .annotate(income=Sum('amount'))
        .order_by('month')
    )
    # Расходы по месяцам
    expense_qs = (
        Expense.objects
        .annotate(month=TruncMonth('expense_date'))
        .values('month')
        .annotate(expense=Sum('amount'))
        .order_by('month')
    )
    # Собираем данные по месяцам
    data = defaultdict(lambda: {'income': 0, 'expense': 0})
    for x in income_qs:
        if x['month']:
            data[x['month']]['income'] = float(x['income'] or 0)
    for x in expense_qs:
        if x['month']:
            data[x['month']]['expense'] = float(x['expense'] or 0)
    # Формируем итоговый список
    result = []
    for month in sorted(data.keys()):
        result.append({
            'month': month.strftime('%Y-%m'),
            'income': data[month]['income'],
            'expense': data[month]['expense'],
            'net': data[month]['income'] - data[month]['expense']
        })
    # Общие суммы
    total_income = sum(x['income'] for x in result)
    total_expense = sum(x['expense'] for x in result)
    total_net = total_income - total_expense
    return Response({
        'monthly': result,
        'total_income': total_income,
        'total_expense': total_expense,
        'total_net': total_net
    })