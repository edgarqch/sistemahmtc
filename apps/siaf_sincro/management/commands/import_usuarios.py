import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction

class Command(BaseCommand):
    help = "Lee el archivo CSV exportado de BDAdmin e importa/actualiza los usuarios en Django"

    def handle(self, *args, **options):
        # Ruta estándar donde se genera el archivo plano desde Windows
        file_path = r"C:\Users\Usuario\Documents\usuarios_siaf.csv"

        if not os.path.exists(file_path):
            raise CommandError(f"El archivo CSV de usuarios no fue encontrado en la ruta: {file_path}")

        self.stdout.write(self.style.NOTICE(f"Iniciando procesamiento de usuarios SIAF: {file_path}"))

        try:
            with open(file_path, mode='r', encoding='utf-8', errors='ignore') as csv_file:
                reader = csv.reader(csv_file, delimiter=';')
                creados = 0
                actualizados = 0

                # Envolvemos todo el bucle en una transacción atómica de PostgreSQL
                with transaction.atomic():
                    for row in reader:
                        if len(row) < 3:
                            continue

                        # Limpiamos las comillas y espacios de los extremos
                        username = row[0].strip().replace('"', '').lower()
                        nombre_completo = row[1].strip().replace('"', '')
                        estado_vigente = row[2].strip().replace('"', '')

                        if not username or not nombre_completo:
                            continue

                        # Buscamos si el usuario ya existe para no resetear contraseñas existentes
                        usuario_existe = User.objects.filter(username=username).exists()

                        if not usuario_existe:
                            # 1. CASO USUARIO NUEVO: Se crea con contraseña temporal igual al username
                            user = User.objects.create_user(
                                username=username,
                                first_name=nombre_completo[:150],  # Límite nativo del campo en Django
                                is_active=True
                            )
                            user.set_password(username)  # Contraseña provisional = username
                            
                            # Tratamiento especial de superusuario para tu cuenta 'hmtc'
                            if username == 'hmtc':
                                user.is_staff = True
                                user.is_superuser = True
                            
                            user.save()
                            creados += 1
                        else:
                            # 2. CASO USUARIO EXISTENTE: Solo actualizamos datos informativos
                            user = User.objects.get(username=username)
                            user.first_name = nombre_completo[:150]
                            
                            # Si en SQL Server pasa a no vigente, lo desactivamos en Django (excepto hmtc)
                            if estado_vigente != 'S' and username != 'hmtc':
                                user.is_active = False
                            else:
                                user.is_active = True
                                
                            # Si es hmtc, nos aseguramos que mantenga siempre sus credenciales de TI
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
