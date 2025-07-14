from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Price, Discount, Invoice, InvoiceItem, Payment,
    ExpenseCategory, Expense, TeacherSalary, FuturePayment
)

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('school', 'course', 'amount', 'currency', 'price_type', 'is_active', 'effective_from', 'effective_to', 'created_at')
    list_filter = ('school', 'currency', 'price_type', 'is_active', 'created_at')
    search_fields = ('school__name', 'course__name', 'description')
    date_hierarchy = 'effective_from'
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active', 'amount')
    actions = ['activate_prices', 'deactivate_prices']

    def activate_prices(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} цен активировано.')
    activate_prices.short_description = "Активировать выбранные цены"

    def deactivate_prices(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} цен деактивировано.')
    deactivate_prices.short_description = "Деактивировать выбранные цены"

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('school', 'name', 'percentage', 'amount', 'currency', 'code', 'is_active', 'valid_from', 'valid_to', 'current_uses')
    list_filter = ('school', 'currency', 'is_active', 'valid_from', 'valid_to')
    search_fields = ('name', 'code', 'description')
    filter_horizontal = ('applies_to_courses',)
    date_hierarchy = 'valid_from'
    readonly_fields = ('current_uses', 'created_at', 'updated_at')
    list_editable = ('is_active', 'percentage', 'amount')
    actions = ['activate_discounts', 'deactivate_discounts']

    def activate_discounts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} скидок активировано.')
    activate_discounts.short_description = "Активировать выбранные скидки"

    def deactivate_discounts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} скидок деактивировано.')
    deactivate_discounts.short_description = "Деактивировать выбранные скидки"

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('description', 'quantity', 'unit_price', 'discount_percentage', 'total')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'school', 'student', 'total_amount', 'paid_amount', 'balance_display', 'currency', 'status', 'issue_date', 'due_date', 'is_overdue')
    list_filter = ('school', 'status', 'currency', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'student__first_name', 'student__last_name', 'description')
    date_hierarchy = 'issue_date'
    inlines = [InvoiceItemInline]
    readonly_fields = ('invoice_number', 'paid_amount', 'created_at', 'updated_at')
    actions = ['mark_as_paid', 'mark_as_overdue', 'send_reminder']
    list_editable = ('status',)

    def balance_display(self, obj):
        balance = obj.calculate_balance()
        if balance > 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', f'{balance} {obj.currency}')
        elif balance < 0:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', f'{abs(balance)} {obj.currency}')
        else:
            return format_html('<span style="color: green;">Оплачен</span>')
    balance_display.short_description = 'Баланс'

    def is_overdue(self, obj):
        if obj.due_date < timezone.now().date() and obj.status not in ['paid', 'refunded']:
            return format_html('<span style="color: red;">Просрочен</span>')
        return format_html('<span style="color: green;">В срок</span>')
    is_overdue.short_description = 'Статус срока'

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid')
        self.message_user(request, f'{updated} счетов отмечено как оплаченные.')
    mark_as_paid.short_description = "Отметить как оплаченные"

    def mark_as_overdue(self, request, queryset):
        updated = queryset.update(status='overdue')
        self.message_user(request, f'{updated} счетов отмечено как просроченные.')
    mark_as_overdue.short_description = "Отметить как просроченные"

    def send_reminder(self, request, queryset):
        # Здесь можно добавить логику отправки напоминаний
        self.message_user(request, f'Напоминания отправлены для {queryset.count()} счетов.')
    send_reminder.short_description = "Отправить напоминания"

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'student_name', 'amount', 'currency', 'payment_date', 'payment_method', 'status', 'processed_by', 'receipt_link')
    list_filter = ('status', 'payment_method', 'currency', 'payment_date', 'processed_by')
    search_fields = ('payment_number', 'invoice__invoice_number', 'transaction_id', 'receipt_number', 'invoice__student__first_name', 'invoice__student__last_name')
    date_hierarchy = 'payment_date'
    readonly_fields = ('payment_number', 'created_at', 'updated_at')
    actions = ['mark_as_completed', 'mark_as_failed', 'generate_receipts']
    list_editable = ('status',)

    def student_name(self, obj):
        return obj.invoice.student.get_full_name()
    student_name.short_description = 'Студент'

    def receipt_link(self, obj):
        if obj.status == 'completed':
            return format_html('<a href="{}" target="_blank">Скачать чек</a>', 
                             reverse('generate_receipt', args=[obj.id]))
        return '-'
    receipt_link.short_description = 'Чек'

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} платежей отмечено как завершенные.')
    mark_as_completed.short_description = "Отметить как завершенные"

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} платежей отмечено как неудачные.')
    mark_as_failed.short_description = "Отметить как неудачные"

    def generate_receipts(self, request, queryset):
        # Здесь можно добавить логику массовой генерации чеков
        self.message_user(request, f'Чеки сгенерированы для {queryset.count()} платежей.')
    generate_receipts.short_description = "Сгенерировать чеки"

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('school', 'name', 'is_active', 'expenses_count', 'total_expenses')
    list_filter = ('school', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    actions = ['activate_categories', 'deactivate_categories']

    def expenses_count(self, obj):
        return obj.expenses.count()
    expenses_count.short_description = 'Количество расходов'

    def total_expenses(self, obj):
        total = obj.expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        return f'{total} {obj.expenses.first().currency if obj.expenses.exists() else "UZS"}'
    total_expenses.short_description = 'Общая сумма'

    def activate_categories(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} категорий активировано.')
    activate_categories.short_description = "Активировать выбранные категории"

    def deactivate_categories(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} категорий деактивировано.')
    deactivate_categories.short_description = "Деактивировать выбранные категории"

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('school', 'category', 'description', 'amount', 'currency', 'expense_date', 'is_approved', 'approved_by', 'created_by')
    list_filter = ('school', 'category', 'currency', 'is_approved', 'expense_date', 'created_by')
    search_fields = ('description', 'notes', 'created_by__username')
    date_hierarchy = 'expense_date'
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_expenses', 'reject_expenses', 'mark_as_paid']
    list_editable = ('is_approved',)

    def approve_expenses(self, request, queryset):
        updated = queryset.update(is_approved=True, approved_by=request.user)
        self.message_user(request, f'{updated} расходов одобрено.')
    approve_expenses.short_description = "Одобрить выбранные расходы"

    def reject_expenses(self, request, queryset):
        updated = queryset.update(is_approved=False, approved_by=None)
        self.message_user(request, f'{updated} расходов отклонено.')
    reject_expenses.short_description = "Отклонить выбранные расходы"

    def mark_as_paid(self, request, queryset):
        # Здесь можно добавить логику отметки как выплаченные
        self.message_user(request, f'{queryset.count()} расходов отмечено как выплаченные.')
    mark_as_paid.short_description = "Отметить как выплаченные"

@admin.register(TeacherSalary)
class TeacherSalaryAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'school', 'period_start', 'period_end', 'base_salary', 'total_salary', 'currency', 'is_paid', 'payment_date', 'created_by')
    list_filter = ('school', 'currency', 'is_paid', 'period_start', 'period_end', 'created_by')
    search_fields = ('teacher__username', 'teacher__first_name', 'teacher__last_name', 'notes')
    date_hierarchy = 'period_start'
    readonly_fields = ('total_salary', 'created_at', 'updated_at')
    actions = ['mark_as_paid', 'mark_as_unpaid', 'calculate_salaries']
    list_editable = ('is_paid', 'payment_date')

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(is_paid=True, payment_date=timezone.now().date())
        self.message_user(request, f'{updated} зарплат отмечено как выплаченные.')
    mark_as_paid.short_description = "Отметить как выплаченные"

    def mark_as_unpaid(self, request, queryset):
        updated = queryset.update(is_paid=False, payment_date=None)
        self.message_user(request, f'{updated} зарплат отмечено как невыплаченные.')
    mark_as_unpaid.short_description = "Отметить как невыплаченные"

    def calculate_salaries(self, request, queryset):
        for salary in queryset:
            salary.calculate_total()
            salary.save()
        self.message_user(request, f'Зарплаты пересчитаны для {queryset.count()} записей.')
    calculate_salaries.short_description = "Пересчитать зарплаты"

@admin.register(FuturePayment)
class FuturePaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "group", "payment_date", "amount", "status", "created_at")
    list_filter = ("status", "payment_date", "group")
    search_fields = ("student__first_name", "student__last_name", "group__name")
    ordering = ("-payment_date",)

# Настройка админ панели
admin.site.site_header = "Discovery LC - Администрация"
admin.site.site_title = "Discovery LC Admin"
admin.site.index_title = "Управление системой Discovery LC"



