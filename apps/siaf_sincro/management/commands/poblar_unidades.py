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
            # Área Médica y Enfermería
            "Emergencias - Área Médica", "Emergencias - Enfermería",
            "Pediatría - Área Médica", "Pediatría y Neonatología - Enfermería",
            "Ginecología y Obstetricia - Área Médica", "Ginecología y Obstetricia - Enfermería",
            "Gastroenterología - Área Médica",
            "Medicina Interna - Área Médica", "Medicina Interna - Enfermería",
            "Cirugía General - Área Médica",
            "Traumatología - Área Médica", "Cirugía General y Traumatología - Enfermería",
            "Anestesiología", "Quirofano", "Odontología", "Telesalud",
            # Apoyo al Diagnostico
            "Laboratorio Clínico", "Nutrición y Dietética", "Trabajo Social", "Farmacia", "Unidad Transfusional", "Ecografia", "Rayos X", "Endoscopia",
            # Área Administrativa
            "Dirección", "Sub Direccion Administrativa", "Unidad de Recursos Humanos", "Unidad Informática", "Unidad de Finanzas", 
            "Unidad Administrativa", "Unidad de Estadistica", "Unidad del SUS", "Unidad de Almacenes", "Jefatura de Enfermería", "Secretaría",
            "Docencia e Investigación", "Informaciones", "Gestión de Calidad", "Cajas y admisiones", "Archivos",
            # Área de apoyo
            "Servicio de Choferes", "Servicio de Porteria", "Servicio de Cocina", "Servicio de Limpieza", "Servicio de Lavanderia",
            "Servicio de Mantenimiento",
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
