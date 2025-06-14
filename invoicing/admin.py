from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import (
    Branch, Patient, Treatment, ElectronicInvoice, 
    PatientInvoice, PatientInvoiceItem
)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['cedula', 'full_name', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['cedula', 'name', 'lname1', 'lname2']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('cedula', 'name', 'lname1', 'lname2')
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'formatted_price', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Información del Tratamiento', {
            'fields': ('code', 'name', 'price', 'is_active')
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_price(self, obj):
        return f"₡{obj.price:,.2f}"
    formatted_price.short_description = 'Precio'
    formatted_price.admin_order_field = 'price'


class PatientInvoiceInline(admin.TabularInline):
    model = PatientInvoice
    extra = 0
    fields = ['invoice_number', 'patient', 'branch', 'date']
    readonly_fields = []


@admin.register(ElectronicInvoice)
class ElectronicInvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'date', 'patient_count', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['invoice_number']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PatientInvoiceInline]
    
    def patient_count(self, obj):
        return obj.patient_invoices.count()
    patient_count.short_description = 'Cantidad de Pacientes'


class PatientInvoiceItemInline(admin.TabularInline):
    model = PatientInvoiceItem
    extra = 0
    fields = [
        'treatment', 'quantity', 'unit_price', 
        'subtotal_display', 'monto_asembis_display', 
        'monto_dr_display', 'iva_display', 'total_display'
    ]
    readonly_fields = [
        'subtotal_display', 'monto_asembis_display', 
        'monto_dr_display', 'iva_display', 'total_display'
    ]
    
    def subtotal_display(self, obj):
        if obj.pk:
            return f"₡{obj.subtotal:,.2f}"
        return "₡0.00"
    subtotal_display.short_description = 'Subtotal'
    
    def monto_asembis_display(self, obj):
        if obj.pk:
            return f"₡{obj.monto_asembis:,.2f}"
        return "₡0.00"
    monto_asembis_display.short_description = 'Monto ASEMBIS (15%)'
    
    def monto_dr_display(self, obj):
        if obj.pk:
            return f"₡{obj.monto_dr:,.2f}"
        return "₡0.00"
    monto_dr_display.short_description = 'Monto DR (85%)'
    
    def iva_display(self, obj):
        if obj.pk:
            return f"₡{obj.iva:,.2f}"
        return "₡0.00"
    iva_display.short_description = 'I.V.A. (4%)'
    
    def total_display(self, obj):
        if obj.pk:
            return format_html(
                '<strong>₡{:,.2f}</strong>', 
                obj.total
            )
        return "₡0.00"
    total_display.short_description = 'Total'


@admin.register(PatientInvoice)
class PatientInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'patient', 'branch', 'date', 
        'electronic_invoice', 'items_count', 'invoice_total'
    ]
    list_filter = ['date', 'branch', 'created_at']
    search_fields = [
        'invoice_number', 'patient__name', 'patient__lname1', 
        'patient__cedula', 'electronic_invoice__invoice_number'
    ]
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PatientInvoiceItemInline]
    
    fieldsets = (
        ('Información de Factura', {
            'fields': ('electronic_invoice', 'invoice_number', 'date', 'patient', 'branch')
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Cantidad de Tratamientos'
    
    def invoice_total(self, obj):
        total = sum(item.total for item in obj.items.all())
        return f"₡{total:,.2f}"
    invoice_total.short_description = 'Total Factura'


@admin.register(PatientInvoiceItem)
class PatientInvoiceItemAdmin(admin.ModelAdmin):
    list_display = [
        'patient_invoice', 'treatment', 'quantity', 
        'unit_price_display', 'subtotal_display', 
        'monto_asembis_display', 'monto_dr_display', 
        'iva_display', 'total_display'
    ]
    list_filter = [
        'patient_invoice__date', 
        'patient_invoice__branch',
        'treatment'
    ]
    search_fields = [
        'patient_invoice__invoice_number',
        'patient_invoice__patient__name',
        'patient_invoice__patient__cedula',
        'treatment__name'
    ]
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Información del Tratamiento', {
            'fields': ('patient_invoice', 'treatment', 'quantity', 'unit_price')
        }),
        ('Cálculos', {
            'fields': (
                'subtotal_display', 'monto_asembis_display', 
                'monto_dr_display', 'iva_display', 'total_display'
            ),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def unit_price_display(self, obj):
        return f"₡{obj.unit_price:,.2f}"
    unit_price_display.short_description = 'Precio Unitario'
    unit_price_display.admin_order_field = 'unit_price'
    
    def subtotal_display(self, obj):
        return f"₡{obj.subtotal:,.2f}"
    subtotal_display.short_description = 'Subtotal'
    
    def monto_asembis_display(self, obj):
        return f"₡{obj.monto_asembis:,.2f}"
    monto_asembis_display.short_description = 'Monto ASEMBIS (15%)'
    
    def monto_dr_display(self, obj):
        return f"₡{obj.monto_dr:,.2f}"
    monto_dr_display.short_description = 'Monto DR (85%)'
    
    def iva_display(self, obj):
        return f"₡{obj.iva:,.2f}"
    iva_display.short_description = 'I.V.A. (4%)'
    
    def total_display(self, obj):
        return format_html(
            '<strong>₡{:,.2f}</strong>', 
            obj.total
        )
    total_display.short_description = 'Total'


# Customize Admin Site Headers
admin.site.site_header = 'Sistema de Facturación Médica'
admin.site.site_title = 'Admin Facturación'
admin.site.index_title = 'Administración del Sistema'