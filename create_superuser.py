import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aserradero.settings')
django.setup()

from django.contrib.auth.models import User

# Crear superuser si no existe
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@aserradero.local', 'admin123')
    print("Superuser 'admin' creado exitosamente")
    print("Usuario: admin")
    print("Contraseña: admin123")
else:
    print("El usuario 'admin' ya existe")
