from django import forms
from .models import Autor, Instrumento

class AutorForm(forms.ModelForm):
    class Meta:
        model = Autor
        fields = ['nombre', 'apellidos','cargo']


class InstrumentoForm(forms.ModelForm):
    class Meta:
        model = Instrumento
        fields = ['titulo', 'categoria','descripcion', 'documento', 'fecha_creacion','autor_id']