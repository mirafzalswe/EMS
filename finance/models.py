from django.db import models
from django.conf import settings
from django.utils import timezone
from schools.models import School, Branch
from courses.models import Course, Group
from users.models import User
from django.db import transaction
from decimal import Decimal
from django.db.models import Sum

class Currency(models.TextChoices):
    """
    Поддерживаемые валюты.
    """
    RUB = 'RUB', 'Российский рубль'
    USD = 'USD', 'Доллар США'

    UZS = 'UZS', 'Узбекский сум'

class PaymentStatus(models.TextChoices):
    """
    Статусы платежей.
    """
    PENDING = 'pending', 'Ожидает оплаты'
    PROCESSING = 'processing', 'В обработке'
    COMPLETED = 'completed', 'Оплачен'
    FAILED = 'failed', 'Ошибка оплаты'
    REFUNDED = 'refunded', 'Возвращен'
    PARTIALLY_REFUNDED = 'partially_refunded', 'Частично возвращен'
    CANCELLED = 'cancelled', 'Отменен'

class PaymentMethod(models.TextChoices):
    """
    Методы оплаты.
    """
    CASH = 'cash', 'Наличные'
    BANK_TRANSFER = 'bank_transfer', 'Банковский перевод'
    CREDIT_CARD = 'credit_card', 'Кредитная карта'
    ONLINE_PAYMENT = 'online_payment', 'Онлайн оплата'
    CHECK = 'check', 'Чек'
    OTHER = 'other', 'Другое'

class InvoiceStatus(models.TextChoices):
    """
    Статусы счетов.
    """
    DRAFT = 'draft', 'Черновик'
    PENDING = 'pending', 'Ожидает оплаты'
    PARTIALLY_PAID = 'partially_paid', 'Частично оплачен'
    PAID = 'paid', 'Оплачен'
    OVERDUE = 'overdue', 'Просрочен'
    CANCELLED = 'cancelled', 'Отменен'
    REFUNDED = 'refunded', 'Возвращен'

class PriceType(models.TextChoices):
    """
    Типы цен.
    """
    STANDARD = 'standard', 'Стандартная'
    DISCOUNT = 'discount', 'Со скидкой'
    SPECIAL = 'special', 'Специальная'
    PROMOTIONAL = 'promotional', 'Акционная'

class Price(models.Model):
    """
    Модель для хранения цен на курсы, занятия и т.д.
    """
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE,
        related_name='prices',
        verbose_name='Учебный центр'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='prices',
        verbose_name='Курс'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Сумма'
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.RUB,
        verbose_name='Валюта'
    )
    price_type = models.CharField(
        max_length=20,
        choices=PriceType.choices,
        default=PriceType.STANDARD,
        verbose_name='Тип цены'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    # Дополнительные поля для управления ценообразованием
    effective_from = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Действует с'
    )
    effective_to = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Действует до'
    )
    description = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name='Описание'
    )
    
    class Meta:
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'
        unique_together = ['school', 'course', 'price_type', 'effective_from']
    
    def __str__(self):
        return f"{self.course.name} - {self.amount} {self.currency} ({self.get_price_type_display()})"
    
    def is_valid(self):
        """
        Проверяет, действительна ли цена на текущий момент.
        """
        now = timezone.now()
        if not self.is_active:
            return False
        if self.effective_from and self.effective_from > now:
            return False
        if self.effective_to and self.effective_to < now:
            return False
        return True

class Discount(models.Model):
    """
    Модель для хранения скидок.
    """
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE,
        related_name='discounts',
        verbose_name='Учебный центр'
    )
    name = models.CharField(max_length=255, verbose_name='Название')
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Процент скидки'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        verbose_name='Фиксированная сумма скидки'
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.RUB,
        verbose_name='Валюта для фиксированной скидки'
    )
    code = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Промокод'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    valid_from = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Действует с'
    )
    valid_to = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Действует до'
    )
    max_uses = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name='Максимальное количество использований'
    )
    current_uses = models.IntegerField(
        default=0,
        verbose_name='Текущее количество использований'
    )
    applies_to_courses = models.ManyToManyField(
        Course,
        blank=True,
        related_name='applicable_discounts',
        verbose_name='Применяется к курсам'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Скидка'
        verbose_name_plural = 'Скидки'
    
    def __str__(self):
        if self.percentage > 0:
            return f"{self.name} - {self.percentage}%"
        return f"{self.name} - {self.amount} {self.currency}"
    
    def is_valid(self):
        """
        Проверяет, действительна ли скидка на текущий момент.
        """
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and self.valid_from > now:
            return False
        if self.valid_to and self.valid_to < now:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True

class Invoice(models.Model):
    """
    Модель для хранения счетов.
    """
    invoice_number = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='Номер счета'
    )
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name='Учебный центр'
    )
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='invoices',
        verbose_name='Филиал'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name='Студент',
        limit_choices_to={'user_type': 'student'}
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name='Курс'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='invoices',
        verbose_name='Группа'
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Общая сумма'
    )
    paid_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        verbose_name='Оплаченная сумма'
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.RUB,
        verbose_name='Валюта'
    )
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        verbose_name='Статус'
    )
    issue_date = models.DateField(verbose_name='Дата выставления')
    due_date = models.DateField(verbose_name='Срок оплаты')
    description = models.TextField(blank=True, verbose_name='Описание')
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name='invoices',
        verbose_name='Скидка'
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        verbose_name='Сумма скидки'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices',
        verbose_name='Создатель'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Счет'
        verbose_name_plural = 'Счета'
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"Счет #{self.invoice_number} для {self.student.user.full_name}"
    
    def calculate_balance(self):
        """
        Вычисляет остаток к оплате.
        """
        return self.total_amount - self.paid_amount
    
    def update_status(self):
        """
        Обновляет статус счета на основе платежей.
        """
        balance = self.calculate_balance()
        
        if self.status == InvoiceStatus.CANCELLED or self.status == InvoiceStatus.REFUNDED:
            return
        
        if balance <= 0:
            self.status = InvoiceStatus.PAID
        elif self.paid_amount > 0:
            self.status = InvoiceStatus.PARTIALLY_PAID
        elif timezone.now().date() > self.due_date and self.status != InvoiceStatus.DRAFT:
            self.status = InvoiceStatus.OVERDUE
        
        self.save()

class InvoiceItem(models.Model):
    """
    Элемент счета (позиция).
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Счет'
    )
    description = models.CharField(max_length=255, verbose_name='Описание')
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=1,
        verbose_name='Количество'
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Цена за единицу'
    )
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=0,
        verbose_name='Процент скидки'
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        verbose_name='Сумма скидки'
    )
    total = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Итого'
    )
    
    class Meta:
        verbose_name = 'Позиция счета'
        verbose_name_plural = 'Позиции счетов'
    
    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}"
    
    def calculate_total(self):
        """
        Рассчитывает общую сумму позиции с учетом скидки.
        """
        subtotal = self.quantity * self.unit_price
        
        # Расчет суммы скидки (процент или фиксированная сумма)
        if self.discount_percentage > 0:
            discount = subtotal * self.discount_percentage / 100
        else:
            discount = self.discount_amount
            
        return subtotal - discount

class Payment(models.Model):
    """
    Модель для хранения платежей.
    """
    payment_number = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='Номер платежа'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Счет'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Сумма'
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.RUB,
        verbose_name='Валюта'
    )
    payment_date = models.DateField(verbose_name='Дата платежа')
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name='Способ оплаты'
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name='Статус'
    )
    transaction_id = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name='ID транзакции'
    )
    receipt_number = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name='Номер чека'
    )
    receipt_file = models.FileField(
        upload_to='receipts/', 
        null=True, 
        blank=True,
        verbose_name='Файл чека'
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_payments',
        verbose_name='Обработано'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payments',
        verbose_name='Создано'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Платеж #{self.payment_number} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        """
        Обновляем статус счета при изменении платежа.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Если платеж подтвержден, обновляем оплаченную сумму в счете
        if self.status == PaymentStatus.COMPLETED:
            invoice = self.invoice
            if is_new:  # Только для новых платежей
                invoice.paid_amount += self.amount
                invoice.save()
            invoice.update_status()

class ExpenseCategory(models.Model):
    """
    Категории расходов.
    """
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE,
        related_name='expense_categories',
        verbose_name='Учебный центр'
    )
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    
    class Meta:
        verbose_name = 'Категория расходов'
        verbose_name_plural = 'Категории расходов'
        unique_together = ['school', 'name']
    
    def __str__(self):
        return self.name

class Expense(models.Model):
    """
    Модель для хранения расходов.
    """
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name='Учебный центр'
    )
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='expenses',
        verbose_name='Филиал'
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name='Категория'
    )
    description = models.CharField(max_length=255, verbose_name='Описание')
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Сумма'
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.RUB,
        verbose_name='Валюта'
    )
    expense_date = models.DateField(verbose_name='Дата расхода')
    receipt_file = models.FileField(
        upload_to='expense_receipts/', 
        null=True, 
        blank=True,
        verbose_name='Файл чека'
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_expenses',
        verbose_name='Создано'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='approved_expenses',
        verbose_name='Утверждено'
    )
    is_approved = models.BooleanField(default=False, verbose_name='Утверждено')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Расход'
        verbose_name_plural = 'Расходы'
        ordering = ['-expense_date']
    
    def __str__(self):
        return f"{self.description} - {self.amount} {self.currency}"

class TeacherSalary(models.Model):
    """
    Модель для хранения зарплат преподавателей.
    """
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='salaries',
        verbose_name='Преподаватель'
    )
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE,
        related_name='teacher_salaries',
        verbose_name='Учебный центр'
    )
    period_start = models.DateField(verbose_name='Начало периода')
    period_end = models.DateField(verbose_name='Конец периода')
    base_salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Базовая ставка'
    )
    lesson_bonus = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        verbose_name='Бонус за занятия'
    )
    performance_bonus = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        verbose_name='Бонус за результаты'
    )
    other_bonuses = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        verbose_name='Прочие бонусы'
    )
    deductions = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        verbose_name='Удержания'
    )
    total_salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Итоговая зарплата'
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.RUB,
        verbose_name='Валюта'
    )
    is_paid = models.BooleanField(default=False, verbose_name='Оплачено')
    payment_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Дата выплаты'
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_salaries',
        verbose_name='Создано'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Зарплата преподавателя'
        verbose_name_plural = 'Зарплаты преподавателей'
        ordering = ['-period_end']
    
    def __str__(self):
        return f"Зарплата {self.teacher.get_full_name() or self.teacher.username} за период {self.period_start} - {self.period_end}"
    
    def calculate_total(self):
        """
        Рассчитывает итоговую зарплату.
        """
        total = self.base_salary + self.lesson_bonus + self.performance_bonus + self.other_bonuses - self.deductions
        return max(0, total)  # Не может быть отрицательной
    
    def save(self, *args, **kwargs):
        """
        Автоматически рассчитываем итоговую зарплату при сохранении.
        """
        self.total_salary = self.calculate_total()
        super().save(*args, **kwargs)

class StudentFinanceManager:
    """
    Менеджер для работы с финансами студента (расчёт баланса, автосписание, история платежей).
    Используется для User с user_type='student'.
    """
    @staticmethod
    def get_balance(student):
        """
        Возвращает текущий баланс студента (сумма всех платежей минус автосписания за курсы).
        """
        from courses.models import Enrollment
        # Все активные зачисления (группы)
        enrollments = Enrollment.objects.filter(student=student, is_active=True)
        total_due = Decimal('0.00')
        for enrollment in enrollments:
            course = enrollment.group.course
            # Считаем, сколько месяцев студент учится (от даты зачисления до сегодня)
            months = (timezone.now().year - enrollment.enrollment_date.year) * 12 + (timezone.now().month - enrollment.enrollment_date.month) + 1
            total_due += course.price * months
        # Все платежи студента (только успешные)
        payments = Payment.objects.filter(invoice__student=student, status=PaymentStatus.COMPLETED)
        total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        return total_paid - total_due

    @staticmethod
    def get_last_payment(student):
        """
        Возвращает последний платёж студента (или None), учитывая как обычные платежи, так и FuturePayment со статусом 'paid'.
        """
        from django.db.models import Value, CharField, DateField, DecimalField
        from django.db.models.functions import Cast
        # Получаем последний обычный платёж
        last_payment = Payment.objects.filter(invoice__student=student, status=PaymentStatus.COMPLETED).order_by('-payment_date').first()
        # Получаем последний FuturePayment со статусом 'paid'
        last_future = FuturePayment.objects.filter(student=student, status='paid').order_by('-payment_date').first()
        # Сравниваем даты
        if last_payment and last_future:
            if last_payment.payment_date >= last_future.payment_date:
                return last_payment
            else:
                # Приводим FuturePayment к виду Payment-like объекта для отображения
                class FPObj:
                    def __init__(self, fp):
                        self.amount = fp.amount
                        self.payment_date = fp.payment_date
                        self.payment_method = 'future'
                        self.status = 'completed'
                        self.notes = 'FuturePayment'
                        self.id = fp.id
                        self.is_future_payment = True
                    def __str__(self):
                        return f"FuturePayment: {self.amount} {self.payment_date}"
                return FPObj(last_future)
        elif last_payment:
            return last_payment
        elif last_future:
            class FPObj:
                def __init__(self, fp):
                    self.amount = fp.amount
                    self.payment_date = fp.payment_date
                    self.payment_method = 'future'
                    self.status = 'completed'
                    self.notes = 'FuturePayment'
                    self.id = fp.id
                    self.is_future_payment = True
                def __str__(self):
                    return f"FuturePayment: {self.amount} {self.payment_date}"
            return FPObj(last_future)
        else:
            return None

    @staticmethod
    def get_payment_history(student):
        """
        Возвращает QuerySet истории платежей студента.
        """
        return Payment.objects.filter(invoice__student=student).order_by('-payment_date')

    @staticmethod
    def manual_withdraw(student, amount, admin_user, note="Ручное списание админом", payment_method=PaymentMethod.CASH):
        """
        Ручное списание средств с баланса студента (создаёт отрицательный платёж).
        Теперь можно явно указать payment_method.
        """
        with transaction.atomic():
            # Создаём фиктивный invoice для списания
            from courses.models import Course
            invoice = Invoice.objects.create(
                invoice_number=f"MANUAL-{student.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                school=student.enrollments.first().group.course.subject.school if student.enrollments.exists() else None,
                student=student,
                course=student.enrollments.first().group.course if student.enrollments.exists() else None,
                total_amount=amount,
                paid_amount=0,
                currency=Currency.UZS,
                status=InvoiceStatus.PAID,
                issue_date=timezone.now().date(),
                due_date=timezone.now().date(),
                description=note,
                created_by=admin_user
            )
            payment = Payment.objects.create(
                payment_number=f"MANUAL-{student.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                invoice=invoice,
                amount=-abs(amount),
                currency=Currency.UZS,
                payment_date=timezone.now().date(),
                payment_method=payment_method,
                status=PaymentStatus.COMPLETED,
                notes=note,
                processed_by=admin_user,
                created_by=admin_user
            )
            return payment

    @staticmethod
    def auto_monthly_withdraw():
        """
        Автоматически списывает стоимость курса у всех студентов, если наступил новый месяц и не было оплаты.
        Теперь payment_method всегда OTHER (автоматическое списание).
        """
        from courses.models import Enrollment
        today = timezone.now().date()
        for enrollment in Enrollment.objects.filter(is_active=True):
            student = enrollment.student
            course = enrollment.group.course
            # Проверяем, был ли платёж за этот месяц
            month_start = today.replace(day=1)
            paid_this_month = Payment.objects.filter(
                invoice__student=student,
                invoice__course=course,
                payment_date__gte=month_start,
                status=PaymentStatus.COMPLETED
            ).exists()
            if not paid_this_month:
                # Списываем стоимость курса
                StudentFinanceManager.manual_withdraw(
                    student=student,
                    amount=course.price,
                    admin_user=None,
                    note=f"Автоматическое списание за {today.strftime('%B %Y')}",
                    payment_method=PaymentMethod.OTHER
                )

class FuturePayment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает оплаты"),
        ("overdue", "Просрочено"),
        ("paid", "Оплачено"),
    ]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="future_payments")
    group = models.ForeignKey('courses.Group', on_delete=models.CASCADE, related_name="future_payments")
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Будущая оплата"
        verbose_name_plural = "Будущие оплаты"
        ordering = ["payment_date"]

    def __str__(self):
        return f"{self.student} - {self.group} - {self.payment_date} - {self.amount} - {self.get_status_display()}"

class MonthlyIncomeStat(models.Model):
    year = models.IntegerField()
    month = models.IntegerField()
    total_income = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        unique_together = ('year', 'month')
        ordering = ['year', 'month']

    def __str__(self):
        return f'{self.year}-{self.month:02d}: {self.total_income}'
