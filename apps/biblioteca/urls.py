from django.urls import path, re_path
from .views import crearAutor, listarAutor, editarAutor, eliminarAutor, crearInstrumento, listarInstrumento

urlpatterns = [
   path('crear_autor/', crearAutor, name = 'crear_autor'),
   path('listar_autor/', listarAutor, name = 'listar_autor'),
   path('editar_autor/<int:id>', editarAutor, name = 'editar_autor'),
   path('eliminar_autor/<int:id>', eliminarAutor, name = 'eliminar_autor'),

   path('crear_instrumento/', crearInstrumento, name = 'crear_instrumento'),
   path('listar_instrumento/', listarInstrumento, name = 'listar_instrumento'),

   #re_path(r'^crear_autor/(?P<id>\d+)', crearAutor, name = 'crear_autor')
]