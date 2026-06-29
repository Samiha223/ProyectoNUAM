import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_tributaria.settings')
django.setup()

from django.contrib.auth.models import User, Group
from tributacion.models import Mercado, Instrumento

def seed():
    print("Iniciando carga de datos de prueba...")
    
    # 1. Crear Mercados
    acciones, _ = Mercado.objects.get_or_create(nombre='Acciones')
    cfi, _ = Mercado.objects.get_or_create(nombre='CFI')
    mutuos, _ = Mercado.objects.get_or_create(nombre='Fondos Mutuos')
    print("Mercados creados.")

    # 2. Crear Instrumentos
    instrumentos_data = [
        {'nemotecnico': 'CHILE', 'nombre': 'Banco de Chile', 'mercado': acciones, 'inscrito': True},
        {'nemotecnico': 'COPEC', 'nombre': 'Empresas Copec S.A.', 'mercado': acciones, 'inscrito': True},
        {'nemotecnico': 'CFIMRCLP', 'nombre': 'CFI Pioneer Real Estate', 'mercado': cfi, 'inscrito': True},
        {'nemotecnico': 'CFIMVALP', 'nombre': 'CFI LarrainVial Ahorro', 'mercado': cfi, 'inscrito': True},
        {'nemotecnico': 'FM_GL_PRO', 'nombre': 'Fondo Mutuo Global Pro', 'mercado': mutuos, 'inscrito': False},
        {'nemotecnico': 'FM_CL_STG', 'nombre': 'Fondo Mutuo Santiago Liquidez', 'mercado': mutuos, 'inscrito': True},
    ]

    for data in instrumentos_data:
        inst, created = Instrumento.objects.get_or_create(
            nemotecnico=data['nemotecnico'],
            defaults={'nombre': data['nombre'], 'mercado': data['mercado'], 'inscrito': data['inscrito']}
        )
        if created:
            print(f"Instrumento creado: {inst.nemotecnico}")

    # 3. Crear Grupos / Roles
    admin_group, _ = Group.objects.get_or_create(name='Administrador')
    corredor_group, _ = Group.objects.get_or_create(name='Corredor de Bolsa')
    print("Grupos/Roles RBAC creados.")

    # 4. Crear Usuarios de prueba
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        admin_user.groups.add(admin_group)
        print("Usuario administrador creado: admin / admin123")
    else:
        admin_user = User.objects.get(username='admin')
        admin_user.groups.add(admin_group)

    if not User.objects.filter(username='corredor').exists():
        corredor_user = User.objects.create_user('corredor', 'corredor@example.com', 'corredor123')
        corredor_user.groups.add(corredor_group)
        print("Usuario corredor creado: corredor / corredor123")
    else:
        corredor_user = User.objects.get(username='corredor')
        corredor_user.groups.add(corredor_group)

    print("Carga de datos finalizada con éxito.")

if __name__ == '__main__':
    seed()
