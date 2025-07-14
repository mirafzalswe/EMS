from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Group, Course
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates 10 test students and enrolls them in a group'

    def handle(self, *args, **kwargs):
        # Test student data
        students_data = [
            {'first_name': 'John', 'last_name': 'Smith', 'email': 'john.smith@example.com'},
            {'first_name': 'Emma', 'last_name': 'Johnson', 'email': 'emma.johnson@example.com'},
            {'first_name': 'Michael', 'last_name': 'Williams', 'email': 'michael.williams@example.com'},
            {'first_name': 'Sophia', 'last_name': 'Brown', 'email': 'sophia.brown@example.com'},
            {'first_name': 'William', 'last_name': 'Jones', 'email': 'william.jones@example.com'},
            {'first_name': 'Olivia', 'last_name': 'Garcia', 'email': 'olivia.garcia@example.com'},
            {'first_name': 'James', 'last_name': 'Miller', 'email': 'james.miller@example.com'},
            {'first_name': 'Ava', 'last_name': 'Davis', 'email': 'ava.davis@example.com'},
            {'first_name': 'Alexander', 'last_name': 'Rodriguez', 'email': 'alexander.rodriguez@example.com'},
            {'first_name': 'Isabella', 'last_name': 'Martinez', 'email': 'isabella.martinez@example.com'},
        ]

        group = Group.objects.first()
        if not group:
            self.stdout.write(self.style.ERROR('No groups found. Please create a group first.'))
            return

        created_count = 0
        for student_data in students_data:
            username = student_data['email'].split('@')[0]
            
            # Create user if doesn't exist
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': student_data['email'],
                    'first_name': student_data['first_name'],
                    'last_name': student_data['last_name'],
                    'user_type': 'student',
                    'is_active': True
                }
            )
            
            if created:
                # Set password for new user
                user.set_password('testpass123')
                user.save()
                created_count += 1

                # Enroll student in the group
                from courses.models import Enrollment
                Enrollment.objects.get_or_create(
                    student=user,
                    group=group,
                    defaults={
                        'enrollment_date': timezone.now().date(),
                        'is_active': True
                    }
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} students and enrolled them in group {group.name}'
            )
        ) 