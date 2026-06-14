import os
import django
import sys
import shutil

# Установка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_system.settings')
django.setup()

from patients.models import Hospital, Patient
from employees.models import Employee

def run():
    print("Создание 'Тестовая больница' в demo_db...")
    hospital, created = Hospital.objects.using('demo_default').get_or_create(
        name="Тестовая больница",
        defaults={
            'address': "г. Ташкент, ул. Демонстрационная, 1",
            'api_key': "demo-secret-key-12345"
        }
    )
    print(f"Больница {'создана' if created else 'найдена'}: {hospital.id}")
    
    # Update employees
    print("Обновление филиала у демо-сотрудников...")
    demo_employees = Employee.objects.using('demo_employees_db').all()
    count = 0
    for emp in demo_employees:
        if emp.hospital_id != hospital.id:
            emp.hospital_id = hospital.id
            emp.save(using='demo_employees_db')
            count += 1
    print(f"Обновлено {count} сотрудников.")

    # Delete patients
    print("Удаление пациентов из demo_db...")
    deleted_count, _ = Patient.objects.using('demo_default').all().delete()
    print(f"Удалено {deleted_count} пациентов.")

    # Re-create backups
    print("Обновление бэкапов демо-баз...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    demo_db_path = os.path.join(base_dir, 'demo_db.sqlite3')
    demo_emp_path = os.path.join(base_dir, 'demo_employees.sqlite3')
    
    demo_db_backup = os.path.join(base_dir, 'db_demo_backup.sqlite3')
    demo_emp_backup = os.path.join(base_dir, 'employees_demo_backup.sqlite3')
    
    shutil.copy2(demo_db_path, demo_db_backup)
    shutil.copy2(demo_emp_path, demo_emp_backup)
    
    print("Бэкапы успешно обновлены.")
    print("Готово!")

if __name__ == '__main__':
    run()
