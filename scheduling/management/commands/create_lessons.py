from django.core.management.base import BaseCommand
from scheduling.models import Schedule, Lesson
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Создает уроки для всех активных расписаний'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Количество дней вперед для создания уроков (по умолчанию 30)'
        )
        
        parser.add_argument(
            '--schedule-id',
            type=int,
            help='ID конкретного расписания (если нужно создать для одного)'
        )
        
        parser.add_argument(
            '--group-name',
            type=str,
            help='Название группы для создания уроков'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        schedule_id = options.get('schedule_id')
        group_name = options.get('group_name')
        
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        
        # Определяем какие расписания обрабатывать
        if schedule_id:
            schedules = Schedule.objects.filter(id=schedule_id, is_active=True)
            if not schedules.exists():
                self.stdout.write(
                    self.style.ERROR(f'Расписание с ID {schedule_id} не найдено или неактивно')
                )
                return
        elif group_name:
            schedules = Schedule.objects.filter(
                group__name__icontains=group_name, 
                is_active=True
            )
            if not schedules.exists():
                self.stdout.write(
                    self.style.ERROR(f'Активные расписания для группы "{group_name}" не найдены')
                )
                return
        else:
            schedules = Schedule.objects.filter(is_active=True)
        
        if not schedules.exists():
            self.stdout.write(
                self.style.WARNING('Не найдено активных расписаний')
            )
            return
        
        total_created = 0
        
        self.stdout.write(f'Создание уроков с {start_date} по {end_date}')
        self.stdout.write(f'Найдено {schedules.count()} активных расписаний')
        
        for schedule in schedules:
            try:
                lessons = schedule.create_lessons_for_period(start_date, end_date)
                created_count = len(lessons)
                total_created += created_count
                
                if created_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Группа "{schedule.group.name}" - создано {created_count} уроков'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'• Группа "{schedule.group.name}" - уроки уже существуют'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Ошибка для группы "{schedule.group.name}": {str(e)}'
                    )
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 ИТОГО СОЗДАНО: {total_created} уроков'
            )
        )
        
        # Показываем статистику
        self.show_statistics()
    
    def show_statistics(self):
        """Показывает статистику по урокам"""
        today = date.today()
        
        # Статистика по урокам
        total_lessons = Lesson.objects.count()
        future_lessons = Lesson.objects.filter(date__gte=today).count()
        past_lessons = Lesson.objects.filter(date__lt=today).count()
        conducted_lessons = Lesson.objects.filter(is_conducted=True).count()
        canceled_lessons = Lesson.objects.filter(is_canceled=True).count()
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('📊 СТАТИСТИКА:'))
        self.stdout.write(f'   Всего уроков: {total_lessons}')
        self.stdout.write(f'   Будущих уроков: {future_lessons}')
        self.stdout.write(f'   Прошедших уроков: {past_lessons}')
        self.stdout.write(f'   Проведенных уроков: {conducted_lessons}')
        self.stdout.write(f'   Отмененных уроков: {canceled_lessons}')
