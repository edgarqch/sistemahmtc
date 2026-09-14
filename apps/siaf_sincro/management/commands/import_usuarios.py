import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction

class Command(BaseCommand):
    help = "Lee el archivo CSV exportado de BDAdmin e importa/actualiza los usuarios en Django"

    def handle(self, *args, **options):
        # 📂 Ruta Oficial de Producción en el Servidor Linux (Montaje SMB)
        ruta_servidor = r"/mnt/siaf_compartido/usuarios_siaf.csv"
        
        # 🏠 Ruta de Respaldo Local (Entorno de desarrollo en Windows)
        ruta_desarrollo = r"C:\Users\Usuario\Documents\usuarios_siaf.csv"
        
        # Selección inteligente de ruta según el entorno operativo
        if os.path.exists(ruta_servidor):
            file_path = ruta_servidor
        elif os.path.exists(ruta_desarrollo):
            file_path = ruta_desarrollo
        else:
            raise CommandError(
                f"Crítico: El archivo CSV de usuarios no fue encontrado en la ruta oficial ({ruta_servidor}) "
                f"ni en la ruta local de desarrollo ({ruta_desarrollo})."
            )

        self.stdout.write(self.style.NOTICE(f"Iniciando procesamiento de usuarios SIAF desde: {file_path}"))
        
        try:
            with open(file_path, mode='r', encoding='utf-8', errors='ignore') as csv_file:
                reader = csv.reader(csv_file, delimiter=';')
                creados = 0
                actualizados = 0
                
                # Bloque transaccional atómico para asegurar consistencia absoluta en PostgreSQL
                with transaction.atomic():
                    for row in reader:
                        if len(row) < 3:
                            continue
                        
                        # Limpieza perimetral de espacios y comillas encapsuladas por el volcado del BCP
                        username = row[0].strip().replace('"', '').lower()
                        nombre_completo = row[1].strip().replace('"', '')
                        estado_vigente = row[2].strip().replace('"', '')
                        
                        if not username or not nombre_completo:
                            continue
                        
                        usuario_existe = User.objects.filter(username=username).exists()
                        
                        if not usuario_existe:
                            # Creación segura de nueva cuenta con clave provisional
                            user = User.objects.create_user(
                                username=username,
                                first_name=nombre_completo[:150],
                                is_active=True
                            )
                            user.set_password(username) # Contraseña temporal = username
                            
                            # Cuenta maestra de TI conserva privilegios globales administrativos
                            if username == 'hmtc':
                                user.is_staff = True
                                user.is_superuser = True
                            
                            user.save()
                            creados += 1
                        else:
                            # Sincronización y actualización de cuentas existentes
                            user = User.objects.get(username=username)
                            user.first_name = nombre_completo[:150]
                            
                            # Purgar accesos de ex-empleados basándose en el estado de vigencia de Windows
                            if estado_vigente != 'S' and username != 'hmtc':
                                user.is_active = False
                            else:
                                user.is_active = True
                                
                            if username == 'hmtc':
                                user.is_staff = True
                                user.is_superuser = True
                            
                            user.save()
                            actualizados += 1
                            
                self.stdout.write(self.style.SUCCESS(
                    f"Sincronización de usuarios finalizada con éxito.\n"
                    f"-> Cuentas NUEVAS Creadas (Clave Temporal Activada): {creados}\n"
                    f"-> Cuentas EXISTENTES Sincronizadas: {actualizados}"
                ))
        except Exception as e:
            raise CommandError(f"Error crítico durante la importación de usuarios: {str(e)}")

