from django.urls import path
from . import views
from . import views_medcore

urlpatterns = [
    path('', views.landing_page, name='landing'),
    
    # Prod URLs
    path('prod/', views.prod_landing, name='prod_landing'),
    path('patient/login/', views.patient_login, name='patient_login'),
    path('employee/hospitals/', views.employee_hospitals, name='employee_hospitals'),
    path('employee/login/', views.login_view, name='login'),
    
    # Guide URL
    path('guide/', views.guide_page, name='guide'),
    
    path('logout/', views.logout_view, name='logout'),
    
    # Заглушки, которые мы реализуем позже
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('employee/profile/', views.employee_profile, name='employee_profile'),
    path('lab/', views.lab_dashboard, name='lab_dashboard'),
    path('registry/', views.registry_dashboard, name='registry_dashboard'),
    path('admin_panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_panel/employees/', views.admin_employees_panel, name='admin_employees_panel'),
    
    # MedCore Control Panel
    path('medcore/login/', views_medcore.medcore_login, name='medcore_login'),
    path('medcore/logout/', views_medcore.medcore_logout, name='medcore_logout'),
    path('medcore/', views_medcore.medcore_dashboard, name='medcore_dashboard'),
    path('medcore/hospital/<int:hospital_id>/', views_medcore.medcore_hospital_detail, name='medcore_hospital_detail'),
    path('medcore/processing/', views_medcore.medcore_processing, name='medcore_processing'),
    path('medcore/global_db/', views_medcore.medcore_global_db, name='medcore_global_db'),
    
    # PDF Export Endpoint
    path('record/<int:record_id>/pdf/', views.export_record_pdf, name='export_record_pdf'),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from . import views_api

urlpatterns += [
    # Swagger API Endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Public API
    path('api/v1/hospitals/', views_api.public_hospitals_list, name='api_hospitals'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
