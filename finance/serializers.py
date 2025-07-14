from rest_framework import serializers
from django.utils import timezone
from schools.serializers import SchoolSerializer, BranchSerializer
from courses.serializers import CourseSerializer, GroupSerializer
from users.serializers import UserSerializer
from .models import (
    Price, Discount, Invoice, InvoiceItem, Payment,
    ExpenseCategory, Expense, TeacherSalary,
    Currency, PaymentStatus, PaymentMethod, InvoiceStatus,
    PriceType, FuturePayment
)
from users.models import User
from courses.models import Group

class PriceSerializer(serializers.ModelSerializer):
    """
    Сериализатор для цен.
    """
    school_details = SchoolSerializer(source='school', read_only=True)
    course_details = CourseSerializer(source='course', read_only=True)
    
    class Meta:
        model = Price
        fields = [
            'id', 'school', 'school_details', 'course', 'course_details',
            'amount', 'currency', 'price_type', 'is_active', 'effective_from',
            'effective_to', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """
        Проверяем корректность дат действия цены.
        """
        effective_from = data.get('effective_from')
        effective_to = data.get('effective_to')
        
        if effective_from and effective_to and effective_from > effective_to:
            raise serializers.ValidationError(
                "Дата начала действия не может быть позже даты окончания"
            )
        
        return data

class DiscountSerializer(serializers.ModelSerializer):
    """
    Сериализатор для скидок.
    """
    school_details = SchoolSerializer(source='school', read_only=True)
    applies_to_courses_details = CourseSerializer(
        source='applies_to_courses',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = Discount
        fields = [
            'id', 'school', 'school_details', 'name', 'percentage',
            'amount', 'currency', 'code', 'is_active', 'valid_from',
            'valid_to', 'max_uses', 'current_uses', 'applies_to_courses',
            'applies_to_courses_details', 'description', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['current_uses', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Проверяем корректность данных скидки.
        """
        percentage = data.get('percentage')
        amount = data.get('amount')
        
        if not percentage and not amount:
            raise serializers.ValidationError(
                "Необходимо указать либо процент скидки, либо фиксированную сумму"
            )
        
        if percentage and amount:
            raise serializers.ValidationError(
                "Можно указать только процент скидки или фиксированную сумму, но не оба значения"
            )
        
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')
        
        if valid_from and valid_to and valid_from > valid_to:
            raise serializers.ValidationError(
                "Дата начала действия не может быть позже даты окончания"
            )
        
        return data

class InvoiceItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для позиций счета.
    """
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'invoice', 'description', 'quantity', 'unit_price',
            'discount_percentage', 'discount_amount', 'total'
        ]
    
    def validate(self, data):
        """
        Проверяем корректность данных позиции.
        """
        discount_percentage = data.get('discount_percentage')
        discount_amount = data.get('discount_amount')
        
        if discount_percentage and discount_amount:
            raise serializers.ValidationError(
                "Можно указать только процент скидки или фиксированную сумму, но не оба значения"
            )
        
        return data

class InvoiceSerializer(serializers.ModelSerializer):
    """
    Сериализатор для счетов.
    """
    school_details = SchoolSerializer(source='school', read_only=True)
    branch_details = BranchSerializer(source='branch', read_only=True)
    student_details = UserSerializer(source='student', read_only=True)
    course_details = CourseSerializer(source='course', read_only=True)
    group_details = GroupSerializer(source='group', read_only=True)
    discount_details = DiscountSerializer(source='discount', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    balance = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'school', 'school_details', 'branch',
            'branch_details', 'student', 'student_details', 'course',
            'course_details', 'group', 'group_details', 'total_amount',
            'paid_amount', 'balance', 'currency', 'status', 'issue_date',
            'due_date', 'description', 'discount', 'discount_details',
            'discount_amount', 'created_by', 'created_by_details', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'invoice_number', 'paid_amount', 'created_at', 'updated_at'
        ]
    
    def get_balance(self, obj):
        """
        Вычисляет остаток к оплате.
        """
        return obj.calculate_balance()
    
    def validate(self, data):
        """
        Проверяем корректность данных счета.
        """
        issue_date = data.get('issue_date')
        due_date = data.get('due_date')
        
        if issue_date and due_date and issue_date > due_date:
            raise serializers.ValidationError(
                "Дата выставления не может быть позже срока оплаты"
            )
        
        return data

class PaymentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для платежей.
    """
    invoice_details = InvoiceSerializer(source='invoice', read_only=True)
    processed_by_details = UserSerializer(source='processed_by', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'invoice', 'invoice_details', 'amount',
            'currency', 'payment_date', 'payment_method', 'status',
            'transaction_id', 'receipt_number', 'receipt_file', 'notes',
            'processed_by', 'processed_by_details', 'created_by',
            'created_by_details', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'payment_number', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """
        Проверяем корректность данных платежа.
        """
        invoice = data.get('invoice')
        amount = data.get('amount')
        
        if invoice and amount:
            if amount > invoice.calculate_balance():
                raise serializers.ValidationError(
                    "Сумма платежа не может превышать остаток по счету"
                )
        
        return data

class ExpenseCategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для категорий расходов.
    """
    school_details = SchoolSerializer(source='school', read_only=True)
    
    class Meta:
        model = ExpenseCategory
        fields = [
            'id', 'school', 'school_details', 'name', 'description',
            'is_active'
        ]

class ExpenseSerializer(serializers.ModelSerializer):
    """
    Сериализатор для расходов.
    """
    school_details = SchoolSerializer(source='school', read_only=True)
    branch_details = BranchSerializer(source='branch', read_only=True)
    category_details = ExpenseCategorySerializer(source='category', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    approved_by_details = UserSerializer(source='approved_by', read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'school', 'school_details', 'branch', 'branch_details',
            'category', 'category_details', 'description', 'amount',
            'currency', 'expense_date', 'receipt_file', 'notes',
            'created_by', 'created_by_details', 'approved_by',
            'approved_by_details', 'is_approved', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class TeacherSalarySerializer(serializers.ModelSerializer):
    """
    Сериализатор для зарплат преподавателей.
    """
    teacher_details = UserSerializer(source='teacher', read_only=True)
    school_details = SchoolSerializer(source='school', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = TeacherSalary
        fields = [
            'id', 'teacher', 'teacher_details', 'school', 'school_details',
            'period_start', 'period_end', 'base_salary', 'lesson_bonus',
            'performance_bonus', 'other_bonuses', 'deductions',
            'total_salary', 'currency', 'is_paid', 'payment_date',
            'notes', 'created_by', 'created_by_details', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['total_salary', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Проверяем корректность данных зарплаты.
        """
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        
        if period_start and period_end and period_start > period_end:
            raise serializers.ValidationError(
                "Дата начала периода не может быть позже даты окончания"
            )
        
        return data

class FuturePaymentSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = FuturePayment
        fields = [
            'id', 'student', 'student_name', 'group', 'group_name',
            'payment_date', 'amount', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at'] 