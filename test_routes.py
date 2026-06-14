import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_system.settings')
django.setup()

from django.test import Client

c = Client()
urls_to_test = [
    '/',
    '/prod/',
    '/guide/',
    '/patient/login/',
    '/employee/login/',
    '/employee/hospitals/',
]

for url in urls_to_test:
    response = c.get(url)
    print(f"URL: {url} -> Status: {response.status_code}")
