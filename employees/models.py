from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class EmployeeManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, specialty=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, specialty=specialty, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, specialty=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        return self.create_user(email, full_name, password, **extra_fields)

class Employee(AbstractBaseUser):
    ROLE_CHOICES = [
        ('doctor', 'Врач'),
        ('registry', 'Регистратор'),
        ('lab_tech', 'Лаборант / Диагност'),
        ('admin', 'Администратор'),
        ('medcore_admin', 'MedCore Admin'),
    ]

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    specialty = models.CharField(max_length=100, blank=True, null=True)
    hospital_branch = models.CharField(max_length=255, blank=True, null=True)
    hospital_id = models.IntegerField(blank=True, null=True, verbose_name="ID Больницы (из Global DB)")
    
    SHIFT_CHOICES = [
        ('morning', '08:00–13:00'),
        ('evening', '13:00–18:00'),
    ]
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='morning')
    work_schedule = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = EmployeeManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role']

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"

    @property
    def is_staff(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

class AuditLog(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    patient_identifier = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.employee.full_name}: {self.action}"
