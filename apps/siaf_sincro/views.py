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
        unidad_id = request.POST.get('unidad_id')
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
                    unidad_id=unidad_id, # <--- SE GUARDA LA UNIDAD SELECCIONADA
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

    # Agregamos las unidades al contexto de renderizado
    from .models import UnidadHospitalaria
    unidades = UnidadHospitalaria.objects.all()
    productos = ProductoSiaf.objects.filter(tipo_almacen='CENTRAL')
    context = {
        'productos': productos,
        'unidades': unidades,
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
        # Nota: Se eliminó la restricción estricta de 'usuario=request.user' 
        # por si a futuro el almacenero o administrador también necesita imprimirlo.
        pedido = PedidoAlmacen.objects.get(id=pedido_id)
    except PedidoAlmacen.DoesNotExist:
        messages.error(request, "Documento no disponible.")
        return redirect('siaf_sincro:historial_pedidos')
    
    context = {
        'pedido': pedido, 
        'detalles': pedido.detalles.all(), 
        'hospital_nombre': 'HOSPITAL MADRE TERESA DE CALCUTA'
    }
    
    # ESTRATEGIA: Si el pedido ya fue entregado, muestra el formato de entrega con firmas.
    # Si está PENDIENTE o AUTORIZADO, muestra el ticket de comprobación para el solicitante.
    if pedido.estado == 'ENTREGADO':
        template = get_template('siaf_sincro/pdf_pedido_formato.html')
    else:
        template = get_template('siaf_sincro/pdf_ticket_comprobante.html')
        
    html = template.render(context)
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=result)
    
    if pisa_status.err:
        return HttpResponse('Error técnico al generar el PDF', status=500)
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Ticket_{pedido.codigo_pedido}.pdf"'
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

from django.utils import timezone
import hashlib

@login_required
@user_passes_test(es_administrador, login_url='index')
def procesar_autorizacion_siaf(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(PedidoAlmacen, id=pedido_id)
        accion = request.POST.get('accion')
        
        if pedido.estado != 'PENDIENTE':
            messages.warning(request, "El pedido ya fue procesado.")
            return redirect('siaf_sincro:listado_autorizaciones')
            
        if accion == 'AUTORIZAR':
            pedido.estado = 'AUTORIZADO'
            
            # INYECCIÓN DE FIRMA DIGITAL POR SISTEMA
            pedido.usuario_autoriza = request.user
            pedido.fecha_autorizacion = timezone.now()
            
            # Generamos un hash único combinando datos del pedido y el usuario para blindar el PDF
            cadena_firma = f"{pedido.codigo_pedido}-{request.user.username}-{pedido.fecha_autorizacion}"
            pedido.firma_hash = hashlib.sha256(cadena_firma.encode('utf-8')).hexdigest()[:16].upper()
            
            pedido.save()
            messages.success(request, f"El pedido {pedido.codigo_pedido} ha sido AUTORIZADO electrónicamente.")
        
        elif accion == 'RECHAZAR':
            pedido.estado = 'RECHAZADO'
            pedido.save()
            messages.warning(request, f"El pedido {pedido.codigo_pedido} ha sido RECHAZADO.")
            
        return redirect('siaf_sincro:listado_autorizaciones')


@login_required
@user_passes_test(es_almacenero, login_url='index')
def listado_despachos_siaf(request):
    # 1. Pedidos pendientes de entrega física (Ventanilla)
    pedidos_autorizados = PedidoAlmacen.objects.filter(estado='AUTORIZADO')
    # 2. Historial de pedidos ya despachados por el almacén (Últimos 100 para optimizar RAM)
    pedidos_entregados = PedidoAlmacen.objects.filter(estado='ENTREGADO').order_by('-fecha_pedido')[:100]
    
    context = {
        'pedidos': pedidos_autorizados,
        'pedidos_entregados': pedidos_entregados,
        'titulo_pagina': 'Despacho, Entrega e Impresión de Pedidos (Responsable de Almacén)'
    }
    return render(request, 'siaf_sincro/despachar_pedidos.html', context)

@login_required
@user_passes_test(es_almacenero, login_url='index') # Blindado para Bodega
def procesar_entrega_siaf(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(PedidoAlmacen, id=pedido_id)
        
        if pedido.estado != 'AUTORIZADO':
            messages.warning(request, "El pedido no está autorizado o ya fue procesado.")
            return redirect('siaf_sincro:listado_despachos')
            
        try:
            with transaction.atomic():
                detalles_ids = request.POST.getlist('detalle_id[]')
                cantidades_despachadas = request.POST.getlist('cantidad_despachada[]')
                
                # Respaldo contra aplanamiento de arrays del navegador
                if not detalles_ids:
                    detalles_ids = request.POST.get('detalle_id[]')
                    detalles_ids = [detalles_ids] if detalles_ids else []
                if not cantidades_despachadas:
                    cantidades_despachadas = request.POST.get('cantidad_despachada[]')
                    cantidades_despachadas = [cantidades_despachadas] if cantidades_despachadas else []

                # Procesamiento e impacto de renglones
                if not detalles_ids or len(detalles_ids) == 0:
                    detalles_directos = pedido.detallepedido_set.all()
                    if not detalles_directos.exists():
                        detalles_directos = pedido.detalles.all()
                        
                    for detalle in detalles_directos:
                        detalle.cantidad_despachada = detalle.cantidad_solicitada
                        detalle.save() # Aquí saltará la regla si no hay stock
                else:
                    for d_id, cant_desp in zip(detalles_ids, cantidades_despachadas):
                        if not d_id or cant_desp is None or cant_desp == '':
                            continue
                            
                        detalle = DetallePedido.objects.filter(id=int(d_id), pedido=pedido).first()
                        if not detalle:
                            continue
                            
                        nueva_cantidad = int(cant_desp)
                        if nueva_cantidad > detalle.cantidad_solicitada:
                            raise ValueError(f"No puedes despachar más de lo solicitado en: {detalle.producto.nombre}")
                        
                        detalle.cantidad_despachada = nueva_cantidad
                        detalle.save() # Aquí saltará la regla si no hay stock
                
                # Consolidación final de la orden en PostgreSQL
                pedido.estado = 'ENTREGADO'
                try:
                    pedido.fecha_entrega = timezone.now()
                except Exception:
                    pedido.fecha_entrega = datetime.now()
                pedido.save()
                
            messages.success(request, f"¡Éxito! El pedido {pedido.codigo_pedido} ha sido despachado correctamente.")
            return redirect('siaf_sincro:listado_despachos') # Éxito: redirección normal
            
        except (ValueError, Exception) as e:
            # ========================================================
            # 🛡️ RENDER DIRECTO CONTRA CONFLICTOS DE REDIRECCIÓN 🛡️
            # ========================================================
            error_msg = f"No se puede despachar: {str(e)}"
            
            # Recreamos las mismas consultas exactas de tu función listado_despachos_siaf
            pedidos_autorizados = PedidoAlmacen.objects.filter(estado='AUTORIZADO')
            pedidos_entregados = PedidoAlmacen.objects.filter(estado='ENTREGADO').order_by('-fecha_pedido')[:100]
            
            context = {
                'pedidos': pedidos_autorizados,
                'pedidos_entregados': pedidos_entregados,
                'titulo_pagina': 'Despacho, Entrega e Impresión de Pedidos (Responsable de Almacén)',
                'error_inventario': error_msg  # Inyectamos el texto del stock directo al HTML
            }
            return render(request, 'siaf_sincro/despachar_pedidos.html', context)


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

from apps.siaf_sincro.models import DiscrepanciaInventario

def es_administrador(user):
    return user.is_staff or user.groups.filter(name='Aprobadores_Almacen').exists() or user.is_superuser

@login_required
@user_passes_test(es_administrador, login_url='index')
def reporte_discrepancias(request):
    alertas = DiscrepanciaInventario.objects.select_related('producto').filter(unidades_omitidas_siaf__gt=0)
    return render(request, 'siaf_sincro/reporte_discrepancias.html', {
        'alertas': alertas,
        'titulo_pagina': 'Auditoría: Discrepancias de Inventario SIAF'
    })
