import os
import django
import sys

# Setup django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_system.settings')
django.setup()

from employees.models import Employee
from patients.models import Patient

# Delete Demo Employees from prod (employees.sqlite3)
demo_emails = ['doctor@hospital.uz', 'registry@hospital.uz', 'admin@hospital.uz', 'mixil@hospital.uz']
deleted_employees = Employee.objects.using('employees_db').filter(email__in=demo_emails).delete()
print(f"Deleted {deleted_employees[0]} demo employees from PROD.")

# Delete Demo Patients from prod (db.sqlite3)
# We can find them by checking if they were loaded via fixtures initially,
# or we can delete patients with known demo PINFLs.
# Let's check which patients have the demo PINFLs.
demo_pinfls = [
    '12345678901234', # Ivanov
    '33333333333333',
    '44444444444444',
    '55555555555555',
    '98765432109876'
]
deleted_patients = Patient.objects.using('default').filter(pinfl__in=demo_pinfls).delete()
print(f"Deleted {deleted_patients[0]} demo patients from PROD.")

print("Prod DBs have been cleaned of demo accounts.")
