"""
Script para crear permisos granulares CRUD en la base de datos.
Ejecutar: python seed_permisos.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.Models.models import Permiso, Rol, PermisoPorRol

def seed_permisos():
    app = create_app()
    with app.app_context():
        # Permisos CRUD para cada entidad
        entidades = ['usuarios', 'clientes', 'productos', 'ventas', 'citas', 'empleados', 'proveedores']
        acciones = ['ver', 'crear', 'editar', 'eliminar']
        permisos_creados = []
        for entidad in entidades:
            for accion in acciones:
                nombre = f"{accion}_{entidad}"
                if not Permiso.query.filter_by(nombre=nombre).first():
                    db.session.add(Permiso(nombre=nombre))
                    permisos_creados.append(nombre)
        # Permisos adicionales
        especiales = ['ver_reportes', 'gestionar_configuracion', 'cancelar_citas']
        for esp in especiales:
            if not Permiso.query.filter_by(nombre=esp).first():
                db.session.add(Permiso(nombre=esp))
                permisos_creados.append(esp)
        db.session.commit()
        print(f"✅ Permisos creados: {permisos_creados}")

        # Asignar todos los permisos al rol Admin
        rol_admin = Rol.query.filter_by(nombre='Admin').first()
        if rol_admin:
            todos = Permiso.query.all()
            for p in todos:
                if not PermisoPorRol.query.filter_by(rol_id=rol_admin.id, permiso_id=p.id).first():
                    db.session.add(PermisoPorRol(rol_id=rol_admin.id, permiso_id=p.id))
            db.session.commit()
            print("✅ Todos los permisos asignados a Admin")
        else:
            print("⚠️ Rol 'Admin' no encontrado, crea el rol primero.")

        # Opcional: asignar algunos permisos a Optometra
        rol_opto = Rol.query.filter_by(nombre='Optometra').first()
        if rol_opto:
            permisos_opto = ['ver_clientes', 'ver_citas', 'crear_citas', 'editar_citas', 'ver_ventas']
            for nombre_perm in permisos_opto:
                p = Permiso.query.filter_by(nombre=nombre_perm).first()
                if p and not PermisoPorRol.query.filter_by(rol_id=rol_opto.id, permiso_id=p.id).first():
                    db.session.add(PermisoPorRol(rol_id=rol_opto.id, permiso_id=p.id))
            db.session.commit()
            print("✅ Permisos asignados a Optometra")

if __name__ == '__main__':
    seed_permisos()