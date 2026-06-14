from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from employees.models import Employee
from patients.models import Hospital, ProcessingLog, Patient, EncryptedMedicalRecord

def medcore_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is not None and user.role == 'medcore_admin':
            request.session['medcore_admin_id'] = user.id
            return redirect('medcore_dashboard')
        else:
            messages.error(request, "Неверные учетные данные или нет доступа.")
            
    return render(request, 'medcore_login.html')

def medcore_logout(request):
    if 'medcore_admin_id' in request.session:
        del request.session['medcore_admin_id']
    return redirect('medcore_login')

def check_medcore_auth(request):
    if 'medcore_admin_id' in request.session:
        try:
            user = Employee.objects.using('employees_db').get(id=request.session['medcore_admin_id'])
            if user.role == 'medcore_admin':
                return user
        except Employee.DoesNotExist:
            pass
    return None

def medcore_dashboard(request):
    medcore_user = check_medcore_auth(request)
    if not medcore_user:
        return redirect('medcore_login')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_hospital':
            hospital_id = request.POST.get('hospital_id')
            try:
                # Delete employees associated with hospital
                Employee.objects.using('employees_db').filter(hospital_id=hospital_id).delete()
                # Delete hospital
                Hospital.objects.using('default').get(id=hospital_id).delete()
                messages.success(request, "Больница и ее сотрудники успешно удалены.")
            except Exception as e:
                messages.error(request, f"Ошибка удаления: {str(e)}")
            return redirect('medcore_dashboard')
        else:
            name = request.POST.get('name')
            region = request.POST.get('region')
            city = request.POST.get('city')
            street = request.POST.get('street')
            api_key = request.POST.get('api_key')
            
            # Form the full address
            address = f"{region}, {city}, {street}"
            
            try:
                Hospital.objects.using('default').create(name=name, address=address, api_key=api_key)
                messages.success(request, f"Больница {name} успешно добавлена.")
            except Exception as e:
                messages.error(request, f"Ошибка создания: {str(e)}")
            return redirect('medcore_dashboard')

    hospitals = Hospital.objects.using('default').all()
    
    # Сбор статистики
    for h in hospitals:
        h.patient_count = Patient.objects.using('default').filter(hospital=h).count()
        h.record_count = EncryptedMedicalRecord.objects.using('default').filter(hospital=h).count()
        h.admin_count = Employee.objects.using('employees_db').filter(hospital_id=h.id, role='admin').count()

    return render(request, 'medcore_dashboard.html', {'hospitals': hospitals, 'medcore_user': medcore_user})

def medcore_hospital_detail(request, hospital_id):
    medcore_user = check_medcore_auth(request)
    if not medcore_user:
        return redirect('medcore_login')
        
    hospital = Hospital.objects.using('default').get(id=hospital_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_admin':
            email = request.POST.get('email')
            
            if Employee.objects.using('employees_db').filter(email=email).exists():
                messages.error(request, f"Администратор с почтой {email} уже зарегистрирован.")
                return redirect('medcore_hospital_detail', hospital_id=hospital_id)
                
            full_name = request.POST.get('full_name')
            password = request.POST.get('password')
            
            try:
                emp = Employee.objects.db_manager('employees_db').create_user(
                    email=email,
                    full_name=full_name,
                    password=password,
                    role='admin',
                    hospital_id=hospital.id,
                    hospital_branch=hospital.name
                )
                messages.success(request, f"Администратор {full_name} успешно создан.")
            except Exception as e:
                messages.error(request, f"Ошибка создания администратора: {str(e)}")
                
        elif action == 'remove_admin':
            emp_id = request.POST.get('emp_id')
            try:
                emp = Employee.objects.using('employees_db').get(id=emp_id)
                emp.delete()
                messages.success(request, "Администратор удален.")
            except:
                messages.error(request, "Ошибка удаления.")
                
        return redirect(f'/medcore/hospital/{hospital_id}/')
        
    admins = Employee.objects.using('employees_db').filter(hospital_id=hospital.id, role='admin')
    
    return render(request, 'medcore_hospital.html', {'hospital': hospital, 'admins': admins, 'medcore_user': medcore_user})

def medcore_processing(request):
    medcore_user = check_medcore_auth(request)
    if not medcore_user:
        return redirect('medcore_login')
        
    hospitals = Hospital.objects.using('default').all()
    selected_hospital = request.GET.get('hospital_id')
    
    logs = ProcessingLog.objects.using('default').all().order_by('-timestamp')
    if selected_hospital:
        logs = logs.filter(hospital_id=selected_hospital)
        
    return render(request, 'medcore_processing.html', {
        'logs': logs,
        'hospitals': hospitals,
        'selected_hospital': selected_hospital,
        'medcore_user': medcore_user
    })

def medcore_global_db(request):
    medcore_user = check_medcore_auth(request)
    if not medcore_user:
        return redirect('medcore_login')
        
    patients = Patient.objects.using('default').all()
    selected_patient_id = request.GET.get('patient_id')
    
    if selected_patient_id:
        records = EncryptedMedicalRecord.objects.using('default').filter(patient_id=selected_patient_id).order_by('-created_at')
        selected_patient = Patient.objects.using('default').filter(id=selected_patient_id).first()
    else:
        records = EncryptedMedicalRecord.objects.using('default').all().order_by('-created_at')
        selected_patient = None
        
    for r in records:
        try:
            if isinstance(r.encrypted_payload, memoryview):
                r.display_cipher = r.encrypted_payload.tobytes().decode('utf-8', errors='ignore')
            elif isinstance(r.encrypted_payload, bytes):
                r.display_cipher = r.encrypted_payload.decode('utf-8', errors='ignore')
            else:
                r.display_cipher = str(r.encrypted_payload)
        except Exception:
            r.display_cipher = "ENCRYPTED_FERNET_TOKEN"
    
    return render(request, 'medcore_global_db.html', {
        'patients': patients,
        'records': records,
        'selected_patient': selected_patient,
        'medcore_user': medcore_user
    })
