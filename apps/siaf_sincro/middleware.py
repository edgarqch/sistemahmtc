from django.shortcuts import redirect

class ObligarCambioContrasenaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            
            # Exclusión de seguridad para el administrador
            if request.user.is_superuser or request.user.username == 'hmtc':
                return self.get_response(request)

            # Verificar la contraseña en esta sesión para optimizar rendimiento
            if 'clave_temporal' not in request.session:
                if request.user.check_password(request.user.username):
                    request.session['clave_temporal'] = True
                else:
                    request.session['clave_temporal'] = False

            # Aplicar el bloqueo si la bandera es verdadera
            if request.session.get('clave_temporal') is True:
                
                # BLINDAJE DIRECTO: Si la URL del navegador ya contiene la palabra de escape, déjalo pasar
                # Esto evita el bucle sin importar el namespace o prefijo (/siaf/, /siaf_sincro/, etc.)
                if 'cambiar-contrasena' in request.path or 'logout' in request.path:
                    return self.get_response(request)
                
                # Si intenta cargar archivos estáticos (CSS/JS de Gentelella), déjalo pasar
                if request.path.startswith('/static/'):
                    return self.get_response(request)

                # Si no está en las rutas de escape, lo redirigimos firmemente
                return redirect('siaf_sincro:cambiar_password')

        response = self.get_response(request)
        return response
