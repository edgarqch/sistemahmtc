from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from .models import ProductoSiaf, PedidoAlmacen, DetallePedido

from django.contrib.auth.decorators import login_required, user_passes_test

@login_required
def pagina_inicio(request):
    """Renderiza el cuadro de mando dinámico de bienvenida del hospital."""
    return render(request, 'siaf_sincro/inicio.html')

# =========================================================================
# 🛡️ CONTROL DE ACCESO INTEGRAL POR ROLES DE NEGOCIO Y SUPERUSUARIO
# =========================================================================

def es_solicitante(user):
    """Permite el acceso a miembros de Solicitantes o al Administrador de TI."""
    return user.groups.filter(name='Solicitantes_Almacen').exists() or user.is_superuser

def es_aprobador(user):
    """Permite el acceso a miembros de Aprobadores (Dirección) o al Administrador de TI."""
    return user.groups.filter(name='Aprobadores_Almacen').exists() or user.is_superuser

def es_almacenero(user):
    """Permite el acceso al personal de Almacén (Despacho) o al Administrador de TI."""
    return user.groups.filter(name='Almaceneros_Almacen').exists() or user.is_superuser

@login_required
@user_passes_test(es_solicitante, login_url='index')
def listado_productos_siaf(request):
    # 1. PASO: DETECTAR SI ES UNA PETICIÓN DE GUARDADO (POST)
    if request.method == 'POST':
        # Capturamos los datos que viajan desde el formulario del carrito modal
        justificacion = request.POST.get('justificacion')
        productos_ids = request.POST.getlist('producto_id[]')
        cantidades = request.POST.getlist('cantidad[]')

        # Validación de seguridad del lado del servidor
        if not productos_ids:
            messages.error(request, "Error: El carrito de pedidos está vacío.")
            return redirect('siaf_sincro:listado_items')

        try:
            # 2. PASO: ABRIR UNA TRANSACCIÓN SEGURA EN POSTGRESQL
            with transaction.atomic():
                # Creamos la cabecera del documento asociando al usuario logueado
                pedido = PedidoAlmacen.objects.create(
                    usuario=request.user,
                    justificacion=justificacion,
                    estado='PENDIENTE'
                )

                # Recorremos en paralelo los identificadores y cantidades recibidos
                for prod_id, cant in zip(productos_ids, cantidades):
                    producto = ProductoSiaf.objects.get(id=prod_id)
                    
                    # Insertamos cada ítem en el desglose
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=producto,
                        cantidad_solicitada=int(cant)
                    )

            # Si todo el bucle se completa con éxito, mandamos un mensaje de confirmación
            messages.success(request, f"¡Éxito! El pedido {pedido.codigo_pedido} ha sido registrado de forma correcta.")
            return redirect('siaf_sincro:historial_pedidos')

        except Exception as e:
            # Si algo falla (ej. se cae la red o el ID no existe), la transacción se deshace (rollback)
            messages.error(request, f"Error crítico al guardar el documento de pedido: {str(e)}")
            return redirect('siaf_sincro:listado_items')

    # 3. PASO: SI ES UNA PETICIÓN NORMAL (GET), SOLAMENTE RENDERIZA EL CATALOGO
    productos = ProductoSiaf.objects.filter(tipo_almacen='CENTRAL')
    context = {
        'productos': productos,
        'titulo_pagina': 'Catálogo de Almacén Central (General)'
    }
    return render(request, 'siaf_sincro/listar_productos.html', context)

@login_required
@user_passes_test(es_solicitante, login_url='index')
def historial_pedidos_siaf(request):
    # Traemos los pedidos del usuario logueado, ordenados del más reciente al más antiguo
    pedidos = PedidoAlmacen.objects.filter(usuario=request.user)
    
    context = {
        'pedidos': pedidos,
        'titulo_pagina': 'Mis Pedidos de Almacén'
    }
    return render(request, 'siaf_sincro/historial_pedidos.html', context)


import io
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import PedidoAlmacen

@login_required
def generar_pdf_pedido(request, pedido_id):
    try:
        # Buscamos el pedido asegurando que pertenezca al usuario logueado (por seguridad)
        pedido = PedidoAlmacen.objects.get(id=pedido_id, usuario=request.user)
    except PedidoAlmacen.DoesNotExist:
        messages.error(request, "El documento solicitado no existe o no tiene permisos para verlo.")
        return redirect('siaf_sincro:historial_pedidos')

    # Traemos todos los detalles (productos) asociados a este pedido maestro
    detalles = pedido.detalles.all()

    context = {
        'pedido': pedido,
        'detalles': detalles,
        'hospital_nombre': 'HOSPITAL MADRE TERESA DE CALCUTA'
    }

    # Cargamos el template HTML exclusivo que diseñaremos para el formato de impresión
    template = get_template('siaf_sincro/pdf_pedido_formato.html')
    html = template.render(context)
    
    # Creamos un buffer en memoria RAM para procesar el PDF binario
    result = io.BytesIO()
    
    # El motor PISA convierte el HTML + CSS en un PDF real
    pisa_status = pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=result)
    
    if pisa_status.err:
        return HttpResponse('Ocurrió un error técnico al generar el PDF', status=500)
        
    # Preparamos la respuesta del navegador para que fuerce la descarga o apertura del archivo
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Documento_{pedido.codigo_pedido}.pdf"'
    return response



# Control de seguridad: Verifica que el usuario sea administrador o personal autorizado
def es_administrador(user):
    return user.is_staff or user.groups.filter(name='Administracion').exists()

@login_required
@user_passes_test(es_aprobador, login_url='index')
def listado_autorizaciones_siaf(request):
    # Traemos solo los pedidos que están esperando firma del Director/Admin
    pedidos_pendientes = PedidoAlmacen.objects.filter(estado='PENDIENTE')
    
    context = {
        'pedidos': pedidos_pendientes,
        'titulo_pagina': 'Autorización de Pedidos (Dirección / Administración)'
    }
    return render(request, 'siaf_sincro/autorizar_pedidos.html', context)

@login_required
@user_passes_test(es_aprobador, login_url='index')
def procesar_autorizacion_siaf(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(PedidoAlmacen, id=pedido_id)
        accion = request.POST.get('accion') # Puede ser 'AUTORIZAR' o 'RECHAZAR'
        
        if pedido.estado != 'PENDIENTE':
            messages.warning(request, f"El pedido {pedido.codigo_pedido} ya fue procesado previamente.")
            return redirect('siaf_sincro:listado_autorizaciones')
            
        if accion == 'AUTORIZAR':
            pedido.estado = 'AUTORIZADO'
            pedido.save()
            messages.success(request, f"El pedido {pedido.codigo_pedido} ha sido AUTORIZADO con éxito. Pasó a Almacén Central.")
        elif accion == 'RECHAZAR':
            pedido.estado = 'RECHAZADO'
            pedido.save()
            messages.warning(request, f"El pedido {pedido.codigo_pedido} ha sido RECHAZADO.")
            
        return redirect('siaf_sincro:listado_autorizaciones')

@login_required
@user_passes_test(es_almacenero, login_url='index')
def listado_despachos_siaf(request):
    # El almacenero solo ve los pedidos que ya fueron autorizados por la Dirección
    pedidos_autorizados = PedidoAlmacen.objects.filter(estado='AUTORIZADO')
    
    context = {
        'pedidos': pedidos_autorizados,
        'titulo_pagina': 'Despacho y Entrega de Pedidos (Responsable de Almacén)'
    }
    return render(request, 'siaf_sincro/despachar_pedidos.html', context)

@login_required
@user_passes_test(es_almacenero, login_url='index')
def procesar_entrega_siaf(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(PedidoAlmacen, id=pedido_id)
        
        if pedido.estado != 'AUTORIZADO':
            messages.warning(request, f"El pedido {pedido.codigo_pedido} no está autorizado o ya fue entregado.")
            return redirect('siaf_sincro:listado_despachos')
            
        try:
            # Cambiamos el estado a ENTREGADO. El método save() del modelo se encargará 
            # de validar el stock y restar las unidades automáticamente en PostgreSQL.
            pedido.estado = 'ENTREGADO'
            pedido.save()
            messages.success(request, f"¡Éxito! El pedido {pedido.codigo_pedido} ha sido registrado como ENTREGADO y el stock fue actualizado.")
            
        except ValueError as e:
            # Si el modelo detecta que no hay suficiente stock en ese instante, cancela y avisa:
            messages.error(request, str(e))
            
        return redirect('siaf_sincro:listado_despachos')

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib import messages

class CambiarPasswordTemporalView(PasswordChangeView):
    template_name = 'registration/cambiar_password_obligatorio.html'
    success_url = reverse_lazy('siaf_sincro:inicio')

    def form_valid(self, form):
        # Al procesarse el cambio con éxito, destruimos la bandera en la sesión
        if 'clave_temporal' in self.request.session:
            self.request.session['clave_temporal'] = False
            
        messages.success(self.request, "¡Contraseña actualizada con éxito! Ya puedes navegar en el sistema.")
        return super().form_valid(form)
