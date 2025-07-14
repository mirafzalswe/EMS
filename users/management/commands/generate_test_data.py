from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, time
import random
from faker import Faker
import uuid

from schools.models import School, Branch, Classroom, SchoolStaffAssignment
from courses.models import Subject, Course, Group, Enrollment, LearningMaterial
from scheduling.models import Schedule, Lesson, Event
from assignments.models import Assignment, Submission
from attendance.models import Attendance
from communication.models import Message, Announcement, ChatGroup

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Generates test data for all models'

    def generate_unique_username(self, base):
        """Generate a unique username by appending a UUID4 suffix"""
        return f"{base}_{str(uuid.uuid4())[:8]}"

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting test data generation...')
        
        # Create School
        school = School.objects.create(
            name="EduCenter Prime",
            description="Ведущий образовательный центр",
            address="ул. Главная, 1",
            phone="+998901234567",
            email="info@educenter.uz",
            website="https://educenter.uz"
        )
        
        # Create Branches
        branches = []
        for i in range(5):
            branch = Branch.objects.create(
                school=school,
                name=f"Филиал {i+1}",
                address=fake.address(),
                phone=fake.phone_number(),
                email=f"branch{i+1}@educenter.uz"
            )
            branches.append(branch)
        
        # Create Classrooms
        classrooms = []
        for branch in branches:
            for i in range(4):
                classroom = Classroom.objects.create(
                    branch=branch,
                    name=f"Кабинет {i+1}",
                    capacity=random.randint(15, 30),
                    description=f"Кабинет для занятий #{i+1}"
                )
                classrooms.append(classroom)
        
        # Create Subjects
        subjects = []
        subject_names = ['Математика', 'Физика', 'Химия', 'Биология', 'История', 
                        'Английский язык', 'Программирование', 'Литература']
        for subject_name in subject_names:
            subject = Subject.objects.create(
                name=subject_name,
                description=f"Изучение предмета {subject_name}",
                school=school
            )
            subjects.append(subject)
        
        # Create Courses
        courses = []
        for subject in subjects:
            for level in ['Начальный', 'Средний', 'Продвинутый']:
                course = Course.objects.create(
                    name=f"{subject.name} - {level} уровень",
                    subject=subject,
                    description=f"{level} курс по предмету {subject.name}",
                    price=random.randint(500000, 2000000),
                    duration=random.randint(30, 120),
                    duration_type=random.choice(['hours', 'days', 'weeks'])
                )
                course.available_branches.set(random.sample(branches, random.randint(1, len(branches))))
                courses.append(course)
        
        # Create Teachers
        teachers = []
        for i in range(20):
            username = self.generate_unique_username('teacher')
            teacher = User.objects.create(
                username=username,
                email=f"{username}@educenter.uz",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                user_type='teacher',
                is_active=True
            )
            teacher.set_password('testpass123')
            teacher.save()
            teachers.append(teacher)
        
        # Create Groups
        groups = []
        for course in courses:
            for i in range(2):
                teacher = random.choice(teachers)
                branch = random.choice(course.available_branches.all())
                start_date = timezone.now().date() + timedelta(days=random.randint(-30, 30))
                
                group = Group.objects.create(
                    name=f"Группа {course.name} #{i+1}",
                    course=course,
                    branch=branch,
                    teacher=teacher,
                    start_date=start_date,
                    end_date=start_date + timedelta(days=90),
                    max_students=random.randint(10, 20),
                    is_active=True
                )
                groups.append(group)
        
        # Create Students and Enrollments
        students = []
        for i in range(100):
            username = self.generate_unique_username('student')
            student = User.objects.create(
                username=username,
                email=f"{username}@example.com",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                user_type='student',
                is_active=True
            )
            student.set_password('testpass123')
            student.save()
            students.append(student)
            
            # Enroll student in 1-3 random groups
            for group in random.sample(groups, random.randint(1, 3)):
                if group.students_count < group.max_students:
                    Enrollment.objects.create(
                        student=student,
                        group=group,
                        enrollment_date=timezone.now().date(),
                        is_active=True
                    )
        
        # Create Schedules
        schedules = []
        weekdays = {
            0: 'Понедельник',
            1: 'Вторник',
            2: 'Среда',
            3: 'Четверг',
            4: 'Пятница',
            5: 'Суббота',
            6: 'Воскресенье'
        }
        
        time_slots = [
            (time(9, 0), time(10, 30)),  # 1 пара
            (time(10, 45), time(12, 15)),  # 2 пара
            (time(13, 0), time(14, 30)),  # 3 пара
            (time(14, 45), time(16, 15)),  # 4 пара
            (time(16, 30), time(18, 0))   # 5 пара
        ]

        for group in groups:
            # Создаем расписание на 3 дня в неделю
            days = random.sample(range(0, 5), 3)  # Выбираем 3 случайных дня с понедельника по пятницу
            for day in days:
                # Выбираем 2-3 пары в день
                slots = random.sample(time_slots, random.randint(2, 3))
                for start_time, end_time in slots:
                    schedule = Schedule.objects.create(
                        group=group,
                        classroom=random.choice(classrooms),
                        day_of_week=day,
                        start_time=start_time,
                        end_time=end_time,
                        is_active=True
                    )
                    schedules.append(schedule)

        # Create Lessons
        lessons = []
        current_date = timezone.now().date()
        end_date = current_date + timedelta(days=30)  # Создаем занятия на месяц вперед

        while current_date <= end_date:
            for schedule in schedules:
                if current_date.weekday() == schedule.day_of_week:
                    # Создаем занятие только если это правильный день недели
                    lesson = Lesson.objects.create(
                        schedule=schedule,
                        date=current_date,
                        start_time=schedule.start_time,
                        end_time=schedule.end_time,
                        topic=f"Тема занятия: {fake.sentence()}",
                        description=f"Описание занятия:\n{fake.text()}",
                        is_conducted=current_date < timezone.now().date(),
                        conducted_by=schedule.group.teacher if current_date < timezone.now().date() else None,
                        canceled=random.random() < 0.1,  # 10% шанс отмены
                        cancellation_reason=fake.text() if random.random() < 0.1 else ''
                    )
                    lessons.append(lesson)
            current_date += timedelta(days=1)

        # Create Events
        events = []
        for _ in range(20):
            start_datetime = timezone.now() + timedelta(days=random.randint(-7, 30))
            event = Event.objects.create(
                title=fake.sentence(),
                description=fake.text(),
                start_datetime=start_datetime,
                end_datetime=start_datetime + timedelta(hours=random.randint(1, 4)),
                location=fake.address(),
                created_by=random.choice(teachers),
                is_public=random.choice([True, False])
            )
            participants = random.sample(teachers + students, random.randint(3, 10))
            event.participants.set(participants)
            events.append(event)
        
        # Create Assignments
        for group in groups:
            lessons = Lesson.objects.filter(schedule__group=group)
            for lesson in random.sample(list(lessons), min(5, lessons.count())):
                assignment = Assignment.objects.create(
                    title=fake.sentence(),
                    description=fake.text(),
                    group=group,
                    lesson=lesson,
                    due_date=lesson.date + timedelta(days=7),
                    max_points=100,
                    status='published',
                    created_by=group.teacher
                )
                
                # Create submissions for this assignment
                for enrollment in group.enrollments.all():
                    if random.random() > 0.3:  # 70% chance of submission
                        Submission.objects.create(
                            assignment=assignment,
                            student=enrollment.student,
                            content=fake.text(),
                            points=random.randint(60, 100),
                            feedback=fake.text(),
                            submitted_at=timezone.now() - timedelta(days=random.randint(1, 5))
                        )
        
        # Create Attendance Records
        for lesson in Lesson.objects.filter(date__lt=timezone.now().date()):
            for enrollment in lesson.schedule.group.enrollments.all():
                Attendance.objects.create(
                    student=enrollment.student,
                    lesson=lesson,
                    status=random.choice(['present', 'absent', 'late']),
                    marked_by=lesson.schedule.group.teacher,
                    marked_at=lesson.date
                )
        
        # Create Messages and Announcements
        for group in groups:
            # Create group announcement
            message = Message.objects.create(
                sender=group.teacher,
                subject=fake.sentence(),
                content=fake.text(),
                message_type='announcement',
                group=group
            )
            
            Announcement.objects.create(
                message=message,
                expires_at=timezone.now() + timedelta(days=30),
                is_pinned=random.choice([True, False])
            )
            
            # Add recipients
            for enrollment in group.enrollments.all():
                message.recipients.add(enrollment.student)
        
        # Create Chat Groups
        for branch in branches:
            chat_group = ChatGroup.objects.create(
                name=f"Общий чат {branch.name}",
                description="Общий чат для обсуждений",
                created_by=random.choice(teachers),
                school=school
            )
            # Add random members
            members = random.sample(teachers + students, random.randint(5, 20))
            chat_group.members.set(members)
        
        self.stdout.write(self.style.SUCCESS('Successfully generated test data')) 