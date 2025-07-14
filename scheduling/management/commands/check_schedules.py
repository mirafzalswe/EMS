
from django.core.management.base import BaseCommand
from scheduling.models import Schedule, Lesson
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Проверяет расписания и показывает информацию о них'
    
    def handle(self, *args, **options):
        today = date.today()
        
        self.stdout.write(
            self.style.SUCCESS(f'📅 Проверка расписаний на {today}')
        )
        self.stdout.write('')
        
        # Активные расписания
        active_schedulesr = Schedule.objects.filter(is_active=True)
        
        if not active_schedules.exists():
            self.stdout.write(
                self.style.ERROR('❌ Нет активных расписаний!')
            )
            return
        
        self.stdout.write(f'✅ Найдено {active_schedules.count()} активных расписаний:')
        self.stdout.write('')
        
        for schedule in active_schedules:
            # Считаем уроки для каждого расписания
            total_lessons = Lesson.objects.filter(schedule=schedule).count()
            future_lessons = Lesson.objects.filter(
                schedule=schedule, 
                date__gte=today
            ).count()
            
            # Ближайший урок
            next_lesson = Lesson.objects.filter(
                schedule=schedule,
                date__gte=today
            ).order_by('date').first()
            
            # Сегодняшний урок
            today_lesson = Lesson.objects.filter(
                schedule=schedule,
                date=today
            ).first()
            
            self.stdout.write(f'📚 Группа: {schedule.group.name}')
            self.stdout.write(f'   День недели: {schedule.get_day_of_week_display()}')
            self.stdout.write(f'   Время: {schedule.start_time} - {schedule.end_time}')
            self.stdout.write(f'   Аудитория: {schedule.classroom or "Не указана"}')
            self.stdout.write(f'   Всего уроков: {total_lessons}')
            self.stdout.write(f'   Будущих уроков: {future_lessons}')
            
            if today_lesson:
                status = "Проведен" if today_lesson.is_conducted else "Запланирован"
                if today_lesson.is_canceled:
                    status = "Отменен"
                self.stdout.write(f'   🔥 СЕГОДНЯ: {today_lesson.start_time} ({status})')
            else:
                self.stdout.write(f'   📅 Сегодня уроков нет')
            
            if next_lesson:
                self.stdout.write(f'   ⏭️  Следующий урок: {next_lesson.date} {next_lesson.start_time}')
            else:
                self.stdout.write(f'   ⚠️  Нет запланированных уроков!')
            
            self.stdout.write('')