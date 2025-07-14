# init_data.py

import os
import django
import sys
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import models
from django.contrib.auth import get_user_model
from schools.models import Branch, Classroom
from django.utils import timezone

User = get_user_model()

def create_branch():
    """Create main branch and classrooms"""
    # Create main branch
    main_branch = Branch.objects.create(
        name="EduTrack Main Center",
        address="123 Education Street",
        phone="+998901234567",
        email="main@edutrack.uz",
        branch_type="main",
        opening_time="09:00",
        closing_time="20:00",
        is_active=True
    )
    print(f"Created branch: {main_branch.name}")

    # Create classrooms
    classrooms_data = [
        {
            'name': 'Room 101',
            'capacity': 15,
            'room_type': 'lecture',
            'floor': 1
        },
        {
            'name': 'Computer Lab',
            'capacity': 20,
            'room_type': 'computer',
            'floor': 1
        },
        {
            'name': 'Language Lab',
            'capacity': 12,
            'room_type': 'language',
            'floor': 2
        }
    ]

    for classroom_data in classrooms_data:
        classroom = Classroom.objects.create(
            branch=main_branch,
            **classroom_data
        )
        print(f"Created classroom: {classroom.name}")

    return main_branch

def create_users():
    """Create admins, teachers and students"""
    # Create Admins
    admins_data = [
        {
            'username': 'director',
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'director@edutrack.com',
            'user_type': 'admin',
            'phone': '+998901234567',
            'password': 'admin123'
        },
        {
            'username': 'manager',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'email': 'manager@edutrack.com',
            'user_type': 'admin',
            'phone': '+998901234568',
            'password': 'admin123'
        }
    ]

    # Create Teachers
    teachers_data = [
        {
            'username': 'english_teacher',
            'first_name': 'Michael',
            'last_name': 'Brown',
            'email': 'michael@edutrack.com',
            'user_type': 'teacher',
            'specialization': 'English Language',
            'experience': 5,
            'phone': '+998901234569',
            'password': 'teacher123'
        },
        {
            'username': 'math_teacher',
            'first_name': 'Emma',
            'last_name': 'Wilson',
            'email': 'emma@edutrack.com',
            'user_type': 'teacher',
            'specialization': 'Mathematics',
            'experience': 8,
            'phone': '+998901234570',
            'password': 'teacher123'
        },
        {
            'username': 'programming',
            'first_name': 'David',
            'last_name': 'Lee',
            'email': 'david@edutrack.com',
            'user_type': 'teacher',
            'specialization': 'Programming',
            'experience': 6,
            'phone': '+998901234571',
            'password': 'teacher123'
        }
    ]

    # Create Students
    students_data = [
        {
            'username': 'student1',
            'first_name': 'Alex',
            'last_name': 'Martinez',
            'email': 'alex@student.com',
            'user_type': 'student',
            'birthday': '2005-03-15',
            'phone': '+998901234572',
            'password': 'student123'
        },
        {
            'username': 'student2',
            'first_name': 'Sofia',
            'last_name': 'Garcia',
            'email': 'sofia@student.com',
            'user_type': 'student',
            'birthday': '2004-07-22',
            'phone': '+998901234573',
            'password': 'student123'
        },
        {
            'username': 'student3',
            'first_name': 'James',
            'last_name': 'Wilson',
            'email': 'james@student.com',
            'user_type': 'student',
            'birthday': '2006-01-10',
            'phone': '+998901234574',
            'password': 'student123'
        }
    ]

    # Create all users
    for admin_data in admins_data:
        password = admin_data.pop('password')
        admin = User.objects.create(**admin_data)
        admin.set_password(password)
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        print(f"Created admin: {admin.username}")

    for teacher_data in teachers_data:
        password = teacher_data.pop('password')
        teacher = User.objects.create(**teacher_data)
        teacher.set_password(password)
        teacher.save()
        print(f"Created teacher: {teacher.username}")

    for student_data in students_data:
        password = student_data.pop('password')
        if 'birthday' in student_data:
            student_data['birthday'] = datetime.strptime(student_data['birthday'], '%Y-%m-%d').date()
        student = User.objects.create(**student_data)
        student.set_password(password)
        student.save()
        print(f"Created student: {student.username}")

def init_data():
    """Initialize all data"""
    try:
        print("Starting data initialization...")
        
        # Create branch and classrooms
        branch = create_branch()
        
        # Create users
        create_users()
        
        print("\nData initialization completed successfully!")
        print("\nLogin credentials:")
        print("\nAdmins:")
        print("Username: director, Password: admin123")
        print("Username: manager, Password: admin123")
        print("\nTeachers:")
        print("Username: english_teacher, Password: teacher123")
        print("Username: math_teacher, Password: teacher123")
        print("Username: programming, Password: teacher123")
        print("\nStudents:")
        print("Username: student1, Password: student123")
        print("Username: student2, Password: student123")
        print("Username: student3, Password: student123")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    init_data()