from django.core.management.base import BaseCommand
from apps.siaf_sincro.models import UnidadHospitalaria, PedidoAlmacen

class Command(BaseCommand):
    help = "Crea unidades hospitalarias base y repara pedidos antiguos vacíos"

    def handle(self, *args, **options):
        # 1. Creamos una unidad comodín para los registros antiguos que no tengan lista llena
        unidad_defecto, _ = UnidadHospitalaria.objects.get_or_create(
            nombre="Servicio No Especificado", codigo_interno="S-N"
        )
        
        # 2. Creamos las unidades reales del Hospital Madre Teresa de Calcuta
        unidades = [
            "Emergencias", "CE Pediatría", "CE Ginecología y Obstetricia", 
            "CE Medicina Interna", "CE Cirugía General", "CE Gastroenterología", "CE Traumatología",
            "Inter. Cirugia General", "Inter. Medicina Interna", "Inter. Pediatria", "Inter. Ginecología",
            "Odontología", "Telesalud", "CE Gastroenterología", "Anestesiología", 
            "Laboratorio Clínico", "Nutrición y Dietética", "Trabajo Social", "Farmacia", "Unidad Transfusional",
            "Ecografia", "Rayos X", "Endoscopia",
            "Dirección", "Sub Direccion Administrativa", "Recursos Humanos", "Informática", "Finanzas", "Resp. Administrativo", "Estadistica",
            "Unidad SUS", "Almacenes", "Jefatura de Enfermería", "Secretaría", "Docencia e Investigación", "Informaciones", "Gestión de Calidad",
            "Cajas y admisiones"
        ]
        # Corrección del bucle: Buscamos y creamos directamente por el campo 'nombre'
        for uni in unidades:
            UnidadHospitalaria.objects.get_or_create(nombre=uni)

        # 3. Reparacion e inyeccion de datos para pedidos huerfanos historicos (TEXTO PLANO)
        pedidos_vacios = PedidoAlmacen.objects.filter(unidad__isnull=True)
        cantidad = pedidos_vacios.count()
        
        if cantidad > 0:
            pedidos_vacios.update(unidad=unidad_defecto)
            self.stdout.write(self.style.SUCCESS(f"OK: Se repararon {cantidad} pedidos antiguos con la unidad por defecto."))
        else:
            self.stdout.write(self.style.SUCCESS("OK: No se encontraron pedidos huerfanos en la base de datos."))
