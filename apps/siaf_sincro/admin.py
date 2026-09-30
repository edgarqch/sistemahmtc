from django.contrib import admin
from apps.siaf_sincro.models import ProductoSiaf, PedidoAlmacen, DetallePedido

@admin.register(ProductoSiaf)
class ProductoSiafAdmin(admin.ModelAdmin):
    # Columnas que se mostrarán en el listado del panel web
    list_display = ('tipo_almacen', 'codigo_siaf', 'nombre', 'unidad_medida', 'stock_unidades', 'actualizado_el')
    
    # Filtros laterales rápidos (útil para cuando agregues Nutrición y Laboratorio)
    list_filter = ('tipo_almacen', 'unidad_medida')
    
    # Barra de búsqueda inteligente por código o por nombre del insumo
    search_fields = ('codigo_siaf', 'nombre')
    
    # Orden predeterminado: Primero por tipo de almacén y luego alfabéticamente por nombre
    ordering = ('tipo_almacen', 'nombre')
    
    # Hace que la fecha de actualización sea de solo lectura en el panel
    readonly_fields = ('actualizado_el',)


# Configuramos un diseño inline para ver el desglose de artículos dentro del mismo pedido
class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0  # No muestra filas vacías extras por defecto
    readonly_fields = ['producto', 'cantidad_solicitada'] # Evita edición accidental
    can_delete = False # Evita borrar detalles desde el admin para proteger la consistencia

@admin.register(PedidoAlmacen)
class PedidoAlmacenAdmin(admin.ModelAdmin):
    # Columnas que se mostrarán en el listado general del admin
    list_display = ('codigo_pedido', 'usuario', 'fecha_pedido', 'estado')
    
    # Filtros laterales convenientes
    list_filter = ('estado', 'fecha_pedido')
    
    # Buscador superior por código de pedido o nombre de usuario
    search_fields = ('codigo_pedido', 'usuario__username')
    
    # Hacemos el código de pedido de solo lectura
    readonly_fields = ['codigo_pedido', 'fecha_pedido']
    
    # Incrustamos la tabla de artículos seleccionados abajo de la cabecera
    inlines = [DetallePedidoInline]

# NOTA: Si aún no habías registrado ProductoSiaf, puedes descomentar la siguiente línea:
# admin.site.register(ProductoSiaf)

from .models import UnidadHospitalaria, DiscrepanciaInventario

# ... (Mantén aquí tus registros previos de PedidoAlmacen y ProductoSiaf) ...

@admin.register(UnidadHospitalaria)
class UnidadHospitalariaAdmin(admin.ModelAdmin):
    """Mapeo del catálogo de servicios médicos y estaciones de enfermería."""
    list_display = ('nombre', 'codigo_interno')
    search_fields = ('nombre', 'codigo_interno')
    ordering = ('nombre',)


@admin.register(DiscrepanciaInventario)
class DiscrepanciaInventarioAdmin(admin.ModelAdmin):
    """Bandeja de auditoría del Escudo de Deltas contra asimetrías del SIAF."""
    list_display = (
        'producto', 
        'stock_siaf_csv', 
        'stock_django_real', 
        'unidades_omitidas_siaf', 
        'detectado_el'
    )
    list_filter = ('detectado_el',)
    search_fields = ('producto__codigo_siaf', 'producto__nombre')
    ordering = ('-detectado_el',)
    
    # Bloqueamos la edición manual en el panel web para proteger la integridad de la auditoría
    readonly_fields = (
        'producto', 
        'stock_siaf_csv', 
        'stock_django_real', 
        'unidades_omitidas_siaf', 
        'detectado_el'
    )

    def has_add_permission(self, request):
        """Evita la creación manual de registros de discrepancia desde el admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Evita la eliminación accidental de registros de auditoría."""
        return False
