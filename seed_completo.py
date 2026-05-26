"""
Script completo para inicializar la base de datos con:
- Roles (Admin, Cliente, Optometra)
- Permisos granulares (CRUD + especiales con endpoints reales)
- Permiso especial 'cliente_acceso_basico' para el rol Cliente
- Datos de prueba (mínimo 2 registros por tabla principal)
- Usuarios: admin, cliente, optómetra

Nota: Para SQLite, los campos fecha deben ser objetos date, no strings.
"""

import sys
import os
from datetime import date, datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.Models.models import (
    Rol, Usuario, Cliente, Permiso, PermisoPorRol,
    Marca, CategoriaProducto, Producto, Imagen,
    Proveedor, Compra, DetalleCompra,
    Servicio, Empleado, Horario, EstadoCita, Cita,
    EstadoPedido, Pedido, DetallePedido, Abono,
    EstadoVenta, Venta, DetalleVenta, CampanaSalud
)
from werkzeug.security import generate_password_hash

# ============================================================
# 1. DEFINICIÓN DE PERMISOS (SOLO CON ENDPOINTS REALES)
# ============================================================

ENTIDADES_CRUD = [
    'usuarios', 'clientes', 'productos', 'ventas', 'citas',
    'empleados', 'proveedores', 'compras', 'pedidos',
    'marcas', 'categorias', 'servicios', 'campanas'
]
ACCIONES_CRUD = ['ver', 'crear', 'editar', 'eliminar']

# Permisos especiales que realmente tienen endpoints
PERMISOS_ESPECIALES = [
    'cambiar_estado_pedido',    # PUT /pedidos/<id>
    'cambiar_estado_cita',      # PUT /citas/<id>
    'cambiar_estado_venta',     # PUT /ventas/<id>
    'ver_imagenes',             # GET /imagenes, /imagenes/<id>, /imagenes/producto/<id>
    'subir_imagenes',           # POST /imagenes
    'eliminar_imagenes',        # DELETE /imagenes/<id>
    'gestionar_configuracion',  # CRUD de roles y permisos
    'ver_dashboard',            # Para el frontend
    'cliente_acceso_basico',    # Permiso mínimo para clientes (requerido por la lógica de negocio)
]

def crear_permisos():
    """Crea todos los permisos granulares (CRUD + especiales con endpoints)."""
    permisos_creados = []
    # CRUD
    for entidad in ENTIDADES_CRUD:
        for accion in ACCIONES_CRUD:
            nombre = f"{accion}_{entidad}"
            if not Permiso.query.filter_by(nombre=nombre).first():
                db.session.add(Permiso(nombre=nombre))
                permisos_creados.append(nombre)
    # Especiales
    for nombre in PERMISOS_ESPECIALES:
        if not Permiso.query.filter_by(nombre=nombre).first():
            db.session.add(Permiso(nombre=nombre))
            permisos_creados.append(nombre)
    db.session.commit()
    print(f"✅ Permisos creados ({len(permisos_creados)}): {permisos_creados[:10]}...")

def crear_roles():
    """Crea roles: Admin, Cliente, Optometra."""
    roles = ['Admin', 'Cliente', 'Optometra']
    roles_creados = []
    for nombre_rol in roles:
        if not Rol.query.filter_by(nombre=nombre_rol).first():
            db.session.add(Rol(nombre=nombre_rol, descripcion=f'Rol {nombre_rol}', estado=True))
            roles_creados.append(nombre_rol)
    db.session.commit()
    print(f"✅ Roles creados: {roles_creados}")

def asignar_permisos_a_admin():
    """Asigna TODOS los permisos al rol Admin."""
    rol_admin = Rol.query.filter_by(nombre='Admin').first()
    if not rol_admin:
        print("❌ Rol Admin no encontrado")
        return
    todos_permisos = Permiso.query.all()
    asignados = 0
    for p in todos_permisos:
        if not PermisoPorRol.query.filter_by(rol_id=rol_admin.id, permiso_id=p.id).first():
            db.session.add(PermisoPorRol(rol_id=rol_admin.id, permiso_id=p.id))
            asignados += 1
    db.session.commit()
    print(f"✅ Asignados {asignados} permisos al rol Admin")

def asignar_permisos_optometra():
    """Asigna permisos relevantes para optómetra (solo agenda)."""
    rol_opt = Rol.query.filter_by(nombre='Optometra').first()
    if not rol_opt:
        print("⚠️ Rol Optometra no encontrado")
        return
    permisos_optometra = [
        'ver_citas', 'crear_citas', 'editar_citas', 'eliminar_citas',
        'cambiar_estado_cita',
        'ver_empleados', 'crear_empleados', 'editar_empleados', 'eliminar_empleados',
        'ver_servicios',  # Para ver servicios al agendar
    ]
    asignados = 0
    for perm_nombre in permisos_optometra:
        p = Permiso.query.filter_by(nombre=perm_nombre).first()
        if p and not PermisoPorRol.query.filter_by(rol_id=rol_opt.id, permiso_id=p.id).first():
            db.session.add(PermisoPorRol(rol_id=rol_opt.id, permiso_id=p.id))
            asignados += 1
    db.session.commit()
    print(f"✅ Asignados {asignados} permisos al rol Optometra")

def asignar_permisos_cliente():
    """Asigna el permiso 'cliente_acceso_basico' al rol Cliente."""
    rol_cliente = Rol.query.filter_by(nombre='Cliente').first()
    if not rol_cliente:
        print("⚠️ Rol Cliente no encontrado")
        return
    permiso_basico = Permiso.query.filter_by(nombre='cliente_acceso_basico').first()
    if not permiso_basico:
        print("⚠️ Permiso 'cliente_acceso_basico' no encontrado, créelo primero")
        return
    if not PermisoPorRol.query.filter_by(rol_id=rol_cliente.id, permiso_id=permiso_basico.id).first():
        db.session.add(PermisoPorRol(rol_id=rol_cliente.id, permiso_id=permiso_basico.id))
        db.session.commit()
        print("✅ Asignado 'cliente_acceso_basico' al rol Cliente")
    else:
        print("ℹ️ El rol Cliente ya tiene el permiso básico")

def crear_usuarios():
    """Crea usuarios: Admin (con cliente), Cliente estándar, Optómetra."""
    rol_admin = Rol.query.filter_by(nombre='Admin').first()
    rol_cliente = Rol.query.filter_by(nombre='Cliente').first()
    rol_opt = Rol.query.filter_by(nombre='Optometra').first()
    if not all([rol_admin, rol_cliente, rol_opt]):
        print("❌ Faltan roles")
        return

    # Admin con cliente asociado
    admin_email = "admin@visualoutlet.com"
    admin_pass = "Admin123"
    if not Usuario.query.filter_by(correo=admin_email).first():
        admin_cliente = Cliente(
            nombre="Admin", apellido="Cliente", tipo_documento="CC", numero_documento="999999999",
            fecha_nacimiento=date(1980,1,1), genero="Masculino", telefono="5550000",
            correo=admin_email, municipio="Bogotá", direccion="Calle Admin 123",
            departamento="Cundinamarca", barrio="Centro", codigo_postal="111111",
            ocupacion="Administrador", telefono_emergencia="5551111", estado=True
        )
        db.session.add(admin_cliente)
        db.session.flush()
        usuario_admin = Usuario(
            correo=admin_email, contrasenia=generate_password_hash(admin_pass),
            rol_id=rol_admin.id, cliente_id=admin_cliente.id, estado=True,
            nombre="Administrador", apellido="Sistema", telefono="5550001",
            tipo_documento="CC", numero_documento="111111111", fecha_nacimiento=date(1980,1,1)
        )
        db.session.add(usuario_admin)
        print(f"✅ Admin creado: {admin_email} / {admin_pass}")
    else:
        print(f"ℹ️ Admin ya existe: {admin_email}")

    # Cliente estándar
    cliente_email = "cliente@test.com"
    cliente_pass = "Cliente123"
    if not Usuario.query.filter_by(correo=cliente_email).first():
        cliente_std = Cliente(
            nombre="Juan", apellido="Perez", tipo_documento="CC", numero_documento="12345678",
            fecha_nacimiento=date(1990,1,1), genero="Masculino", telefono="3001234567",
            correo=cliente_email, municipio="Bogotá", direccion="Calle 123",
            departamento="Cundinamarca", barrio="Chapinero", codigo_postal="110111",
            ocupacion="Estudiante", telefono_emergencia="3119876543", estado=True
        )
        db.session.add(cliente_std)
        db.session.flush()
        usuario_cliente = Usuario(
            correo=cliente_email, contrasenia=generate_password_hash(cliente_pass),
            rol_id=rol_cliente.id, cliente_id=cliente_std.id, estado=True,
            nombre="Juan", apellido="Perez", telefono="3001234567",
            tipo_documento="CC", numero_documento="12345678", fecha_nacimiento=date(1990,1,1)
        )
        db.session.add(usuario_cliente)
        print(f"✅ Cliente creado: {cliente_email} / {cliente_pass}")
    else:
        print(f"ℹ️ Cliente ya existe: {cliente_email}")

    # Optómetra
    opt_email = "optometra@visualoutlet.com"
    opt_pass = "Optometra123"
    if not Usuario.query.filter_by(correo=opt_email).first():
        empleado_opt = Empleado.query.filter_by(correo=opt_email).first()
        if not empleado_opt:
            empleado_opt = Empleado(
                nombre="Laura", apellido="Gómez", tipo_documento="CC", numero_documento="98765432",
                telefono="3009876543", correo=opt_email, direccion="Clínica 123",
                fecha_ingreso=date(2023,1,15), cargo="Optómetra", estado=True
            )
            db.session.add(empleado_opt)
            db.session.flush()
        usuario_opt = Usuario(
            correo=opt_email, contrasenia=generate_password_hash(opt_pass),
            rol_id=rol_opt.id, cliente_id=None, estado=True,
            nombre="Laura", apellido="Gómez", telefono="3009876543",
            tipo_documento="CC", numero_documento="98765432", fecha_nacimiento=date(1990,5,10)
        )
        db.session.add(usuario_opt)
        print(f"✅ Optometra creado: {opt_email} / {opt_pass}")
    else:
        print(f"ℹ️ Optometra ya existe: {opt_email}")

    db.session.commit()

# ============================================================
# 3. DATOS DE PRUEBA (poblar tablas con al menos 2 registros)
# ============================================================

def poblar_datos_prueba():
    """Inserta datos de ejemplo en todas las tablas principales."""
    
    # ----- Marcas -----
    marcas_data = ["Ray-Ban", "Oakley", "Polaroid"]
    marcas = []
    for nombre in marcas_data:
        m = Marca.query.filter_by(nombre=nombre).first()
        if not m:
            m = Marca(nombre=nombre, estado=True)
            db.session.add(m)
        marcas.append(m)
    db.session.commit()
    print("✅ Marcas cargadas")

    # ----- Categorías -----
    categorias_data = ["Lentes de Sol", "Monturas", "Lentes de Contacto"]
    categorias = []
    for nombre in categorias_data:
        cat = CategoriaProducto.query.filter_by(nombre=nombre).first()
        if not cat:
            cat = CategoriaProducto(nombre=nombre, descripcion=f"Categoría {nombre}", estado=True)
            db.session.add(cat)
        categorias.append(cat)
    db.session.commit()
    print("✅ Categorías cargadas")

    # ----- Productos (mínimo 3) -----
    productos_data = [
        ("Ray-Ban Aviator", 250000, 150000, 10, 5, "Lentes de sol clásicos"),
        ("Oakley Holbrook", 220000, 130000, 8, 4, "Diseño deportivo"),
        ("Polaroid Clip", 80000, 50000, 20, 5, "Clip polarizado")
    ]
    for idx, (nom, pv, pc, stock, smin, desc) in enumerate(productos_data):
        if not Producto.query.filter_by(nombre=nom).first():
            prod = Producto(
                nombre=nom, precio_venta=pv, precio_compra=pc, stock=stock,
                stock_minimo=smin, descripcion=desc, estado=True,
                categoria_producto_id=categorias[idx % len(categorias)].id,
                marca_id=marcas[idx % len(marcas)].id
            )
            db.session.add(prod)
    db.session.commit()
    print("✅ Productos cargados")

    # ----- Proveedores (2) -----
    proveedores_data = [
        ("Distribuidora Óptica SAS", "NIT", "900123456-1", "Juan Pérez", "3101234567", "juan@optidist.com", "Bogotá", "Calle 1 #2-3"),
        ("Lentes del Mundo", "NIT", "900987654-2", "Ana Gómez", "3117654321", "ana@lentesmundo.com", "Medellín", "Carrera 4 #5-6")
    ]
    for razon, tipo_doc, doc, contacto, tel, mail, depto, dir in proveedores_data:
        if not Proveedor.query.filter_by(documento=doc).first():
            prov = Proveedor(
                razon_social_o_nombre=razon, tipo_documento=tipo_doc, documento=doc,
                contacto=contacto, telefono=tel, correo=mail, departamento=depto,
                municipio=depto, direccion=dir, estado=True
            )
            db.session.add(prov)
    db.session.commit()
    print("✅ Proveedores cargados")

    # ----- Compra de ejemplo -----
    proveedor1 = Proveedor.query.first()
    producto1 = Producto.query.first()
    if proveedor1 and producto1 and not Compra.query.first():
        compra = Compra(proveedor_id=proveedor1.id, total=0, estado_compra=True, fecha=datetime.utcnow())
        db.session.add(compra)
        db.session.flush()
        detalle = DetalleCompra(compra_id=compra.id, producto_id=producto1.id, cantidad=10, precio_unidad=150000, subtotal=1500000)
        db.session.add(detalle)
        compra.total = 1500000
        db.session.commit()
        print("✅ Compra de ejemplo creada")

    # ----- Empleados (3) -----
    empleados_data = [
        ("Carlos", "Méndez", "CC", "12345678", "300111222", "carlos@optik.com", date(2023,1,10), "Optómetra Jefe"),
        ("Ana", "López", "CC", "87654321", "300333444", "ana@optik.com", date(2023,2,15), "Optómetra"),
        ("Laura", "Gómez", "CC", "98765432", "3009876543", "laura@optik.com", date(2023,3,20), "Optómetra")
    ]
    for nom, ape, tipo_doc, num_doc, tel, mail, fecha_ing, cargo in empleados_data:
        if not Empleado.query.filter_by(numero_documento=num_doc).first():
            emp = Empleado(
                nombre=nom, apellido=ape, tipo_documento=tipo_doc, numero_documento=num_doc,
                telefono=tel, correo=mail, fecha_ingreso=fecha_ing, cargo=cargo, estado=True
            )
            db.session.add(emp)
    db.session.commit()
    print("✅ Empleados cargados")

    # ----- Horarios para empleados (lunes a viernes) -----
    for emp in Empleado.query.all():
        if not Horario.query.filter_by(empleado_id=emp.id).first():
            for dia in range(0,5):
                h = Horario(
                    empleado_id=emp.id, dia=dia,
                    hora_inicio=datetime.strptime("08:00","%H:%M").time(),
                    hora_final=datetime.strptime("17:00","%H:%M").time(),
                    activo=True
                )
                db.session.add(h)
    db.session.commit()
    print("✅ Horarios cargados")

    # ----- Servicios (3) -----
    servicios_data = [
        ("Examen de la Vista", 30, 50000, "Evaluación completa"),
        ("Adaptación de Lentes de Contacto", 45, 80000, "Entrenamiento"),
        ("Ajuste de Monturas", 15, 15000, "Ajuste y reparación")
    ]
    for nom, dur, prec, desc in servicios_data:
        if not Servicio.query.filter_by(nombre=nom).first():
            serv = Servicio(nombre=nom, duracion_min=dur, precio=prec, descripcion=desc, estado=True)
            db.session.add(serv)
    db.session.commit()
    print("✅ Servicios cargados")

    # ----- Estados de cita -----
    estados_cita = ["Pendiente", "Confirmada", "Completada", "Cancelada"]
    for ec in estados_cita:
        if not EstadoCita.query.filter_by(nombre=ec).first():
            db.session.add(EstadoCita(nombre=ec))
    db.session.commit()
    print("✅ Estados de cita cargados")

    # ----- Citas (mínimo 2) -----
    cliente_prueba = Cliente.query.filter_by(correo="cliente@test.com").first()
    empleado_opt = Empleado.query.filter_by(nombre="Laura").first() or Empleado.query.first()
    servicio = Servicio.query.first()
    estado_pendiente = EstadoCita.query.filter_by(nombre="Pendiente").first()
    if cliente_prueba and empleado_opt and servicio and estado_pendiente and Cita.query.count() < 2:
        fecha = date.today() + timedelta(days=1)
        cita1 = Cita(
            cliente_id=cliente_prueba.id, servicio_id=servicio.id, empleado_id=empleado_opt.id,
            estado_cita_id=estado_pendiente.id, fecha=fecha,
            hora=datetime.strptime("10:00","%H:%M").time(), duracion=servicio.duracion_min
        )
        cita2 = Cita(
            cliente_id=cliente_prueba.id, servicio_id=servicio.id, empleado_id=empleado_opt.id,
            estado_cita_id=estado_pendiente.id, fecha=fecha + timedelta(days=1),
            hora=datetime.strptime("11:30","%H:%M").time(), duracion=servicio.duracion_min
        )
        db.session.add_all([cita1, cita2])
        db.session.commit()
        print("✅ Citas de ejemplo creadas")

    # ----- Estados de pedido -----
    estados_pedido = ["pendiente", "confirmado", "pagado", "anulado"]
    for ep in estados_pedido:
        if not EstadoPedido.query.filter_by(nombre=ep).first():
            db.session.add(EstadoPedido(nombre=ep))
    db.session.commit()
    print("✅ Estados de pedido cargados")

    # ----- Pedido de ejemplo -----
    cliente = Cliente.query.first()
    producto = Producto.query.first()
    estado_pedido_pendiente = EstadoPedido.query.filter_by(nombre='pendiente').first()
    if cliente and producto and estado_pedido_pendiente and not Pedido.query.first():
        pedido = Pedido(
            cliente_id=cliente.id, total=0, metodo_pago='efectivo', metodo_entrega='tienda',
            estado_id=estado_pedido_pendiente.id, abono_acumulado=0
        )
        db.session.add(pedido)
        db.session.flush()
        detalle = DetallePedido(pedido_id=pedido.id, producto_id=producto.id, cantidad=2, precio_unitario=producto.precio_venta, subtotal=2*producto.precio_venta)
        db.session.add(detalle)
        pedido.total = 2*producto.precio_venta
        db.session.commit()
        print("✅ Pedido de ejemplo creado")

    # ----- Abono de ejemplo (opcional, para probar) -----
    if not Abono.query.first():
        abono = Abono(pedido_id=pedido.id, monto=50000, observacion="Primer abono")
        db.session.add(abono)
        pedido.abono_acumulado = 50000
        db.session.commit()
        print("✅ Abono de ejemplo creado")

    # ----- Estados de venta -----
    estados_venta = ["completada", "cancelada"]
    for ev in estados_venta:
        if not EstadoVenta.query.filter_by(nombre=ev).first():
            db.session.add(EstadoVenta(nombre=ev))
    db.session.commit()
    print("✅ Estados de venta cargados")

    # ----- Venta de ejemplo -----
    estado_venta_completada = EstadoVenta.query.filter_by(nombre='completada').first()
    if cliente and producto and estado_venta_completada and not Venta.query.first():
        venta = Venta(
            cliente_id=cliente.id, total=producto.precio_venta, metodo_pago='efectivo',
            metodo_entrega='tienda', fecha_venta=datetime.utcnow(), estado_id=estado_venta_completada.id
        )
        db.session.add(venta)
        db.session.flush()
        detalle_venta = DetalleVenta(venta_id=venta.id, producto_id=producto.id, cantidad=1, precio_unitario=producto.precio_venta, subtotal=producto.precio_venta)
        db.session.add(detalle_venta)
        db.session.commit()
        print("✅ Venta de ejemplo creada")

    # ----- Campañas de Salud (ejemplo) -----
    campana_data = [
        ("OptiSalud", "900123456", "Carlos López", date.today() + timedelta(days=5), "09:00", "Centro Comercial", "Jornada de salud visual", "descripción"),
        ("Visión para Todos", "900987654", "Ana María", date.today() + timedelta(days=10), "14:00", "Parque Principal", "Exámenes gratuitos", "sin observaciones")
    ]
    for emp, nit, cont, fecha, hora, dir, desc, obs in campana_data:
        if not CampanaSalud.query.filter_by(empresa=emp).first():
            camp = CampanaSalud(
                empresa=emp, nit_empresa=nit, contacto=cont, fecha=fecha,
                hora=datetime.strptime(hora, "%H:%M").time(), direccion=dir,
                descripcion=desc, observaciones=obs, estado_cita_id=1, empleado_id=empleado_opt.id
            )
            db.session.add(camp)
    db.session.commit()
    print("✅ Campañas de ejemplo creadas")

    print("✅ Datos de prueba poblados")

# ============================================================
# 4. EJECUCIÓN PRINCIPAL
# ============================================================

def main():
    app = create_app()
    with app.app_context():
        crear_roles()
        crear_permisos()
        asignar_permisos_a_admin()
        asignar_permisos_optometra()
        asignar_permisos_cliente()
        crear_usuarios()
        poblar_datos_prueba()
        print("\n🎉 Seed completado. Datos de prueba creados.")

if __name__ == '__main__':
    main()