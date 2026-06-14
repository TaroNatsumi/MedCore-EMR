from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from employees.models import Employee, AuditLog
from patients.models import Patient, EncryptedMedicalRecord, LabTest, ProcessingLog, Hospital
from hospital_system.encryption_utils import decrypt_payload

def landing_page(request):
    """
    Информационная Главная Страница (Презентация MedCore).
    """
    return render(request, 'landing.html')

def guide_page(request):
    """
    Страница-инструкция (Статический Демо-тур) с обзором интерфейсов системы.
    """
    return render(request, 'guide.html')

def prod_landing(request):
    """
    Страница Основной системы, где пользователь выбирает свою роль.
    """
    if 'patient_pinfl' in request.session:
        return redirect('patient_dashboard')
        
    if request.user.is_authenticated:
        if request.user.role == 'medcore_admin':
            return redirect('medcore_dashboard')
        elif request.user.role == 'doctor':
            return redirect('doctor_dashboard')
        elif request.user.role == 'registry':
            return redirect('registry_dashboard')
        elif request.user.role == 'lab_tech':
            return redirect('lab_dashboard')
        elif request.user.role == 'admin':
            return redirect('admin_dashboard')
            
    return render(request, 'prod_landing.html')

def patient_login(request):
    """
    Страница входа только для пациентов (ПИНФЛ + Полное имя).
    """
    if request.method == 'POST':
        request.session['is_demo'] = False
        full_name = request.POST.get('full_name')
        pinfl = request.POST.get('pinfl')
        
        try:
            patient = Patient.objects.using('default').get(pinfl=pinfl, full_name=full_name)
            from patients.models import PatientAuditLog
            PatientAuditLog.objects.using('default').create(
                patient=patient,
                action="Вход в систему (Проверка карты)"
            )
            request.session['patient_pinfl'] = patient.pinfl
            request.session['patient_name'] = patient.full_name
            messages.success(request, f"Добро пожаловать в Зеркало Здоровья, {patient.full_name}!")
            return redirect('patient_dashboard')
        except Patient.DoesNotExist:
            messages.error(request, "Пациент с такими данными не найден.")
            return redirect('patient_login')
            
    return render(request, 'patient_login.html')

def employee_hospitals(request):
    """
    Страница выбора филиала (больницы) для сотрудников.
    """
    hospitals = Hospital.objects.using('default').all()
    return render(request, 'employee_hospitals.html', {'hospitals': hospitals})

def login_view(request):
    """
    Вход только для сотрудников клиники.
    Принимает hospital_id через GET-параметр для отображения.
    """
    hospital_id = request.GET.get('hospital_id')
    hospital = None
    if hospital_id:
        try:
            hospital = Hospital.objects.using('default').get(id=hospital_id)
        except Hospital.DoesNotExist:
            pass

    if request.method == 'POST':
        request.session['is_demo'] = False
        email = request.POST.get('email')
        password = request.POST.get('password')
        branch = request.POST.get('branch') # Приходит из формы
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            if branch and str(user.hospital_id) != str(branch):
                messages.error(request, "Аккаунт не найден в выбранном филиале.")
                url = reverse('login')
                if branch:
                    url += f'?hospital_id={branch}'
                return redirect(url)
                
            if user.role == 'medcore_admin':
                messages.error(request, "Доступ запрещен. Для входа в MedCore Control используйте соответствующую панель.")
                return redirect('login')
            auth_login(request, user)
            
            AuditLog.objects.using('employees_db').create(
                employee=user,
                action="Успешный вход в систему",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f"Авторизация успешна. Роль: {user.get_role_display()}")
            
            if user.role == 'doctor':
                return redirect('doctor_dashboard')
            elif user.role == 'registry':
                return redirect('registry_dashboard')
            elif user.role == 'lab_tech':
                return redirect('lab_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
        else:
            messages.error(request, "Такого аккаунта нет или неверные данные. Попробуйте снова.")
            url = reverse('login')
            if branch:
                url += f'?hospital_id={branch}'
            return redirect(url)
            
    return render(request, 'login.html', {'hospital': hospital})

def logout_view(request):
    logout_type = request.GET.get('type')
    
    if logout_type == 'patient':
        if 'patient_pinfl' in request.session:
            del request.session['patient_pinfl']
            del request.session['patient_name']
        messages.info(request, "Вы вышли из профиля пациента.")
    elif logout_type == 'employee':
        if request.user.is_authenticated:
            AuditLog.objects.using('employees_db').create(
                employee=request.user,
                action="Выход из системы",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            if request.user.role == 'doctor':
                from records.models import TempDecryptedSession
                TempDecryptedSession.objects.using('temp_db').filter(doctor_id=request.user.id).delete()
            auth_logout(request)
        messages.info(request, "Вы вышли из системы клиники.")
    else:
        if 'patient_pinfl' in request.session:
            del request.session['patient_pinfl']
            del request.session['patient_name']
        if request.user.is_authenticated:
            if request.user.role == 'doctor':
                from records.models import TempDecryptedSession
                TempDecryptedSession.objects.using('temp_db').filter(doctor_id=request.user.id).delete()
            auth_logout(request)
        messages.info(request, "Вы успешно вышли из системы.")
        
    return redirect('landing')

import shutil
import os
from django.conf import settings
from django.db import connections

def patient_dashboard(request):
    if 'patient_pinfl' not in request.session:
        messages.error(request, "Необходима авторизация")
        return redirect('login')
        
    pinfl = request.session['patient_pinfl']
    try:
        patient = Patient.objects.using('default').get(pinfl=pinfl)
        
        active_record = None
        completed_lab_tests = None
        if request.method == 'POST' and request.POST.get('action') == 'open_record':
            record_id = request.POST.get('record_id')
            try:
                record_obj = EncryptedMedicalRecord.objects.using('default').get(id=record_id, patient=patient)
                try:
                    dec_data = decrypt_payload(record_obj.encrypted_payload)
                except Exception:
                    dec_data = {}
                active_record = {
                    'id': record_obj.id,
                    'created_at': record_obj.created_at,
                    'disease_name': record_obj.disease_name,
                    'doctor_name': record_obj.doctor_name,
                    'decrypted_data': dec_data
                }
                from patients.models import LabTest
                completed_lab_tests = LabTest.objects.using('default').filter(record=record_obj, status='completed')
            except EncryptedMedicalRecord.DoesNotExist:
                pass
        elif request.GET.get('close_record'):
            return redirect('patient_dashboard')

        # Получаем зашифрованные записи и расшифровываем их на лету
        encrypted_records = EncryptedMedicalRecord.objects.using('default').filter(patient=patient).order_by('-created_at')
        records = []
        for record in encrypted_records:
            try:
                decrypted_data = decrypt_payload(record.encrypted_payload)
            except Exception:
                decrypted_data = {"error": "Ошибка расшифровки"}
                
            try:
                if isinstance(record.encrypted_payload, memoryview):
                    display_cipher = record.encrypted_payload.tobytes().decode('utf-8', errors='ignore')
                elif isinstance(record.encrypted_payload, bytes):
                    display_cipher = record.encrypted_payload.decode('utf-8', errors='ignore')
                else:
                    display_cipher = str(record.encrypted_payload)
            except Exception:
                display_cipher = "ENCRYPTED_FERNET_TOKEN"
                
            records.append({
                'id': record.id,
                'created_at': record.created_at,
                'disease_name': record.disease_name,
                'doctor_name': record.doctor_name,
                'decrypted_data': decrypted_data,
                'display_cipher': display_cipher
            })
            
        return render(request, 'patient_dashboard.html', {'patient': patient, 'records': records, 'active_record': active_record, 'completed_lab_tests': completed_lab_tests})
    except Patient.DoesNotExist:
        return redirect('logout')

from records.models import TempDecryptedSession
from hospital_system.encryption_utils import encrypt_payload
import uuid
from django.utils import timezone
from patients.models import Patient, EncryptedMedicalRecord, LabTest

def get_dashboard_stats(user):
    today = timezone.now().date()
    stats = {'today': 0, 'in_progress': 0, 'completed': 0}
    
    if user.role == 'registry':
        stats['today'] = Patient.objects.using('default').filter(created_at__date=today).count()
        stats['in_progress'] = 0
        stats['completed'] = 0
    elif user.role == 'doctor':
        stats['today'] = EncryptedMedicalRecord.objects.using('default').filter(doctor_id=user.id, created_at__date=today).count()
        stats['in_progress'] = TempDecryptedSession.objects.using('temp_db').filter(doctor_id=user.id).count()
        stats['completed'] = stats['today']
    elif user.role == 'lab_tech':
        stats['today'] = LabTest.objects.using('default').filter(created_at__date=today).count()
        stats['in_progress'] = LabTest.objects.using('default').filter(lab_tech_id=user.id, status='in_progress').count()
        stats['completed'] = LabTest.objects.using('default').filter(lab_tech_id=user.id, status='completed', updated_at__date=today).count()
    elif user.role == 'admin':
        stats['today'] = Patient.objects.using('default').filter(created_at__date=today).count()
        stats['in_progress'] = TempDecryptedSession.objects.using('temp_db').count() + LabTest.objects.using('default').filter(status='in_progress').count()
        stats['completed'] = EncryptedMedicalRecord.objects.using('default').filter(created_at__date=today).count() + LabTest.objects.using('default').filter(status='completed', updated_at__date=today).count()
        
    return stats

def doctor_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'doctor':
        messages.error(request, "Доступ разрешен только врачам.")
        return redirect('login')

    context = {}
    context['stats'] = get_dashboard_stats(request.user)
    context['dashboard_title'] = "Панель Врача"
    
    # 1. Обработка поиска пациента
    q_pinfl = request.GET.get('q_pinfl')
    if q_pinfl:
        try:
            patient = Patient.objects.using('default').get(pinfl=q_pinfl)
            
            # Логируем доступ
            if request.user.role in ['doctor', 'lab_tech', 'registry', 'admin']:
                ProcessingLog.objects.using('default').create(
                    hospital_id=request.user.hospital_id,
                    employee_name=request.user.full_name,
                    employee_role=request.user.get_role_display(),
                    patient_pinfl=patient.pinfl,
                    action="Просмотр карты пациента"
                )
            
            context['patient'] = patient
            
            # Загружаем историю для найденного пациента
            encrypted_records = EncryptedMedicalRecord.objects.using('default').filter(patient=patient).order_by('-created_at')
            records = []
            for record in encrypted_records:
                try:
                    dec_data = decrypt_payload(record.encrypted_payload)
                except Exception:
                    dec_data = {}
                try:
                    if isinstance(record.encrypted_payload, memoryview):
                        display_cipher = record.encrypted_payload.tobytes().decode('utf-8', errors='ignore')
                    elif isinstance(record.encrypted_payload, bytes):
                        display_cipher = record.encrypted_payload.decode('utf-8', errors='ignore')
                    else:
                        display_cipher = str(record.encrypted_payload)
                except Exception:
                    display_cipher = "ENCRYPTED_FERNET_TOKEN"
                    
                records.append({
                    'id': record.id,
                    'created_at': record.created_at,
                    'disease_name': record.disease_name,
                    'doctor_name': record.doctor_name,
                    'decrypted_data': dec_data,
                    'display_cipher': display_cipher
                })
            context['records'] = records
        except Patient.DoesNotExist:
            messages.warning(request, "Пациент не найден.")
            
    # Calculate current age for pre-filling
    patient_age = ""
    if 'patient' in context and context['patient']:
        p = context['patient']
        if p.birth_date:
            today = timezone.now().date()
            patient_age = today.year - p.birth_date.year - ((today.month, today.day) < (p.birth_date.month, p.birth_date.day))
    context['patient_age'] = patient_age
            
    # 2. Обработка POST-действий (новая запись, редактирование, сохранение)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_patient_profile':
            patient_id = request.POST.get('patient_id')
            p = Patient.objects.using('default').get(id=patient_id)
            p.blood_group = request.POST.get('blood_group')
            p.rh_factor = request.POST.get('rh_factor')
            p.height = request.POST.get('height') or None
            p.weight = request.POST.get('weight') or None
            p.allergies = request.POST.get('allergies')
            p.chronic_diseases = request.POST.get('chronic_diseases')
            p.save(using='default')
            messages.success(request, "Профиль пациента успешно обновлен!")
            return redirect(f'/doctor/?q_pinfl={p.pinfl}')
        
        elif action == 'new_record':
            patient_id = request.POST.get('patient_id')
            patient = Patient.objects.using('default').get(id=patient_id)
            
            # Очищаем старые сессии врача перед новой
            TempDecryptedSession.objects.using('temp_db').filter(doctor_id=request.user.id).delete()
            
            session_id = str(uuid.uuid4())
            session = TempDecryptedSession.objects.using('temp_db').create(
                session_id=session_id,
                doctor_id=request.user.id,
                patient_pinfl=patient.pinfl,
                decrypted_data={}
            )
            context['patient'] = patient
            context['active_session'] = session
            context['active_record'] = {} # Пустая форма
            
        elif action == 'open_record':
            record_id = request.POST.get('record_id')
            record = EncryptedMedicalRecord.objects.using('default').get(id=record_id)
            patient = record.patient
            
            try:
                dec_data = decrypt_payload(record.encrypted_payload)
            except Exception:
                dec_data = {}
                
            # Очищаем старые сессии врача
            TempDecryptedSession.objects.using('temp_db').filter(doctor_id=request.user.id).delete()
            
            session_id = str(uuid.uuid4())
            session = TempDecryptedSession.objects.using('temp_db').create(
                session_id=session_id,
                doctor_id=request.user.id,
                patient_pinfl=patient.pinfl,
                record_id=record.id,
                decrypted_data=dec_data
            )
            context['patient'] = patient
            context['active_session'] = session
            context['active_record'] = {
                'disease_name': record.disease_name,
                'doctor_name': record.doctor_name,
                'created_at': record.created_at,
                **dec_data
            }
            
            # Загружаем результаты исследований
            from patients.models import LabTest
            completed_lab_tests = LabTest.objects.using('default').filter(record=record, status='completed')
            context['completed_lab_tests'] = completed_lab_tests
            
        elif action == 'save_record':
            session_id = request.POST.get('session_id')
            try:
                session = TempDecryptedSession.objects.using('temp_db').get(session_id=session_id)
                patient = Patient.objects.using('default').get(pinfl=session.patient_pinfl)
                
                test_types = request.POST.getlist('test_type[]')
                xray_parts = request.POST.getlist('xray_part[]')
                ordered_tests = []
                for tt, xp in zip(test_types, xray_parts):
                    if tt.strip():
                        if "Рентген" in tt.strip() and xp.strip():
                            ordered_tests.append(f"{tt.strip()} ({xp.strip()})")
                        else:
                            ordered_tests.append(tt.strip())
                            
                # Формируем Payload
                payload = {
                    'symptoms': request.POST.get('symptoms'),
                    'diagnosis': request.POST.get('disease_name') or 'Не указан',
                    'treatment': request.POST.get('treatment'),
                    'tests': request.POST.get('tests'),
                    'ordered_tests': ordered_tests,
                    'vitals': {
                        'bp': request.POST.get('vital_bp'),
                        'temp': request.POST.get('vital_temp'),
                        'age': request.POST.get('vital_age'),
                        'weight': request.POST.get('vital_weight'),
                        'height': request.POST.get('vital_height'),
                    }
                }
                
                # Шифруем AES-256
                encrypted_bytes = encrypt_payload(payload)
                
                if session.record_id:
                    # Обновление существующей записи
                    record = EncryptedMedicalRecord.objects.using('default').get(id=session.record_id)
                    record.disease_name = request.POST.get('disease_name') or 'Не указан'
                    record.encrypted_payload = encrypted_bytes
                    record.save(using='default')
                    messages.success(request, f"Запись успешно обновлена и зашифрована.")
                else:
                    # Создание новой
                    record = EncryptedMedicalRecord.objects.using('default').create(
                        patient=patient,
                        doctor_id=request.user.id,
                        doctor_name=request.user.full_name,
                        disease_name=request.POST.get('disease_name') or 'Не указан',
                        encrypted_payload=encrypted_bytes,
                        hospital_id=request.user.hospital_id
                    )
                    messages.success(request, f"Новая запись зашифрована и сохранена в Global DB.")
                
                ProcessingLog.objects.using('default').create(
                    hospital_id=request.user.hospital_id,
                    employee_name=request.user.full_name,
                    employee_role=request.user.get_role_display(),
                    patient_pinfl=patient.pinfl,
                    action="Сохранение/Обновление медицинской записи"
                )
                
                # Создаем или находим задания для лаборатории
                from patients.models import LabTest
                for test_name in ordered_tests:
                    LabTest.objects.using('default').get_or_create(
                        patient=patient,
                        record=record,
                        test_name=test_name,
                        defaults={'status': 'pending'}
                    )
                
                # УДАЛЕНИЕ СЕССИИ ИЗ ВРЕМЕННОЙ БАЗЫ (The Wipe)
                session.delete(using='temp_db')
                
                # Перезагружаем с поиском этого пациента
                return redirect(f'/doctor/?q_pinfl={patient.pinfl}')
            except Exception as e:
                messages.error(request, f"Ошибка сохранения: {str(e)}")
                
    # Обработка отмены редактирования
    if request.GET.get('cancel_edit'):
        # Очищаем все сессии этого врача
        TempDecryptedSession.objects.using('temp_db').filter(doctor_id=request.user.id).delete()
        messages.info(request, "Редактирование отменено, временная база очищена.")
        q_pinfl = request.GET.get('q_pinfl')
        if q_pinfl:
            return redirect(f'/doctor/?q_pinfl={q_pinfl}')
        return redirect('doctor_dashboard')

    return render(request, 'doctor_dashboard.html', context)

def registry_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'registry':
        messages.error(request, "Доступ разрешен только сотрудникам регистратуры.")
        return redirect('login')

    context = {}
    context['stats'] = get_dashboard_stats(request.user)
    context['dashboard_title'] = "Панель Регистратора"
    
    if request.method == 'GET' and 'pinfl' in request.GET:
        pinfl = request.GET.get('pinfl')
        context['searched'] = True
        try:
            patient = Patient.objects.using('default').get(pinfl=pinfl)
            context['patient'] = patient
            # Логируем аудит
            AuditLog.objects.using('employees_db').create(
                employee=request.user,
                action="Поиск медицинской карты",
                patient_identifier=pinfl
            )
        except Patient.DoesNotExist:
            context['patient'] = None
            
    elif request.method == 'POST' and request.POST.get('action') == 'create_patient':
        try:
            patient = Patient.objects.using('default').create(
                pinfl=request.POST.get('pinfl'),
                full_name=request.POST.get('full_name'),
                passport=request.POST.get('passport'),
                birth_date=request.POST.get('birth_date'),
                gender=request.POST.get('gender'),
                phone_number=request.POST.get('phone_number'),
                blood_group=request.POST.get('blood_group'),
                rh_factor=request.POST.get('rh_factor'),
                height=request.POST.get('height') or None,
                weight=request.POST.get('weight') or None,
                allergies=request.POST.get('allergies'),
                chronic_diseases=request.POST.get('chronic_diseases'),
                hospital_id=request.user.hospital_id
            )
            # Логируем аудит
            AuditLog.objects.using('employees_db').create(
                employee=request.user,
                action="Создание новой медицинской карты",
                patient_identifier=patient.pinfl
            )
            # Глобальный лог процессинга
            ProcessingLog.objects.using('default').create(
                hospital_id=request.user.hospital_id,
                employee_name=request.user.full_name,
                employee_role=request.user.get_role_display(),
                patient_pinfl=patient.pinfl,
                action="Регистрация нового пациента"
            )
            messages.success(request, f"Медицинская карта успешно создана для {patient.full_name} в Global DB!")
            return redirect(f'/registry/?pinfl={patient.pinfl}')
        except Exception as e:
            from django.db import IntegrityError
            if isinstance(e, IntegrityError):
                messages.error(request, "Ошибка: Пациент с таким ПИНФЛ или Паспортом уже существует в базе.")
            else:
                messages.error(request, f"Ошибка создания пациента: {str(e)}")
            
    elif request.method == 'POST' and request.POST.get('action') == 'update_patient':
        try:
            patient = Patient.objects.using('default').get(pinfl=request.POST.get('pinfl'))
            patient.full_name = request.POST.get('full_name')
            patient.passport = request.POST.get('passport')
            patient.birth_date = request.POST.get('birth_date')
            patient.gender = request.POST.get('gender')
            patient.phone_number = request.POST.get('phone_number')
            patient.blood_group = request.POST.get('blood_group')
            patient.rh_factor = request.POST.get('rh_factor')
            patient.height = request.POST.get('height') or None
            patient.weight = request.POST.get('weight') or None
            patient.allergies = request.POST.get('allergies')
            patient.chronic_diseases = request.POST.get('chronic_diseases')
            patient.save(using='default')
            
            AuditLog.objects.using('employees_db').create(
                employee=request.user,
                action="Обновление данных медицинской карты",
                patient_identifier=patient.pinfl
            )
            ProcessingLog.objects.using('default').create(
                hospital_id=request.user.hospital_id,
                employee_name=request.user.full_name,
                employee_role=request.user.get_role_display(),
                patient_pinfl=patient.pinfl,
                action="Обновление профиля пациента"
            )
            messages.success(request, f"Медицинская карта {patient.full_name} успешно обновлена!")
            return redirect(f'/registry/?pinfl={patient.pinfl}')
        except Exception as e:
            messages.error(request, f"Ошибка обновления пациента: {str(e)}")
            
    return render(request, 'registry_dashboard.html', context)

from datetime import timedelta
from django.utils import timezone

from django.db.models import Count
def admin_employees_panel(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        messages.error(request, "Доступ разрешен только администраторам.")
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_schedule':
            emp_id = request.POST.get('employee_id')
            try:
                emp = Employee.objects.using('employees_db').get(id=emp_id)
                emp.work_schedule = {
                    'monday': request.POST.get('monday', 'Выходной'),
                    'tuesday': request.POST.get('tuesday', 'Выходной'),
                    'wednesday': request.POST.get('wednesday', 'Выходной'),
                    'thursday': request.POST.get('thursday', 'Выходной'),
                    'friday': request.POST.get('friday', 'Выходной'),
                }
                # update specialty and role if needed
                if request.POST.get('specialty'):
                    emp.specialty = request.POST.get('specialty')
                if request.POST.get('role_update'):
                    emp.role = request.POST.get('role_update')
                emp.save(using='employees_db')
                AuditLog.objects.using('employees_db').create(
                    employee=request.user,
                    action=f"Изменен график/должность сотрудника {emp.full_name}",
                )
                messages.success(request, f"График сотрудника {emp.full_name} успешно обновлен.")
            except Employee.DoesNotExist:
                messages.error(request, "Сотрудник не найден.")
            return redirect(f'/admin_panel/employees/?employee_id={emp_id}')
            
        elif action == 'delete_employee':
            emp_id = request.POST.get('employee_id')
            try:
                emp = Employee.objects.using('employees_db').get(id=emp_id)
                emp_name = emp.full_name
                emp.delete()
                AuditLog.objects.using('employees_db').create(
                    employee=request.user,
                    action=f"Сотрудник удален из системы: {emp_name}",
                )
                messages.success(request, f"Сотрудник {emp_name} успешно удален.")
            except Employee.DoesNotExist:
                messages.error(request, "Сотрудник не найден.")
            return redirect('admin_employees_panel')

    # Filter logic
    role_filter = request.GET.get('role', '')
    spec_filter = request.GET.get('specialty', '')
    
    employees = Employee.objects.using('employees_db').filter(role__in=['doctor', 'lab_tech'])
    if role_filter:
        employees = employees.filter(role=role_filter)
    if spec_filter:
        employees = employees.filter(specialty__icontains=spec_filter)
        
    employees = employees.order_by('full_name')
    
    # Selected employee logic
    selected_emp_id = request.GET.get('employee_id')
    selected_employee = None
    emp_stats = {'today': 0, 'completed': 0, 'in_progress': 0}
    
    if selected_emp_id:
        try:
            selected_employee = Employee.objects.using('employees_db').get(id=selected_emp_id)
            today = timezone.now().date()
            if selected_employee.role == 'doctor':
                emp_stats['today'] = EncryptedMedicalRecord.objects.using('default').filter(doctor_id=selected_employee.id, created_at__date=today).count()
                emp_stats['completed'] = emp_stats['today'] # For doctor, created = completed
            elif selected_employee.role == 'lab_tech':
                from patients.models import LabTest
                emp_stats['today'] = LabTest.objects.using('default').filter(lab_tech_id=selected_employee.id, updated_at__date=today).count()
                emp_stats['completed'] = LabTest.objects.using('default').filter(lab_tech_id=selected_employee.id, status='completed', updated_at__date=today).count()
                emp_stats['in_progress'] = LabTest.objects.using('default').filter(lab_tech_id=selected_employee.id, status='in_progress').count()
        except Employee.DoesNotExist:
            pass

    context = {
        'dashboard_title': "Панель Сотрудников",
        'employees': employees,
        'selected_employee': selected_employee,
        'emp_stats': emp_stats,
        'role_filter': role_filter,
        'spec_filter': spec_filter,
    }
    return render(request, 'admin_employees_panel.html', context)

def admin_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        messages.error(request, "Доступ разрешен только администраторам.")
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'wipe_temp_db':
            # Admin Wipe Temporary DB
            TempDecryptedSession.objects.using('temp_db').all().delete()
            messages.success(request, "Временная база данных принудительно очищена (Wiped).")
            AuditLog.objects.using('employees_db').create(
                employee=request.user,
                action="Принудительная очистка Временной БД",
            )
            return redirect('admin_dashboard')
            
        elif action == 'add_doctor':
            email = request.POST.get('email')
            
            if Employee.objects.using('employees_db').filter(email=email).exists():
                messages.error(request, f"Сотрудник с почтой {email} уже зарегистрирован.")
                return redirect('admin_dashboard')

            full_name = request.POST.get('full_name')
            password = request.POST.get('password')
            shift = request.POST.get('shift', 'morning')
            specialty = request.POST.get('specialty')
            
            role = request.POST.get('role', 'doctor')
            
            try:
                Employee.objects.db_manager('employees_db').create_user(
                    email=email,
                    full_name=full_name,
                    role=role,
                    password=password,
                    shift=shift,
                    specialty=specialty,
                    hospital_id=request.user.hospital_id,
                    hospital_branch=request.user.hospital_branch
                )
                AuditLog.objects.using('employees_db').create(
                    employee=request.user,
                    action=f"Добавлен новый сотрудник: {full_name} ({specialty})",
                )
                messages.success(request, f"Сотрудник {full_name} успешно добавлен.")
            except Exception as e:
                messages.error(request, f"Ошибка добавления врача: {str(e)}")
            return redirect('admin_dashboard')
            
        elif action == 'update_shift':
            doctor_id = request.POST.get('doctor_id')
            shift = request.POST.get('shift')
            try:
                doc = Employee.objects.using('employees_db').get(id=doctor_id)
                doc.shift = shift
                doc.save(using='employees_db')
                AuditLog.objects.using('employees_db').create(
                    employee=request.user,
                    action=f"Изменена смена врача {doc.full_name} на {shift}",
                )
                messages.success(request, "Смена успешно обновлена.")
            except Employee.DoesNotExist:
                pass
            return redirect('admin_dashboard')

    # Получаем данные для дашборда
    audit_logs = AuditLog.objects.using('employees_db').filter(
        employee__hospital_id=request.user.hospital_id
    ).exclude(employee__role='medcore_admin').order_by('-timestamp')[:15]
    
    # Статистика
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=7)

    daily_patients = EncryptedMedicalRecord.objects.using('default').filter(created_at__date=today).count()
    weekly_patients = EncryptedMedicalRecord.objects.using('default').filter(created_at__gte=seven_days_ago).count()
    
    # Временная БД
    temp_sessions_count = TempDecryptedSession.objects.using('temp_db').count()
    
    context = {
        'audit_logs': audit_logs,
        'daily_patients': daily_patients,
        'weekly_patients': weekly_patients,
        'temp_sessions_count': temp_sessions_count,
        'stats': get_dashboard_stats(request.user),
        'dashboard_title': "Панель Администратора"
    }
    
    return render(request, 'admin_dashboard.html', context)

def employee_profile(request):
    if not request.user.is_authenticated or request.user.role not in ['doctor', 'lab_tech']:
        messages.error(request, "Доступ разрешен только врачам и диагностам.")
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_password':
            new_password = request.POST.get('new_password')
            if new_password:
                request.user.set_password(new_password)
                request.user.save(using='employees_db')
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                messages.success(request, "Ваш пароль был успешно изменен!")
            return redirect('employee_profile')
            
    context = {}
    context['stats'] = get_dashboard_stats(request.user)
            
    return render(request, 'employee_profile.html', context)

from patients.models import LabTest
from hospital_system.test_schemas import TEST_SCHEMAS

def lab_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'lab_tech':
        messages.error(request, "Доступ разрешен только сотрудникам лаборатории и диагностам.")
        return redirect('login')

    context = {}
    context['stats'] = get_dashboard_stats(request.user)
    context['dashboard_title'] = "Панель Диагноста"
    specialty = request.user.specialty or ""
    context['specialty'] = specialty
    
    # 1. Поиск пациента по паспорту
    q_passport = request.GET.get('q_passport')
    if q_passport:
        try:
            patient = Patient.objects.using('default').get(passport=q_passport)
            context['patient'] = patient
            context['searched'] = True
            
            # Находим все НЕ ЗАВЕРШЕННЫЕ тесты пациента
            pending_tests = LabTest.objects.using('default').filter(patient=patient, status='pending')
            
            # Фильтрация по специализации
            spec_lower = specialty.lower()
            if 'рентген' in spec_lower:
                pending_tests = pending_tests.filter(test_name__icontains='Рентген')
            elif 'узи' in spec_lower:
                pending_tests = pending_tests.filter(test_name__icontains='УЗИ')
            elif 'мрт' in spec_lower:
                pending_tests = pending_tests.filter(test_name__icontains='МРТ')
            elif 'лаборант' in spec_lower:
                pending_tests = pending_tests.exclude(test_name__icontains='Рентген').exclude(test_name__icontains='УЗИ').exclude(test_name__icontains='МРТ')
                
            context['pending_tests'] = pending_tests
        except Patient.DoesNotExist:
            messages.warning(request, "Пациент не найден.")
            context['searched'] = True

    # 2. Мои задачи (Панель задач)
    current_tasks = list(LabTest.objects.using('default').filter(lab_tech_id=request.user.id, status='in_progress').order_by('-updated_at'))
    completed_tasks = LabTest.objects.using('default').filter(lab_tech_id=request.user.id, status='completed').order_by('-updated_at')[:20]
    
    for task in current_tasks:
        if task.test_name in TEST_SCHEMAS:
            import copy
            schema_copy = copy.deepcopy(TEST_SCHEMAS[task.test_name])
            if task.result_data:
                val_map = {item['id']: item.get('value', '') for item in task.result_data}
                for field in schema_copy:
                    field['saved_value'] = val_map.get(field['id'], '')
            else:
                for field in schema_copy:
                    field['saved_value'] = ''
            task.schema = schema_copy
        else:
            task.schema = None
            
    context['current_tasks'] = current_tasks
    context['completed_tasks'] = completed_tasks
    
    # 3. POST Actions (Start, Save, Send)
    if request.method == 'POST':
        action = request.POST.get('action')
        test_id = request.POST.get('test_id')
        
        if test_id:
            try:
                test = LabTest.objects.using('default').get(id=test_id)
                
                if action == 'start':
                    test.status = 'in_progress'
                    test.lab_tech_id = request.user.id
                    test.lab_tech_name = request.user.full_name
                    test.save(using='default')
                    messages.success(request, f"Вы взяли в работу: {test.test_name}")
                    return redirect('lab_dashboard')
                    
                elif action == 'cancel':
                    test.status = 'pending'
                    test.lab_tech_id = None
                    test.lab_tech_name = None
                    test.save(using='default')
                    messages.info(request, f"Работа над анализом '{test.test_name}' отменена.")
                    return redirect('lab_dashboard')
                    
                elif action in ['save', 'send']:
                    test.report = request.POST.get('report', '')
                    if 'image' in request.FILES:
                        test.image = request.FILES['image']
                        
                    if test.test_name in TEST_SCHEMAS:
                        schema = TEST_SCHEMAS[test.test_name]
                        result_data = []
                        for field in schema:
                            val = request.POST.get(f"field_{field['id']}")
                            if val is not None:
                                ref_range = field['ref_m'] if test.patient.gender == 'M' else field['ref_f']
                                result_data.append({
                                    "id": field['id'],
                                    "name": field['name'],
                                    "value": val,
                                    "unit": field['unit'],
                                    "ref_range": ref_range
                                })
                        test.result_data = result_data
                        
                    if action == 'send':
                        test.status = 'completed'
                        
                    test.save(using='default')
                    messages.success(request, "Промежуточные данные сохранены." if action == 'save' else "Результаты успешно отправлены врачу!")
                    if action == 'send':
                        return redirect('lab_dashboard')
            except LabTest.DoesNotExist:
                messages.error(request, "Анализ не найден.")
                
    return render(request, 'lab_dashboard.html', context)

import hashlib
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def export_record_pdf(request, record_id):
    if not request.user.is_authenticated and 'patient_pinfl' not in request.session:
        messages.error(request, "Необходима авторизация")
        return redirect('login')
        
    try:
        record = EncryptedMedicalRecord.objects.using('default').get(id=record_id)
        
        # Security check: if patient, check PINFL
        if 'patient_pinfl' in request.session:
            if record.patient.pinfl != request.session['patient_pinfl']:
                return redirect('patient_dashboard')
                
        # Decrypt data
        try:
            dec_data = decrypt_payload(record.encrypted_payload)
        except Exception:
            dec_data = {"error": "Ошибка расшифровки"}
            
        # Calculate SHA-256 hash of the encrypted payload
        payload_bytes = record.encrypted_payload
        if isinstance(payload_bytes, memoryview):
            payload_bytes = payload_bytes.tobytes()
        elif not isinstance(payload_bytes, bytes):
            payload_bytes = str(payload_bytes).encode('utf-8')
            
        record_hash = hashlib.sha256(payload_bytes).hexdigest()
        
        # Create PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="medical_record_{record.id}.pdf"'
        
        c = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        
        # Register Font (Windows Arial)
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Arial', font_path))
            c.setFont("Arial", 16)
        else:
            # Fallback (might break cyrillic)
            c.setFont("Helvetica-Bold", 16)
            
        c.drawString(50, height - 50, "МЕДИЦИНСКАЯ ВЫПИСКА (MedCore)")
        
        if os.path.exists(font_path):
            c.setFont("Arial", 12)
        else:
            c.setFont("Helvetica", 12)
            
        y = height - 90
        
        def write_line(text, y_pos):
            c.drawString(50, y_pos, text)
            return y_pos - 20
            
        y = write_line(f"Пациент: {record.patient.full_name} (ПИНФЛ: {record.patient.pinfl})", y)
        y = write_line(f"Врач: {record.doctor_name}", y)
        y = write_line(f"Дата приема: {record.created_at.strftime('%Y-%m-%d %H:%M')}", y)
        y -= 10
        y = write_line(f"Диагноз: {record.disease_name}", y)
        
        y -= 10
        y = write_line("Симптомы:", y)
        symptoms = str(dec_data.get('symptoms') or 'Нет данных')
        for line in symptoms.split('\n'):
            if line.strip():
                y = write_line(f"  {line.strip()}", y)
                
        y -= 10
        y = write_line("Результаты анализов (Заключение врача):", y)
        tests = str(dec_data.get('tests') or 'Нет данных')
        for line in tests.split('\n'):
            if line.strip():
                y = write_line(f"  {line.strip()}", y)
                
        y -= 10
        from patients.models import LabTest
        completed_lab_tests = LabTest.objects.using('default').filter(record=record, status='completed')
        if completed_lab_tests.exists():
            y = write_line("РЕЗУЛЬТАТЫ ЛАБОРАТОРИИ / ДИАГНОСТИКИ:", y)
            for t in completed_lab_tests:
                y = write_line(f"  - {t.test_name} (Лаборант: {t.lab_tech_name or 'Неизвестно'}):", y)
                if t.result_data:
                    for item in t.result_data:
                        y = write_line(f"      {item.get('name')}: {item.get('value')} {item.get('unit')} (Норма: {item.get('ref_range')})", y)
                if t.report:
                    y = write_line(f"      Заключение: {t.report}", y)
                y -= 5
                
        y -= 10
        y = write_line("Назначение (Лечение):", y)
        treatment = str(dec_data.get('treatment') or 'Нет данных')
        for line in treatment.split('\n'):
            if line.strip():
                y = write_line(f"  {line.strip()}", y)
                
        # Draw hash at the bottom
        c.line(50, 60, width - 50, 60)
        
        if os.path.exists(font_path):
            c.setFont("Arial", 8)
        else:
            c.setFont("Helvetica", 8)
            
        c.drawString(50, 45, "ЭЛЕКТРОННАЯ МЕДИЦИНСКАЯ ЗАПИСЬ ЗАЩИЩЕНА АЛГОРИТМОМ AES-256")
        c.drawString(50, 35, f"SHA-256 ХЭШ: {record_hash}")
        c.drawString(50, 25, f"ID ЗАПИСИ: {record.id} | MedCore Health System")
        
        c.showPage()
        c.save()
        return response
        
    except EncryptedMedicalRecord.DoesNotExist:
        messages.error(request, "Запись не найдена.")
        if 'patient_pinfl' in request.session:
            return redirect('patient_dashboard')
        return redirect('doctor_dashboard')
