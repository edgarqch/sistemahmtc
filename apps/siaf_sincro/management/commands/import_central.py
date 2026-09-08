import csv
import os
from django.core.management.base import BaseCommand, CommandError
from apps.siaf_sincro.models import ProductoSiaf  # Importación desde tu carpeta apps

class Command(BaseCommand):
    help = "Lee el archivo CSV exportado del SIAF e importa/actualiza el stock del Almacén Central"

    def handle(self, *args, **options):
        # 1. Definimos la ruta de desarrollo local en tu Windows (Ajusta 'Usuario' por tu perfil real)
        file_path = r"C:\Users\Usuario\Documents\items_prueba.csv"

        # 2. Validación de seguridad: Verificar si el archivo CSV existe físicamente
        if not os.path.exists(file_path):
            raise CommandError(f"El archivo CSV no fue encontrado en la ruta: {file_path}")

        self.stdout.write(self.style.NOTICE(f"Iniciando procesamiento del catálogo: {file_path}"))

        try:
            # Abrimos el archivo especificando UTF-8 (bcp a veces usa codificaciones nativas de Windows)
            with open(file_path, mode='r', encoding='utf-8', errors='ignore') as csv_file:
                # Configuramos el delimitador de punto y coma (;) como definimos en el BCP
                # El lector de CSV de Python remueve automáticamente las comillas dobles de control
                reader = csv.reader(csv_file, delimiter=';')
                
                creados = 0
                actualizados = 0

                for row in reader:
                    # Validación: Cada fila debe tener estrictamente las 4 columnas de la vista SQL
                    if len(row) < 4:
                        continue  # Salta líneas vacías o corruptas

                    # Asignamos las variables limpiando espacios en blanco en los extremos
                    codigo = row[0].strip()
                    nombre = row[1].strip()
                    unidad = row[2].strip()
                    
                    try:
                        # SQL Server exporta enteros a veces con decimales flotantes (.00), los limpiamos
                        stock = int(float(row[3].strip()))
                    except ValueError:
                        stock = 0

                    # Filtro de control por si viene alguna fila basura
                    if not codigo or not nombre:
                        continue  

                    # 3. SINCRONIZACIÓN INTELIGENTE (update_or_create)
                    # Busca por Código SIAF + Tipo de Almacén. Si coincide actualiza el stock, si no existe lo crea.
                    obj, created = ProductoSiaf.objects.update_or_create(
                        codigo_siaf=codigo,
                        tipo_almacen='CENTRAL',  # Hardcodeamos que este comando es exclusivo del Almacén Central
                        defaults={
                            'nombre': nombre,
                            'unidad_medida': unidad,
                            'stock_unidades': stock
                        }
                    )

                    if created:
                        creados += 1
                    else:
                        actualizados += 1

                # 4. Mensaje final de éxito en la consola de Django
                self.stdout.write(self.style.SUCCESS(
                    f"Sincronización finalizada con éxito.\n"
                    f"-> Ítems NUEVOS Creados: {creados}\n"
                    f"-> Ítems EXISTENTES Actualizados: {actualizados}"
                ))

        except Exception as e:
            raise CommandError(f"Error crítico durante la lectura e inserción de datos: {str(e)}")
