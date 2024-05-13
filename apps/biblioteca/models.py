from django.db import models

class Autor(models.Model):
    id = models.AutoField(primary_key = True)
    nombre = models.CharField('Nombre', max_length = 200, blank = False, null = False)
    apellidos = models.CharField('Apellidos', max_length = 200, blank = False, null = False)
    cargo = models.CharField('Cargo', max_length = 200, blank = False, null = True)
    fecha_creacion = models.DateField('Fecha de creacion', auto_now = True, auto_now_add = False)
    estado = models.BooleanField('Estado', default = True)

    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Instrumento(models.Model):
    id = models.AutoField(primary_key = True)
    titulo = models.CharField('titulo', max_length = 100, blank = False, null = False)
    categoria = models.CharField('categoria', max_length = 100, blank = False, null = True)
    descripcion = models.TextField('Descripcion', blank = False, null = False)
    documento = models.FileField('documento', upload_to='biblioteca/', max_length=255, null=True, blank=True)
    fecha_publicacion = models.DateField('Fecha de publicacion', auto_now = True, auto_now_add = False)
    #autor_id = models.OneToOneField(Autor, on_delete = models.CASCADE, null = True) RELACION DE 1 A 1
    #autor_id = models.ForeignKey(Autor, on_delete = models.CASCADE) RELACION DE 1 A MUCHOS
    autor_id = models.ManyToManyField(Autor) # RELACION DE MUCHOS A MUCHOS
    fecha_creacion = models.DateField('Fecha de creacion', blank = False, null = False)
    estado = models.BooleanField('Estado', default = True)
    portada = models.ImageField('portada', upload_to='portadas/', max_length=255, null=True, blank=True, default='document_default.jpg')

    class Meta:
        verbose_name = 'Instrumento'
        verbose_name_plural = 'Instrumentos'
        ordering = ['titulo']
        
    def __str__(self):
        return self.titulo
