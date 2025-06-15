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
    """Factura Electrónica - Electronic Invoice header (created later to group patient invoices)"""
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
    """Factura de Paciente - Individual patient invoice (now the main starting point)"""
    # Changed: patient_name is now a simple CharField instead of ForeignKey
    patient_name = models.CharField(
        'Nombre del Paciente',
        max_length=200,
        help_text='Nombre completo del paciente'
    )
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        verbose_name='Sucursal'
    )
    
    invoice_number = models.CharField(
        'Número de Factura',
        max_length=50,
        help_text='Número de factura del paciente'
    )
    
    date = models.DateField('Fecha de Factura')
    
    # Changed: electronic_invoice is now optional (can be assigned later)
    electronic_invoice = models.ForeignKey(
        ElectronicInvoice,
        on_delete=models.CASCADE,
        verbose_name='Factura Electrónica',
        related_name='patient_invoices',
        null=True,
        blank=True,
        help_text='Factura electrónica a la que pertenece (opcional, se puede asignar después)'
    )
    
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Factura de Paciente'
        verbose_name_plural = 'Facturas de Pacientes'
        ordering = ['-date', '-invoice_number']
        # Removed unique_together constraint since electronic_invoice is now optional

    def __str__(self):
        return f"Factura {self.invoice_number} - {self.patient_name}"

    @property
    def total_amount(self):
        """Calculate total amount for this invoice"""
        return sum(item.total for item in self.items.all())

    @property
    def total_treatments(self):
        """Get total number of treatments"""
        return self.items.count()


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