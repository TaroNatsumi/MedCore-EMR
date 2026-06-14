from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from patients.models import Hospital

@api_view(['GET'])
def public_hospitals_list(request):
    """
    Возвращает список всех больниц, подключенных к сети MedCore.
    Это публичный эндпоинт, который могут использовать сторонние сервисы 
    для проверки доступности больниц.
    """
    hospitals = Hospital.objects.using('default').all()
    data = []
    for h in hospitals:
        data.append({
            'id': h.id,
            'name': h.name,
            'address': h.address
        })
    return Response(data)
