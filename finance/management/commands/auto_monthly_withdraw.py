from django.core.management.base import BaseCommand
from django.utils import timezone
from finance.models import StudentFinanceManager
from users.models import User
from courses.models import Enrollment


class Command(BaseCommand):
    help = 'Автоматически списывает стоимость курса у студентов, которые не оплатили за текущий месяц'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, что будет сделано, без выполнения действий',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Режим предварительного просмотра - изменения не будут сохранены')
            )
        
        today = timezone.now().date()
        self.stdout.write(f'Выполняется автосписание на {today.strftime("%d.%m.%Y")}')
        
        # Получаем всех активных студентов
        students = User.objects.filter(user_type='student')
        processed_count = 0
        skipped_count = 0
        
        for student in students:
            enrollments = Enrollment.objects.filter(student=student, is_active=True)
            
            for enrollment in enrollments:
                course = enrollment.group.course
                
                # Проверяем, был ли платёж за этот месяц
                month_start = today.replace(day=1)
                paid_this_month = StudentFinanceManager.get_payment_history(student).filter(
                    payment_date__gte=month_start,
                    amount__gt=0  # Только положительные платежи
                ).exists()
                
                if not paid_this_month:
                    if dry_run:
                        self.stdout.write(
                            f'Будет списано: {student.get_full_name()} - {course.name} - {course.price} сум'
                        )
                    else:
                        try:
                            payment = StudentFinanceManager.manual_withdraw(
                                student=student,
                                amount=course.price,
                                admin_user=None,
                                note=f"Автоматическое списание за {today.strftime('%B %Y')}"
                            )
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Списано: {student.get_full_name()} - {course.name} - {course.price} сум'
                                )
                            )
                            processed_count += 1
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'Ошибка при списании для {student.get_full_name()}: {str(e)}'
                                )
                            )
                else:
                    if dry_run:
                        self.stdout.write(
                            f'Пропущено: {student.get_full_name()} - {course.name} (уже оплачено)'
                        )
                    skipped_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Предварительный просмотр завершен. Будет обработано: {processed_count}, пропущено: {skipped_count}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Автосписание завершено. Обработано: {processed_count}, пропущено: {skipped_count}'
                )
            ) 