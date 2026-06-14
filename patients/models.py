from django.db import models
from django.utils import timezone

class Hospital(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название больницы")
    address = models.CharField(max_length=500, blank=True, null=True, verbose_name="Адрес")
    api_key = models.CharField(max_length=100, unique=True, verbose_name="Ключ доступа (API)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class ProcessingLog(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Больница")
    employee_name = models.CharField(max_length=255, verbose_name="Имя сотрудника")
    employee_role = models.CharField(max_length=50, verbose_name="Роль сотрудника")
    patient_pinfl = models.CharField(max_length=14, verbose_name="ПИНФЛ Пациента")
    action = models.CharField(max_length=255, verbose_name="Действие")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        hospital_name = self.hospital.name if self.hospital else 'Система'
        return f"{self.timestamp} | {hospital_name} | {self.action}"

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]
    BLOOD_GROUP_CHOICES = [
        ('O(I)', 'O(I)'),
        ('A(II)', 'A(II)'),
        ('B(III)', 'B(III)'),
        ('AB(IV)', 'AB(IV)'),
    ]
    RH_CHOICES = [
        ('+', 'Rh+'),
        ('-', 'Rh-'),
    ]

    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, related_name='patients', null=True, blank=True, verbose_name="Прикреплен к больнице")
    pinfl = models.CharField(max_length=14, unique=True, verbose_name="ПИНФЛ")
    passport = models.CharField(max_length=20, unique=True, verbose_name="Серия и номер паспорта")
    full_name = models.CharField(max_length=255, verbose_name="ФИО пациента")
    birth_date = models.DateField(verbose_name="Дата рождения")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Пол")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Номер телефона")
    
    blood_group = models.CharField(max_length=10, choices=BLOOD_GROUP_CHOICES, verbose_name="Группа крови", blank=True, null=True)
    rh_factor = models.CharField(max_length=1, choices=RH_CHOICES, verbose_name="Резус-фактор", blank=True, null=True)
    height = models.PositiveIntegerField(verbose_name="Рост (см)", blank=True, null=True)
    weight = models.PositiveIntegerField(verbose_name="Вес (кг)", blank=True, null=True)
    allergies = models.TextField(verbose_name="Аллергии", blank=True, null=True)
    chronic_diseases = models.TextField(verbose_name="Хронические/Врожденные заболевания", blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.pinfl})"


class EncryptedMedicalRecord(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, related_name='records', null=True, blank=True, verbose_name="Больница")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor_id = models.IntegerField(verbose_name="ID Врача (Local DB)")
    doctor_name = models.CharField(max_length=255, verbose_name="ФИО Врача")
    
    disease_name = models.CharField(max_length=255, verbose_name="Название болезни")
    
    # Сюда будет сохраняться зашифрованный Fernet payload (Симптомы, Диагноз, Анализы, Назначение)
    encrypted_payload = models.BinaryField(verbose_name="Зашифрованные медицинские данные")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Record for {self.patient.full_name} - {self.disease_name}"


class LabTest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Не начал'),
        ('in_progress', 'Ведется работа'),
        ('completed', 'Работа сделана'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_tests', verbose_name="Пациент")
    record = models.ForeignKey(EncryptedMedicalRecord, on_delete=models.CASCADE, related_name='lab_tests', verbose_name="Связанная запись")
    
    test_name = models.CharField(max_length=255, verbose_name="Название исследования")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    
    # Ссылка на лаборанта (хранится просто как ID, так как сотрудники в другой БД)
    lab_tech_id = models.IntegerField(blank=True, null=True, verbose_name="ID Лаборанта/Врача")
    lab_tech_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="ФИО Лаборанта")
    
    report = models.TextField(blank=True, null=True, verbose_name="Отчет/Заключение")
    result_data = models.JSONField(blank=True, null=True, verbose_name="Структурированные результаты")
    # Для загрузки снимков. Требует pillow и настроек MEDIA в settings.py
    image = models.ImageField(upload_to='lab_images/', blank=True, null=True, verbose_name="Снимок/Фотография")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.test_name} - {self.patient.full_name} ({self.get_status_display()})"

class PatientAuditLog(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.patient.full_name}: {self.action}"
