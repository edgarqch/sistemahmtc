from django.db import models
from django.contrib.auth.models import User

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

# 1. NUEVA TABLA MAESTRA DE UNIDADES DEL HOSPITAL
class UnidadHospitalaria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Unidad/Servicio")
    codigo_interno = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Código Interno (Opcional)")

    class Meta:
        verbose_name = "Unidad Hospitalaria"
        verbose_name_plural = "Unidades Hospitalarias"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

from django.contrib.auth.models import User
# NOTA: No importamos ProductoSiaf porque ya existe arriba en este mismo archivo

class PedidoAlmacen(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de Autorización'),
        ('AUTORIZADO', 'Autorizado por Dirección/Admin'),
        ('ENTREGADO', 'Entregado / Despachado (Almacén)'),
        ('RECHAZADO', 'Rechazado'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Solicitante")
    fecha_pedido = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud")
    justificacion = models.TextField(verbose_name="Justificación o Destino")
    estado = models.CharField(max_length=40, choices=ESTADO_CHOICES, default='PENDIENTE', verbose_name="Estado")
    codigo_pedido = models.CharField(max_length=20, unique=True, verbose_name="Nro. Pedido", editable=False)
    usuario_autoriza = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name="pedidos_autorizados", 
        verbose_name="Autorizado por"
    )
    fecha_autorizacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Autorización")
    firma_hash = models.CharField(max_length=64, null=True, blank=True, verbose_name="Token Digital de Seguridad")
    unidad = models.ForeignKey(
        UnidadHospitalaria, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name="pedidos",
        verbose_name="Unidad Solicitante"
    )

    class Meta:
        verbose_name = "Pedido de Almacén"
        verbose_name_plural = "Pedidos de Almacén"
        ordering = ['-fecha_pedido']

    def __str__(self):
        return f"Pedido {self.codigo_pedido} - {self.usuario.username} ({self.get_estado_display()})"

    def save(self, *args, **kwargs):
        if not self.codigo_pedido:
            ultimo_pedido = PedidoAlmacen.objects.order_by('id').last()
            self.codigo_pedido = 'PED-00001' if not ultimo_pedido else f'PED-{(ultimo_pedido.id + 1):05d}'
        
        if self.pk:  
            pedido_anterior = PedidoAlmacen.objects.get(pk=self.pk)
            
            # El stock SOLO se descuenta cuando el estado cambia a ENTREGADO
            if pedido_anterior.estado != 'ENTREGADO' and self.estado == 'ENTREGADO':
                from django.db import transaction
                with transaction.atomic():
                    for detalle in self.detalles.all():
                        producto = detalle.producto
                        
                        # ⚠️ CAMBIO CLAVE: Ahora validamos y descontamos la CANTIDAD DESPACHADA
                        if producto.stock_unidades < detalle.cantidad_despachada:
                            raise ValueError(
                                f"No se puede despachar. Stock insuficiente en Almacén Central para: {producto.nombre}. "
                                f"Disponible: {producto.stock_unidades}, A entregar: {detalle.cantidad_despachada}."
                            )
                        
                        # Deducción atómica basándose en lo que realmente sale
                        producto.stock_unidades -= detalle.cantidad_despachada
                        producto.save()
                        
        super().save(*args, **kwargs)



class DetallePedido(models.Model):
    pedido = models.ForeignKey(PedidoAlmacen, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(ProductoSiaf, on_delete=models.PROTECT, verbose_name="Producto SIAF")
    cantidad_solicitada = models.PositiveIntegerField(verbose_name="Cantidad Solicitada")
    
    # 💡 NUEVO CAMPO: Guardará lo que el almacenero decida entregar realmente
    cantidad_despachada = models.PositiveIntegerField(verbose_name="Cantidad Despachada", null=True, blank=True)

    def save(self, *args, **kwargs):
        # Si no se define una cantidad despachada, por defecto es igual a la solicitada
        if self.cantidad_despachada is None:
            self.cantidad_despachada = self.cantidad_solicitada
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad_solicitada} u. (Despachadas: {self.cantidad_despachada}) de {self.producto.nombre}"
