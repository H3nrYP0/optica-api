"""
Script completo para inicializar la base de datos con:
- Roles (Admin, Cliente)
- Permisos granulares (CRUD y especiales)
- Asignación de todos los permisos al rol Admin
- Usuario administrador (con cliente asociado para pruebas)
- Usuario cliente estándar (con su cliente)

Nota: Para SQLite, los campos fecha deben ser objetos date, no strings.
"""

import sys
import os
from datetime import date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.Models.models import Rol, Usuario, Cliente, Permiso, PermisoPorRol
from werkzeug.security import generate_password_hash

# ------------------------------------------------------------
# 1. Lista de permisos granulares (entidades y acciones)
# ------------------------------------------------------------
ENTIDADES = [
    'usuarios', 'clientes', 'productos', 'ventas', 'citas',
    'empleados', 'proveedores'
]
ACCIONES = ['ver', 'crear', 'editar', 'eliminar']

PERMISOS_ESPECIALES = [
    'cambiar_estado_pedido', 'cambiar_estado_cita', 'cambiar_estado_venta',
    'generar_reporte_ventas', 'generar_reporte_citas', 'generar_reporte_inventario',
    'descargar_comprobante_pedido', 'ver_reportes', 'ver_imagenes',
    'subir_imagenes', 'crear_abono', 'ver_abonos', 'gestionar_configuracion',
    'ver_dashboard', 'cancelar_citas'
]

def crear_permisos():
    """Crea todos los permisos granulares si no existen."""
    permisos_creados = []
    for entidad in ENTIDADES:
        for accion in ACCIONES:
            nombre = f"{accion}_{entidad}"
            if not Permiso.query.filter_by(nombre=nombre).first():
                db.session.add(Permiso(nombre=nombre))
                permisos_creados.append(nombre)
    for nombre in PERMISOS_ESPECIALES:
        if not Permiso.query.filter_by(nombre=nombre).first():
            db.session.add(Permiso(nombre=nombre))
            permisos_creados.append(nombre)
    db.session.commit()
    if permisos_creados:
        print(f"✅ Permisos creados ({len(permisos_creados)}): {permisos_creados[:5]}...")

def crear_roles():
    """Crea roles si no existen."""
    roles = ['Admin', 'Cliente']
    roles_creados = []
    for nombre_rol in roles:
        if not Rol.query.filter_by(nombre=nombre_rol).first():
            db.session.add(Rol(nombre=nombre_rol, descripcion=f'Rol {nombre_rol}', estado=True))
            roles_creados.append(nombre_rol)
    db.session.commit()
    if roles_creados:
        print(f"✅ Roles creados: {roles_creados}")

def asignar_permisos_a_admin():
    """Asigna todos los permisos existentes al rol Admin."""
    rol_admin = Rol.query.filter_by(nombre='Admin').first()
    if not rol_admin:
        print("❌ Rol Admin no encontrado, no se asignan permisos.")
        return
    todos_permisos = Permiso.query.all()
    asignados = 0
    for p in todos_permisos:
        if not PermisoPorRol.query.filter_by(rol_id=rol_admin.id, permiso_id=p.id).first():
            db.session.add(PermisoPorRol(rol_id=rol_admin.id, permiso_id=p.id))
            asignados += 1
    db.session.commit()
    print(f"✅ Asignados {asignados} permisos al rol Admin")

def crear_usuarios():
    """Crea:
    - Usuario administrador (con cliente asociado)
    - Usuario cliente estándar (con su cliente)
    """
    rol_admin = Rol.query.filter_by(nombre='Admin').first()
    rol_cliente = Rol.query.filter_by(nombre='Cliente').first()
    if not rol_admin or not rol_cliente:
        print("❌ Faltan roles, ejecuta primero crear_roles().")
        return

    # ----- Cliente para el Admin (mismo correo del admin) -----
    admin_email = "admin@visualoutlet.com"
    admin_pass = "Admin123"
    admin_cliente = None
    if not Usuario.query.filter_by(correo=admin_email).first():
        # Primero crear el cliente asociado al admin
        admin_cliente = Cliente(
            nombre="Admin",
            apellido="Cliente",
            tipo_documento="CC",
            numero_documento="999999999",
            fecha_nacimiento=date(1980, 1, 1),   # ← objeto date
            genero="Masculino",
            telefono="5550000",
            correo=admin_email,
            municipio="Bogotá",
            direccion="Calle Admin 123",
            departamento="Cundinamarca",
            barrio="Centro",
            codigo_postal="111111",
            ocupacion="Administrador",
            telefono_emergencia="5551111",
            estado=True
        )
        db.session.add(admin_cliente)
        db.session.flush()

        usuario_admin = Usuario(
            correo=admin_email,
            contrasenia=generate_password_hash(admin_pass),
            rol_id=rol_admin.id,
            cliente_id=admin_cliente.id,
            estado=True,
            nombre="Administrador",
            apellido="Sistema",
            telefono="5550001",
            tipo_documento="CC",
            numero_documento="111111111",
            fecha_nacimiento=date(1980, 1, 1)
        )
        db.session.add(usuario_admin)
        print(f"✅ Usuario Admin (con cliente) creado: {admin_email} / {admin_pass}")
    else:
        print(f"ℹ️ Usuario Admin ya existe: {admin_email}")

    # ----- Cliente estándar -----
    cliente_email = "cliente@test.com"
    cliente_pass = "Cliente123"
    if not Usuario.query.filter_by(correo=cliente_email).first():
        cliente_std = Cliente(
            nombre="Juan",
            apellido="Perez",
            tipo_documento="CC",
            numero_documento="12345678",
            fecha_nacimiento=date(1990, 1, 1),
            genero="Masculino",
            telefono="3001234567",
            correo=cliente_email,
            municipio="Bogotá",
            direccion="Calle 123",
            departamento="Cundinamarca",
            barrio="Chapinero",
            codigo_postal="110111",
            ocupacion="Estudiante",
            telefono_emergencia="3119876543",
            estado=True
        )
        db.session.add(cliente_std)
        db.session.flush()

        usuario_cliente = Usuario(
            correo=cliente_email,
            contrasenia=generate_password_hash(cliente_pass),
            rol_id=rol_cliente.id,
            cliente_id=cliente_std.id,
            estado=True,
            nombre="Juan",
            apellido="Perez",
            telefono="3001234567",
            tipo_documento="CC",
            numero_documento="12345678",
            fecha_nacimiento=date(1990, 1, 1)
        )
        db.session.add(usuario_cliente)
        print(f"✅ Usuario Cliente creado: {cliente_email} / {cliente_pass}")
    else:
        print(f"ℹ️ Usuario Cliente ya existe: {cliente_email}")

    db.session.commit()

def main():
    app = create_app()
    with app.app_context():
        crear_roles()
        crear_permisos()
        asignar_permisos_a_admin()
        crear_usuarios()
        print("\n🎉 Seed completado. Ahora el administrador tiene un cliente asociado (mismo correo).")

if __name__ == '__main__':
    main()