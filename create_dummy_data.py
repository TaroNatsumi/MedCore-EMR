import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_system.settings')
django.setup()

from employees.models import Employee
from patients.models import Patient

def create_data():
    print("Создание тестовых данных...")
    
    # Врач
    if not Employee.objects.using('employees_db').filter(email='doctor@hospital.uz').exists():
        Employee.objects.db_manager('employees_db').create_user(
            email='doctor@hospital.uz',
            full_name='Смирнова О.П.',
            role='doctor',
            password='password123',
            hospital_branch='Ташкент (ГКБ №1)'
        )
        print("- Врач создан (doctor@hospital.uz / password123)")

    # Регистратор
    if not Employee.objects.using('employees_db').filter(email='registry@hospital.uz').exists():
        Employee.objects.db_manager('employees_db').create_user(
            email='registry@hospital.uz',
            full_name='Иванова А.А.',
            role='registry',
            password='password123',
            hospital_branch='Ташкент (ГКБ №1)'
        )
        print("- Регистратор создан (registry@hospital.uz / password123)")

    # Админ
    if not Employee.objects.using('employees_db').filter(email='admin@hospital.uz').exists():
        Employee.objects.db_manager('employees_db').create_superuser(
            email='admin@hospital.uz',
            full_name='Попова А. А.',
            role='admin',
            password='password123',
            hospital_branch='Ташкент (ГКБ №1)'
        )
        print("- Админ создан (admin@hospital.uz / password123)")

    # Пациент
    if not Patient.objects.using('default').filter(pinfl='12345678901234').exists():
        Patient.objects.using('default').create(
            pinfl='12345678901234',
            passport='AA1234567',
            full_name='Иванов Иван Иванович',
            birth_date='1990-01-01',
            gender='M',
            blood_group='O(I)',
            rh_factor='+',
            height=180,
            weight=80,
            allergies='Пенициллин, Пыль',
            chronic_diseases='Сахарный диабет 2 типа, Гипертония'
        )
        print("- Пациент создан (Иванов Иван Иванович / ПИНФЛ: 12345678901234)")

if __name__ == '__main__':
    create_data()
    print("Готово!")
