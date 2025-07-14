from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from courses.models import Group
from scheduling.models import Lesson
from assignments.models import Assignment, Submission, AssignmentStatus

User = get_user_model()

class Command(BaseCommand):
    help = 'Loads sample data for assignments and submissions'

    def handle(self, *args, **kwargs):
        # Get or create sample users
        teacher = User.objects.filter(is_teacher=True).first()
        if not teacher:
            teacher = User.objects.create_user(
                username='sample_teacher',
                email='teacher@example.com',
                password='password123',
                is_teacher=True
            )

        # Get or create a group
        group = Group.objects.first()
        if not group:
            group = Group.objects.create(
                name='Sample Group',
                description='A sample group for testing'
            )

        # Get or create a lesson
        lesson = Lesson.objects.first()
        if not lesson:
            lesson = Lesson.objects.create(
                title='Sample Lesson',
                description='A sample lesson for testing',
                group=group
            )

        # Create sample assignments
        assignments = []
        for i in range(1, 6):
            assignment = Assignment.objects.create(
                title=f'Sample Assignment {i}',
                description=f'This is a sample assignment #{i} for testing purposes.',
                group=group,
                lesson=lesson,
                due_date=timezone.now() + timezone.timedelta(days=i*7),
                max_points=100,
                status=AssignmentStatus.PUBLISHED,
                created_by=teacher
            )
            assignments.append(assignment)
            self.stdout.write(self.style.SUCCESS(f'Created assignment: {assignment.title}'))

        # Create sample students
        students = []
        for i in range(1, 4):
            student = User.objects.create_user(
                username=f'sample_student{i}',
                email=f'student{i}@example.com',
                password='password123',
                is_student=True
            )
            students.append(student)
            self.stdout.write(self.style.SUCCESS(f'Created student: {student.username}'))

        # Create sample submissions
        for assignment in assignments:
            for student in students:
                submission = Submission.objects.create(
                    assignment=assignment,
                    student=student,
                    content=f'This is a sample submission for {assignment.title} by {student.username}',
                    points=80 if student.username == 'sample_student1' else None,
                    feedback='Good work!' if student.username == 'sample_student1' else '',
                    graded_by=teacher if student.username == 'sample_student1' else None,
                    graded_at=timezone.now() if student.username == 'sample_student1' else None
                )
                self.stdout.write(self.style.SUCCESS(f'Created submission: {submission}'))

        self.stdout.write(self.style.SUCCESS('Successfully loaded sample data')) 