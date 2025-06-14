from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Branch, Patient, Treatment, ElectronicInvoice, 
    PatientInvoice, PatientInvoiceItem
)


class PatientForm(forms.ModelForm):
    """Formulario para pacientes"""
    
    class Meta:
        model = Patient
        fields = ['cedula', 'name', 'lname1', 'lname2']
        widgets = {
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 123456789 (Nacional), 123456789012 (Residente), ABC123 (Extranjero)'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del paciente'
            }),
            'lname1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primer apellido'
            }),
            'lname2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Segundo apellido (opcional)',
                'required': False
            }),
        }

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if cedula:
            # Use the model's validation
            return Patient.validate_cedula(cedula)
        return cedula


class TreatmentForm(forms.ModelForm):
    """Formulario para tratamientos"""
    
    class Meta:
        model = Treatment
        fields = ['code', 'name', 'price', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: SOA-00074'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del tratamiento'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise ValidationError('El precio debe ser mayor a cero.')
        return price


class ElectronicInvoiceForm(forms.ModelForm):
    """Formulario para facturas electrónicas"""
    
    class Meta:
        model = ElectronicInvoice
        fields = ['invoice_number', 'date']
        widgets = {
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de factura electrónica'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def clean_invoice_number(self):
        invoice_number = self.cleaned_data.get('invoice_number')
        if invoice_number:
            # Check if invoice number already exists (excluding current instance if updating)
            existing = ElectronicInvoice.objects.filter(invoice_number=invoice_number)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('Ya existe una factura electrónica con este número.')
        return invoice_number


class PatientInvoiceForm(forms.ModelForm):
    """Formulario para facturas de pacientes"""
    
    class Meta:
        model = PatientInvoice
        fields = ['electronic_invoice', 'patient', 'branch', 'invoice_number', 'date']
        widgets = {
            'electronic_invoice': forms.Select(attrs={
                'class': 'form-select'
            }),
            'patient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'branch': forms.Select(attrs={
                'class': 'form-select'
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de factura del paciente'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        electronic_invoice_id = kwargs.pop('electronic_invoice_id', None)
        super().__init__(*args, **kwargs)
        
        # If creating from an electronic invoice, pre-select it and hide the field
        if electronic_invoice_id:
            self.fields['electronic_invoice'].initial = electronic_invoice_id
            self.fields['electronic_invoice'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        electronic_invoice = cleaned_data.get('electronic_invoice')
        invoice_number = cleaned_data.get('invoice_number')
        
        if electronic_invoice and invoice_number:
            # Check if invoice number already exists within the same electronic invoice
            existing = PatientInvoice.objects.filter(
                electronic_invoice=electronic_invoice,
                invoice_number=invoice_number
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
                
            if existing.exists():
                raise ValidationError({
                    'invoice_number': 'Ya existe una factura de paciente con este número en la misma factura electrónica.'
                })
        
        return cleaned_data


class PatientInvoiceItemForm(forms.ModelForm):
    """Formulario para items de factura de paciente"""
    
    class Meta:
        model = PatientInvoiceItem
        fields = ['treatment', 'quantity', 'unit_price']
        widgets = {
            'treatment': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'readonly': True  # Will be filled automatically from treatment
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active treatments
        self.fields['treatment'].queryset = Treatment.objects.filter(is_active=True).order_by('code')

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError('La cantidad debe ser mayor a cero.')
        return quantity


class PatientInvoiceItemFormSet(forms.BaseInlineFormSet):
    """FormSet personalizado para items de factura"""
    
    def clean(self):
        if any(self.errors):
            return
        
        # Check that at least one item exists
        forms_count = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                forms_count += 1
        
        if forms_count < 1:
            raise ValidationError('Debe agregar al menos un tratamiento a la factura.')


# Create the actual formset
PatientInvoiceItemInlineFormSet = forms.inlineformset_factory(
    PatientInvoice,
    PatientInvoiceItem,
    form=PatientInvoiceItemForm,
    formset=PatientInvoiceItemFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class MonthlyReportForm(forms.Form):
    """Formulario para generar reportes mensuales"""
    
    MONTH_CHOICES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mes'
    )
    year = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '2020',
            'max': '2030'
        }),
        label='Año'
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Sucursal',
        required=False,
        empty_label='Todas las sucursales'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current month and year as default
        from datetime import date
        today = date.today()
        self.fields['month'].initial = today.month
        self.fields['year'].initial = today.year