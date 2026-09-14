import csv
import os
from django.core.management.base import BaseCommand, CommandError
from apps.siaf_sincro.models import ProductoSiaf

class Command(BaseCommand):
    help = "Lee el archivo CSV exportado del SIAF e importa/actualiza el stock del Almacén Central"

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

        self.stdout.write(self.style.NOTICE(f"Iniciando procesamiento del catálogo desde: {file_path}"))
        
        try:
            # Forzamos encoding utf-8 e ignoramos errores para evitar caídas por caracteres Windows antiguos
            with open(file_path, mode='r', encoding='utf-8', errors='ignore') as csv_file:
                reader = csv.reader(csv_file, delimiter=';')
                creados = 0
                actualizados = 0
                
                for row in reader:
                    if len(row) < 4:
                        continue
                    
                    # Limpieza perimetral de comillas añadidas por el BCP
                    codigo = row[0].strip().replace('"', '')
                    nombre = row[1].strip().replace('"', '')
                    unidad = row[2].strip().replace('"', '')
                    
                    try:
                        stock = int(float(row[3].strip()))
                    except ValueError:
                        stock = 0
                        
                    if not codigo or not nombre:
                        continue
                    
                    # Operación atómica en el ORM de Django
                    obj, created = ProductoSiaf.objects.update_or_create(
                        codigo_siaf=codigo,
                        tipo_almacen='CENTRAL',
                        defaults={
                            'nombre': nombre,
                            'unidad_medida': 'Unidad' if unidad == '' else unidad,
                            'stock_unidades': stock
                        }
                    )
                    
                    if created:
                        creados += 1
                    else:
                        actualizados += 1
                        
                self.stdout.write(self.style.SUCCESS(
                    f"Sincronización finalizada con éxito.\n"
                    f"-> Ítems NUEVOS Creados: {creados}\n"
                    f"-> Ítems EXISTENTES Actualizados: {actualizados}"
                ))
                
        except Exception as e:
            raise CommandError(f"Error crítico durante la lectura de datos: {str(e)}")
