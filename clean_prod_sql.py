import sqlite3

# Delete Demo Employees from prod (employees.sqlite3)
demo_emails = ['doctor@hospital.uz', 'registry@hospital.uz', 'admin@hospital.uz', 'mixil@hospital.uz']
conn_emp = sqlite3.connect('employees.sqlite3')
cur_emp = conn_emp.cursor()
placeholders = ', '.join(['?'] * len(demo_emails))
cur_emp.execute(f"DELETE FROM employees_employee WHERE email IN ({placeholders})", demo_emails)
deleted_emp = cur_emp.rowcount
conn_emp.commit()
conn_emp.close()
print(f"Deleted {deleted_emp} demo employees from PROD.")

# Delete Demo Patients from prod (db.sqlite3)
demo_pinfls = [
    '12345678901234', # Ivanov
    '33333333333333',
    '44444444444444',
    '55555555555555',
    '98765432109876'
]
conn_db = sqlite3.connect('db.sqlite3')
cur_db = conn_db.cursor()
placeholders_db = ', '.join(['?'] * len(demo_pinfls))
cur_db.execute(f"DELETE FROM patients_patient WHERE pinfl IN ({placeholders_db})", demo_pinfls)
deleted_pat = cur_db.rowcount
conn_db.commit()
conn_db.close()
print(f"Deleted {deleted_pat} demo patients from PROD.")

print("Prod DBs have been cleaned of demo accounts via sqlite3.")
