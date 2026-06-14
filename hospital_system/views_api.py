from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from patients.models import Hospital

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'name', 'address']

@extend_schema(responses=HospitalSerializer(many=True))
@api_view(['GET'])
def public_hospitals_list(request):
    """
    Возвращает список всех больниц, подключенных к сети MedCore.
    Это публичный эндпоинт, который могут использовать сторонние сервисы 
    для проверки доступности больниц.
    """
    hospitals = Hospital.objects.using('default').all()
    serializer = HospitalSerializer(hospitals, many=True)
    return Response(serializer.data)
