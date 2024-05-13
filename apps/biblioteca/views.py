from django.shortcuts import render,redirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from .forms import AutorForm, InstrumentoForm
from .models import Autor, Instrumento
# Create your views here.
#def home (request):
#   return HttpResponse("<H1>SISTEMA DE BIBLIOTECA HMTC</H1>")

def Home(request):
    return render(request, 'index.html')

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

def listarInstrumento(request):
    instrumentos = Instrumento.objects.filter(estado = True)
    return render(request,'biblioteca/listar_instrumento.html',{'instrumentos':instrumentos})