from django.db import models

class ProductoSiaf(models.Model):
    # Opciones para clasificar los almacenes a futuro
    ALMACEN_CHOICES = [
        ('CENTRAL', 'Almacén Central (General)'),
        ('NUTRICION', 'Almacén de Nutrición'),
        ('LABORATORIO', 'Almacén de Laboratorio'),
    ]

    # 1. Código oficial alfanumérico (MED_CODIFICACION en el SIAF)
    # Agregamos unique=False porque un mismo código podría existir en Almacén y Nutrición
    codigo_siaf = models.CharField(max_length=50, verbose_name="Código SIAF")
    
    # 2. Descripción comercial (MED_COMERCIAL en el SIAF)
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Producto")
    
    # 3. Unidad de medida (med_unidad en el SIAF)
    unidad_medida = models.CharField(max_length=50, verbose_name="Unidad de Medida")
    
    # 4. Stock calculado disponible (Suma/Resta de movimientos del SIAF)
    stock_unidades = models.IntegerField(default=0, verbose_name="Stock Disponible")
    
    # 5. Campo crítico de escalabilidad: Identifica a qué almacén pertenece este ítem localmente
    tipo_almacen = models.CharField(
        max_length=20, 
        choices=ALMACEN_CHOICES, 
        default='CENTRAL',
        verbose_name="Tipo de Almacén"
    )
    
    # 6. Registro de control: Saber cuándo se sincronizó por última vez
    actualizado_el = models.DateTimeField(auto_now=True, verbose_name="Última Sincronización")

    class Meta:
        verbose_name = "Producto SIAF"
        verbose_name_plural = "Productos SIAF"
        # Restricción única compuesta: Un código solo puede repetirse si es de almacenes distintos
        unique_together = ('codigo_siaf', 'tipo_almacen')
        # Añadimos un índice para que las búsquedas en Django sean instantáneas
        indexes = [
            models.Index(fields=['codigo_siaf', 'tipo_almacen']),
        ]

    def __str__(self):
        return f"[{self.tipo_almacen}] {self.codigo_siaf} - {self.nombre}"
