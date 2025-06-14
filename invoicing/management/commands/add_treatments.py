from django.core.management.base import BaseCommand
from invoicing.models import Treatment

class Command(BaseCommand):
    help = 'Add predefined treatments to the database'

    def handle(self, *args, **options):
        treatments_data = [
            ("SOA-00070", "CONSULTA ESPECIALISTA ENDODONCIA", 30000.00),
            ("SOA-00071", "ENDODONCIA MOLAR ESPECIALISTA", 115004.70),
            ("SOA-00072", "ENDODONCIA PREMOLAR ESPECIALISTA", 100000.00),
            ("SOA-00073", "ENDODONCIA ANTERIOR ESPECIALISTA", 90000.00),
            ("SOA-00074", "APICECTOMÍA CON RETRO OBTURACIÓN", 160000.00),
            ("SOA-00075", "RETRATAMIENTO ANTERIOR ESPECIALISTA", 115000.00),
            ("SOA-00076", "RETRATAMIENTO PREMOLAR ESPECIALISTA", 125000.00),
            ("SOA-00078", "REMOCIÓN DE POSTES", 36400.00),
            ("SOA-00300", "ABONO ODONTOLOGÍA", 60000.00),
            ("SOD-0006", "OXIDO DE ZINC", 15380.00),
            ("SOD-00717", "ABONO PERIODONCIA 2", 10000.00),
            ("SOD-00801", "CONSULTA ESPECIALISTA ENDODONCIA", 20200.00),
            ("SOD-00802", "ENDODONCIA MOLAR ESPECIALISTA", 150000.00),
            ("SOD-00803", "ENDODONCIA PREMOLAR ESPECIALISTA", 125000.00),
            ("SOD-00804", "ENDODONCIA ANTERIOR ESPECIALISTA", 115384.62),
            ("SOD-00805", "APICECTOMIA", 173076.92),
            ("SOD-00807", "ABONO ENDODONCIA 2", 40000.00),
            ("SOD-00809", "ABONO ENDODONCIA MULTIRRADICULAR", 75000.00),
            ("SOD-00812", "RETRATAMIENTO ANTERIOR ESPECIALISTA", 140000.00),
            ("SOD-00813", "RETRATAMIENTO PREMOLAR ESPECIALISTA", 150000.00),
            ("SOD-00814", "RETRATAMIENTO MOLARES ESPECIALISTA", 180288.48),
            ("SOD-00815", "APLICACIÓN MTA", 55000.00),
            ("SOD-00817", "COLOCACION DE POSTE", 44999.00),
            ("SOD-OO803", "ENDODONCIA PREMOLAR ESPECIALISTA", 125000.00),
        ]

        created_count = 0
        updated_count = 0

        for code, name, price in treatments_data:
            treatment, created = Treatment.objects.get_or_create(
                code=code,
                defaults={'name': name, 'price': price, 'is_active': True}
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"Created: {code} - {name}")
            else:
                # Update existing treatment
                treatment.name = name
                treatment.price = price
                treatment.is_active = True
                treatment.save()
                updated_count += 1
                self.stdout.write(f"Updated: {code} - {name}")

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {created_count + updated_count} treatments '
                f'({created_count} created, {updated_count} updated)'
            )
        )