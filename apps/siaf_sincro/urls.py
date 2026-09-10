from django.urls import path
from apps.siaf_sincro import views

# Definimos el namespace de la aplicación
app_name = 'siaf_sincro'

urlpatterns = [
    path('inicio/', views.pagina_inicio, name='inicio'),
    path('almacen/central/items/', views.listado_productos_siaf, name='listado_items'),
    path('almacen/pedidos/historial/', views.historial_pedidos_siaf, name='historial_pedidos'),
    path('almacen/pedido/pdf/<int:pedido_id>/', views.generar_pdf_pedido, name='generar_pdf'),
    path('almacen/autorizaciones/', views.listado_autorizaciones_siaf, name='listado_autorizaciones'),
    path('almacen/autorizaciones/procesar/<int:pedido_id>/', views.procesar_autorizacion_siaf, name='procesar_autorizacion'),
    path('almacen/despachos/', views.listado_despachos_siaf, name='listado_despachos'),
    path('almacen/despachos/entregar/<int:pedido_id>/', views.procesar_entrega_siaf, name='procesar_entrega'),
    path('cambiar-contrasena/', views.CambiarPasswordTemporalView.as_view(), name='cambiar_password'),
]
