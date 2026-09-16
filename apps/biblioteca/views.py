from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from .forms import AutorForm, InstrumentoForm
from .models import Autor, Instrumento
from apps.siaf_sincro.models import PedidoAlmacen
# Create your views here.
#def home (request):
#   return HttpResponse("<H1>SISTEMA DE BIBLIOTECA HMTC</H1>")

@login_required
def Home(request):
    """Vista principal con métricas reales, últimos documentos y estados de almacén."""
    
    # Contadores nativos para la barra superior
    total_instrumentos = Instrumento.objects.filter(estado=True).count()
    total_autores = Autor.objects.filter(estado=True).count()
    total_pedidos = PedidoAlmacen.objects.count()
    total_despachos = PedidoAlmacen.objects.filter(estado='entregado').count()
    
    # Estados individuales para el gráfico estadístico del almacén
    pedidos_pendientes = PedidoAlmacen.objects.filter(estado='pendiente').count()
    pedidos_autorizados = PedidoAlmacen.objects.filter(estado='autorizado').count()
    pedidos_rechazados = PedidoAlmacen.objects.filter(estado='rechazado').count()
    
    # Consulta para rellenar la tabla central con los últimos registros
    ultimos_instrumentos = Instrumento.objects.filter(estado=True).order_by('-id')[:5]
    
    contexto = {
        'total_instrumentos': total_instrumentos,
        'total_autores': total_autores,
        'total_pedidos': total_pedidos,
        'total_despachos': total_despachos,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_autorizados': pedidos_autorizados,
        'pedidos_rechazados': pedidos_rechazados,
        'ultimos_instrumentos': ultimos_instrumentos,
    }
    return render(request, 'index.html', contexto)


def crearAutor(request):
    if request.method == 'POST':
        #nom = request.POST.get('nombre')                           |  Metodo de guardar los campos
        #ape = request.POST.get('apellidos')                        |  sin usar el archivo forms.py
        #car = request.POST.get('cargo')                            |  solamente el html
        #autor = Autor(nombre = nom, apellidos = ape, cargo = car)  |  POST.get('nombre') hace referencia a
        #autor.save()                                               |  el name de la etiqueta input
        #return redirect('index')                                   |  del formulario en el hmtl.

        autor_form = AutorForm(request.POST)
        if autor_form.is_valid():
            autor_form.save()
            return redirect('biblioteca:listar_autor')
    else:
        autor_form = AutorForm()
        #print(autor_form)
    return render(request, 'biblioteca/crear_autor.html',{'autor_form':autor_form})

def listarAutor(request):
    autores = Autor.objects.filter(estado = True)
    return render(request,'biblioteca/listar_autor.html',{'autores':autores})

def editarAutor(request, id):
    autor_form = None
    error = None
    try:
        autor = Autor.objects.get(id = id)
        if request.method == 'GET':
            autor_form = AutorForm(instance = autor)
            print(autor_form)
        else:
            autor_form = AutorForm(request.POST, instance = autor)
            if autor_form.is_valid():
                autor_form.save()
            return redirect('biblioteca:listar_autor')
    except ObjectDoesNotExist as e:
        error = e
    return render(request, 'biblioteca/editar_autor.html', {'autor_form':autor_form, 'error':error})

def eliminarAutor(request, id):
    autor = Autor.objects.get(id = id)
    if request.method == 'POST':
        autor.estado = False
        autor.save()
        return redirect('biblioteca:listar_autor')
    return render(request, 'biblioteca/eliminar_autor.html', {'autor':autor})


def crearInstrumento(request):
    if request.method == 'POST':
        instrumento_form = InstrumentoForm(request.POST, request.FILES)
        if instrumento_form.is_valid():
            instrumento_form.save()
            return redirect('biblioteca:listar_instrumento')
    else:
        instrumento_form = InstrumentoForm()
    return render(request, 'biblioteca/crear_instrumento.html',{'instrumento_form':instrumento_form})

@login_required
def listarInstrumento(request):
    instrumentos = Instrumento.objects.filter(estado = True)
    return render(request,'biblioteca/listar_instrumento.html',{'instrumentos':instrumentos})