import csv
import os
from django.core.management.base import BaseCommand, CommandError
from apps.siaf_sincro.models import ProductoSiaf, DetallePedido, DiscrepanciaInventario

from django.utils import timezone
from django.db import transaction
from django.db.models import Sum

class Command(BaseCommand):
    help = "Lee el archivo CSV exportado del SIAF implementando el Escudo de Deltas contra asimetrías"
    
    def handle(self, *args, **options):
        # 📂 Ruta Oficial de Producción en el Servidor Linux (Montaje SMB)
        ruta_servidor = r"/mnt/siaf_compartido/items_prueba.csv"
        
        # 🏠 Ruta de Respaldo Local (Por si pruebas el código en tu máquina de desarrollo)
        ruta_desarrollo = r"C:\Users\Usuario\Documents\items_prueba.csv"
        
        # Selección inteligente de ruta según el entorno
        if os.path.exists(ruta_servidor):
            file_path = ruta_servidor
        elif os.path.exists(ruta_desarrollo):
            file_path = ruta_desarrollo
        else:
            raise CommandError(
                f"Crítico: El archivo CSV no fue encontrado en la ruta oficial del servidor ({ruta_servidor}) "
                f"ni en la ruta local de desarrollo ({ruta_desarrollo})."
            )

        self.stdout.write(self.style.NOTICE(f"Iniciando procesamiento con control de deltas: {file_path}"))
        
        try:
            with open(file_path, mode='r', encoding='utf-8', errors='ignore') as csv_file:
                reader = csv.reader(csv_file, delimiter=';')
                creados = 0
                actualizados = 0
                discrepancias_detectadas = 0

                with transaction.atomic():
                    for row in reader:
                        if len(row) < 4:
                            continue
                        codigo = row[0].strip().replace('"', '')
                        nombre = row[1].strip().replace('"', '')
                        unidad = row[2].strip().replace('"', '')
                        try:
                            stock_csv = int(float(row[3].strip()))
                        except ValueError:
                            stock_csv = 0

                        if not codigo or not nombre:
                            continue

                        # Intentar obtener el producto existente
                        producto, created = ProductoSiaf.objects.get_or_create(
                            codigo_siaf=codigo,
                            tipo_almacen='CENTRAL',
                            defaults={
                                'nombre': nombre,
                                'unidad_medida': 'Unidad' if unidad == '' else unidad,
                                'stock_unidades': stock_csv
                            }
                        )

                        if created:
                            creados += 1
                        else:
                            # --- ALGORITMO DEL DELTA COMPLEMENTARIO ---
                            
                            # Sumamos las unidades despachadas en Django en las últimas 24 horas
                            # que se asumen pendientes de ser digitadas en el SIAF
                            total_despachado_django = DetallePedido.objects.filter(
                                producto=producto,
                                pedido__estado='ENTREGADO',
                                pedido__fecha_pedido__date=timezone.now().date()
                            ).aggregate(total=Sum('cantidad_despachada'))['total'] or 0

                            # Stock que teóricamente debería tener el SIAF si estuviera al día
                            stock_esperado_siaf = producto.stock_unidades + total_despachado_django

                            if stock_csv > stock_esperado_siaf:
                                # ESCENARIO A: Llegó una COMPRA NUEVA o reabastecimiento legítimo al SIAF
                                incremento_compra = stock_csv - stock_esperado_siaf
                                producto.stock_unidades += incremento_compra
                                self.stdout.write(self.style.WARNING(f" [COMPRA] {producto.codigo_siaf}: +{incremento_compra} u."))
                            
                            elif stock_csv > producto.stock_unidades:
                                # ESCENARIO B: El SIAF viene inflado debido a omisión de transacciones físicas
                                unidades_omitidas = stock_csv - producto.stock_unidades
                                
                                # Registramos la alerta para la Subdirección Administrativa
                                DiscrepanciaInventario.objects.update_or_create(
                                    producto=producto,
                                    defaults={
                                        'stock_siaf_csv': stock_csv,
                                        'stock_django_real': producto.stock_unidades,
                                        'unidades_omitidas_siaf': unidades_omitidas
                                    }
                                )
                                discrepancias_detectadas += 1
                                # Se omite la actualización del stock_unidades para proteger la ventanilla real
                            else:
                                # ESCENARIO C: El SIAF procesó bajas correctamente o disminuyó por cuadre
                                producto.stock_unidades = stock_csv

                            producto.nombre = nombre
                            producto.unidad_medida = 'Unidad' if unidad == '' else unidad
                            producto.save()
                            actualizados += 1

                self.stdout.write(self.style.SUCCESS(
                    f"Sincronización procesada.\n"
                    f"-> Ítems Nuevos: {creados}\n"
                    f"-> Sincronizados/Evaluados: {actualizados}\n"
                    f"-> Alertas por omisión en SIAF: {discrepancias_detectadas}"
                ))
        except Exception as e:
            raise CommandError(f"Error crítico en el lazo de control: {str(e)}")
        
