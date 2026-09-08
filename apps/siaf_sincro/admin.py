from django.contrib import admin
from apps.siaf_sincro.models import ProductoSiaf

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
