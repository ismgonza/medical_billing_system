from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re


class Branch(models.Model):
    """Sucursal - Branch office"""
    name = models.CharField('Nombre de Sucursal', max_length=100, unique=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
        ordering = ['name']

    def __str__(self):
        return self.name


class Patient(models.Model):
    """Paciente - Patient information"""
    
    def validate_cedula(value):
        """Validate cedula format based on Costa Rican standards"""
        # Remove any spaces or dashes
        clean_value = re.sub(r'[\s-]', '', value)
        
        # Nacional: 9 digits
        if re.match(r'^\d{9}$', clean_value):
            return clean_value
        
        # Residente: 12 digits
        elif re.match(r'^\d{12}$', clean_value):
            return clean_value
        
        # Extranjero: up to 20 alphanumeric characters
        elif re.match(r'^[a-zA-Z0-9]{1,20}$', clean_value):
            return clean_value
        
        else:
            raise ValidationError(
                'Formato de cédula inválido. '
                'Nacional: 9 dígitos, Residente: 12 dígitos, Extranjero: hasta 20 caracteres alfanuméricos.'
            )

    cedula = models.CharField(
        'Cédula',
        max_length=20,
        unique=True,
        validators=[validate_cedula],
        help_text='Nacional: 9 dígitos, Residente: 12 dígitos, Extranjero: hasta 20 caracteres alfanuméricos'
    )
    name = models.CharField('Nombre', max_length=100)
    lname1 = models.CharField('Primer Apellido', max_length=100)
    lname2 = models.CharField('Segundo Apellido', max_length=100, blank=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['lname1', 'lname2', 'name']

    def clean(self):
        if self.cedula:
            self.cedula = Patient.validate_cedula(self.cedula)

    def __str__(self):
        if self.lname2:
            return f"{self.name} {self.lname1} {self.lname2} - {self.cedula}"
        return f"{self.name} {self.lname1} - {self.cedula}"

    @property
    def full_name(self):
        """Return patient's full name"""
        if self.lname2:
            return f"{self.name} {self.lname1} {self.lname2}"
        return f"{self.name} {self.lname1}"


class Treatment(models.Model):
    """Tratamiento - Medical treatment or service"""
    code = models.CharField(
        'Código',
        max_length=20,
        unique=True,
        help_text='Código único del tratamiento'
    )
    name = models.CharField('Nombre del Tratamiento', max_length=200)
    price = models.DecimalField(
        'Precio',
        max_digits=10,
        decimal_places=2,
        help_text='Precio base del tratamiento'
    )
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Tratamiento'
        verbose_name_plural = 'Tratamientos'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name} - ₡{self.price:,.2f}"


class ElectronicInvoice(models.Model):
    """Factura Electrónica - Electronic Invoice header"""
    invoice_number = models.CharField(
        'Número de Factura Electrónica',
        max_length=50,
        unique=True,
        help_text='Número único de la factura electrónica'
    )
    date = models.DateField('Fecha de Factura')
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Factura Electrónica'
        verbose_name_plural = 'Facturas Electrónicas'
        ordering = ['-date', '-invoice_number']

    def __str__(self):
        return f"Factura {self.invoice_number} - {self.date}"


class PatientInvoice(models.Model):
    """Factura de Paciente - Individual patient invoice within an electronic invoice"""
    electronic_invoice = models.ForeignKey(
        ElectronicInvoice,
        on_delete=models.CASCADE,
        verbose_name='Factura Electrónica',
        related_name='patient_invoices'
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        verbose_name='Paciente'
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        verbose_name='Sucursal'
    )
    invoice_number = models.CharField(
        'Número de Factura de Paciente',
        max_length=50,
        help_text='Número interno de factura del paciente'
    )
    date = models.DateField('Fecha de Factura del Paciente')
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Factura de Paciente'
        verbose_name_plural = 'Facturas de Pacientes'
        ordering = ['-date', '-invoice_number']
        unique_together = ['electronic_invoice', 'invoice_number']

    def __str__(self):
        return f"Factura {self.invoice_number} - {self.patient.full_name}"


class PatientInvoiceItem(models.Model):
    """Detalle de Factura de Paciente - Line items for patient invoices"""
    patient_invoice = models.ForeignKey(
        PatientInvoice,
        on_delete=models.CASCADE,
        verbose_name='Factura de Paciente',
        related_name='items'
    )
    treatment = models.ForeignKey(
        Treatment,
        on_delete=models.PROTECT,
        verbose_name='Tratamiento'
    )
    quantity = models.PositiveIntegerField('Cantidad', default=1)
    unit_price = models.DecimalField(
        'Precio Unitario',
        max_digits=10,
        decimal_places=2,
        help_text='Precio del tratamiento al momento de la factura'
    )
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)

    class Meta:
        verbose_name = 'Detalle de Factura'
        verbose_name_plural = 'Detalles de Facturas'
        ordering = ['patient_invoice', 'treatment']

    def save(self, *args, **kwargs):
        # Set unit_price from treatment if not provided
        if not self.unit_price:
            self.unit_price = self.treatment.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.treatment.name} - {self.patient_invoice.invoice_number}"

    @property
    def subtotal(self):
        """Subtotal (quantity * unit_price)"""
        return self.quantity * self.unit_price

    @property
    def monto_asembis(self):
        """15% of subtotal for ASEMBIS"""
        from decimal import Decimal
        return self.subtotal * Decimal('0.15')

    @property
    def monto_dr(self):
        """85% of subtotal for Doctor"""
        from decimal import Decimal
        return self.subtotal * Decimal('0.85')

    @property
    def iva(self):
        """4% IVA tax"""
        from decimal import Decimal
        return self.subtotal * Decimal('0.04')

    @property
    def total(self):
        """Total amount (Monto ASEMBIS + Monto DR + IVA)"""
        return self.monto_asembis + self.monto_dr + self.iva