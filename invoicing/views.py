from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.forms import inlineformset_factory
from django.template.loader import render_to_string
from datetime import datetime, date
from decimal import Decimal
import weasyprint

from .models import (
    Branch, Patient, Treatment, ElectronicInvoice, 
    PatientInvoice, PatientInvoiceItem
)
from .forms import (
    ElectronicInvoiceForm, PatientInvoiceForm, 
    PatientInvoiceItemForm, PatientForm, TreatmentForm
)


class DashboardView(LoginRequiredMixin, ListView):
    """Dashboard principal con resumen de facturas"""
    template_name = 'invoicing/dashboard.html'
    context_object_name = 'recent_invoices'
    paginate_by = 10

    def get_queryset(self):
        return ElectronicInvoice.objects.order_by('-date')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas del mes actual
        current_month = date.today().month
        current_year = date.today().year
        
        monthly_stats = PatientInvoiceItem.objects.filter(
            patient_invoice__date__month=current_month,
            patient_invoice__date__year=current_year
        ).aggregate(
            total_items=Count('id'),
            total_revenue=Sum('unit_price')
        )
        
        context.update({
            'total_patients': Patient.objects.count(),
            'total_treatments': Treatment.objects.filter(is_active=True).count(),
            'monthly_invoices': PatientInvoice.objects.filter(
                date__month=current_month,
                date__year=current_year
            ).count(),
            'monthly_revenue': monthly_stats['total_revenue'] or Decimal('0.00'),
            'monthly_items': monthly_stats['total_items'] or 0,
        })
        
        return context


class ElectronicInvoicePDFView(LoginRequiredMixin, DetailView):
    """Export electronic invoice as PDF"""
    model = ElectronicInvoice
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        patient_invoices = self.object.patient_invoices.select_related('patient', 'branch').prefetch_related('items__treatment')
        
        # Calculate totals
        total_monto_asembis = Decimal('0.00')
        total_monto_dr = Decimal('0.00')
        total_iva = Decimal('0.00')
        total_general = Decimal('0.00')
        
        for patient_invoice in patient_invoices:
            for item in patient_invoice.items.all():
                total_monto_asembis += item.monto_asembis
                total_monto_dr += item.monto_dr
                total_iva += item.iva
                total_general += item.total
        
        context = {
            'electronic_invoice': self.object,
            'patient_invoices': patient_invoices,
            'totals': {
                'monto_asembis': total_monto_asembis,
                'monto_dr': total_monto_dr,
                'iva': total_iva,
                'total': total_general,
            }
        }
        
        # Render HTML template for PDF
        html_string = render_to_string('invoicing/electronic_invoice_pdf.html', context)
        
        # Generate PDF
        html = weasyprint.HTML(string=html_string)
        pdf = html.write_pdf()
        
        # Return PDF response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="factura_{self.object.invoice_number}.pdf"'
        return response


# Branch Views
class BranchListView(ListView):
    """Lista de sucursales"""
    model = Branch
    template_name = 'invoicing/branch_list.html'
    context_object_name = 'branches'
    paginate_by = 20

    def get_queryset(self):
        queryset = Branch.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset.order_by('name')


class BranchCreateView(CreateView):
    """Crear nueva sucursal"""
    model = Branch
    fields = ['name']
    template_name = 'invoicing/branch_form.html'
    success_url = reverse_lazy('invoicing:branch_list')

    def form_valid(self, form):
        messages.success(self.request, 'Sucursal creada exitosamente.')
        return super().form_valid(form)


class BranchUpdateView(UpdateView):
    """Actualizar sucursal"""
    model = Branch
    fields = ['name']
    template_name = 'invoicing/branch_form.html'
    success_url = reverse_lazy('invoicing:branch_list')

    def form_valid(self, form):
        messages.success(self.request, 'Sucursal actualizada exitosamente.')
        return super().form_valid(form)
class PatientListView(ListView):
    """Lista de pacientes"""
    model = Patient
    template_name = 'invoicing/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 20

    def get_queryset(self):
        queryset = Patient.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(lname1__icontains=search) |
                Q(lname2__icontains=search) |
                Q(cedula__icontains=search)
            )
        return queryset.order_by('lname1', 'lname2', 'name')


class PatientCreateView(CreateView):
    """Crear nuevo paciente"""
    model = Patient
    form_class = PatientForm
    template_name = 'invoicing/patient_form.html'
    success_url = reverse_lazy('invoicing:patient_list')

    def form_valid(self, form):
        messages.success(self.request, 'Paciente creado exitosamente.')
        return super().form_valid(form)


class PatientDetailView(DetailView):
    """Detalle de paciente con historial de facturas"""
    model = Patient
    template_name = 'invoicing/patient_detail.html'
    context_object_name = 'patient'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get patient invoices with related data and calculate totals
        patient_invoices = PatientInvoice.objects.filter(
            patient=self.object
        ).select_related('electronic_invoice', 'branch').prefetch_related('items').order_by('-date')
        
        # Add total calculation for each invoice and count treatments
        invoices_with_totals = []
        total_treatments = 0
        for invoice in patient_invoices:
            total = sum(item.total for item in invoice.items.all())
            invoice.calculated_total = total
            total_treatments += invoice.items.count()
            invoices_with_totals.append(invoice)
        
        context['patient_invoices'] = invoices_with_totals
        context['total_treatments'] = total_treatments
        return context


class PatientUpdateView(UpdateView):
    """Actualizar paciente"""
    model = Patient
    form_class = PatientForm
    template_name = 'invoicing/patient_form.html'

    def get_success_url(self):
        return reverse('invoicing:patient_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Paciente actualizado exitosamente.')
        return super().form_valid(form)


# Treatment Views
class TreatmentListView(ListView):
    """Lista de tratamientos"""
    model = Treatment
    template_name = 'invoicing/treatment_list.html'
    context_object_name = 'treatments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Treatment.objects.all()
        search = self.request.GET.get('search')
        active_only = self.request.GET.get('active_only', 'true')
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )
        
        if active_only == 'true':
            queryset = queryset.filter(is_active=True)
            
        return queryset.order_by('code')


class TreatmentCreateView(CreateView):
    """Crear nuevo tratamiento"""
    model = Treatment
    form_class = TreatmentForm
    template_name = 'invoicing/treatment_form.html'
    success_url = reverse_lazy('invoicing:treatment_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tratamiento creado exitosamente.')
        return super().form_valid(form)


class TreatmentUpdateView(UpdateView):
    """Actualizar tratamiento"""
    model = Treatment
    form_class = TreatmentForm
    template_name = 'invoicing/treatment_form.html'
    success_url = reverse_lazy('invoicing:treatment_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tratamiento actualizado exitosamente.')
        return super().form_valid(form)


# Electronic Invoice Views
class ElectronicInvoiceListView(ListView):
    """Lista de facturas electrónicas"""
    model = ElectronicInvoice
    template_name = 'invoicing/electronic_invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        queryset = ElectronicInvoice.objects.all()
        
        # Filtros
        search = self.request.GET.get('search')
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')
        
        if search:
            queryset = queryset.filter(invoice_number__icontains=search)
            
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        elif year:
            queryset = queryset.filter(date__year=year)
            
        return queryset.order_by('-date', '-invoice_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'month': self.request.GET.get('month', ''),
            'year': self.request.GET.get('year', ''),
        }
        return context


class ElectronicInvoiceCreateView(CreateView):
    """Crear nueva factura electrónica"""
    model = ElectronicInvoice
    form_class = ElectronicInvoiceForm
    template_name = 'invoicing/electronic_invoice_form.html'

    def get_success_url(self):
        return reverse('invoicing:electronic_invoice_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Factura electrónica creada exitosamente.')
        return super().form_valid(form)


class ElectronicInvoiceDetailView(DetailView):
    """Detalle de factura electrónica"""
    model = ElectronicInvoice
    template_name = 'invoicing/electronic_invoice_detail.html'
    context_object_name = 'electronic_invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient_invoices = self.object.patient_invoices.select_related('patient', 'branch').prefetch_related('items__treatment')
        
        # Calcular totales
        total_monto_asembis = Decimal('0.00')
        total_monto_dr = Decimal('0.00')
        total_iva = Decimal('0.00')
        total_general = Decimal('0.00')
        
        for patient_invoice in patient_invoices:
            for item in patient_invoice.items.all():
                total_monto_asembis += item.monto_asembis
                total_monto_dr += item.monto_dr
                total_iva += item.iva
                total_general += item.total
        
        context.update({
            'patient_invoices': patient_invoices,
            'totals': {
                'monto_asembis': total_monto_asembis,
                'monto_dr': total_monto_dr,
                'iva': total_iva,
                'total': total_general,
            }
        })
        
        return context


# Patient Invoice Views
class PatientInvoiceCreateView(CreateView):
    """Crear factura de paciente"""
    model = PatientInvoice
    form_class = PatientInvoiceForm
    template_name = 'invoicing/patient_invoice_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        electronic_invoice_id = self.kwargs.get('electronic_invoice_id')
        if electronic_invoice_id:
            kwargs['electronic_invoice_id'] = electronic_invoice_id
        return kwargs

    def get_success_url(self):
        return reverse('invoicing:patient_invoice_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Factura de paciente creada exitosamente.')
        return super().form_valid(form)


class PatientInvoiceDetailView(DetailView):
    """Detalle de factura de paciente con items"""
    model = PatientInvoice
    template_name = 'invoicing/patient_invoice_detail.html'
    context_object_name = 'patient_invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = self.object.items.select_related('treatment')
        
        # Calcular totales
        total_subtotal = sum(item.subtotal for item in items)
        total_monto_asembis = sum(item.monto_asembis for item in items)
        total_monto_dr = sum(item.monto_dr for item in items)
        total_iva = sum(item.iva for item in items)
        total_general = sum(item.total for item in items)
        
        context.update({
            'items': items,
            'totals': {
                'subtotal': total_subtotal,
                'monto_asembis': total_monto_asembis,
                'monto_dr': total_monto_dr,
                'iva': total_iva,
                'total': total_general,
            }
        })
        
        return context

    def post(self, request, *args, **kwargs):
        """Handle POST requests for adding/updating/deleting treatments"""
        self.object = self.get_object()
        action = request.POST.get('action')
        
        if action == 'add_treatment':
            return self.add_treatment(request)
        elif action == 'update_quantity':
            return self.update_quantity(request)
        elif action == 'delete_item':
            return self.delete_item(request)
        
        messages.error(request, 'Acción no válida.')
        return redirect('invoicing:patient_invoice_detail', pk=self.object.pk)
    
    def add_treatment(self, request):
        """Add a treatment to the patient invoice"""
        treatment_id = request.POST.get('treatment_id')
        
        try:
            treatment = Treatment.objects.get(id=treatment_id, is_active=True)
            quantity = 1  # Always use quantity = 1
            
            # Check if treatment already exists for this patient invoice
            existing_item = PatientInvoiceItem.objects.filter(
                patient_invoice=self.object,
                treatment=treatment
            ).first()
            
            if existing_item:
                messages.warning(request, f'El tratamiento {treatment.name} ya está agregado a esta factura.')
            else:
                # Create new item
                PatientInvoiceItem.objects.create(
                    patient_invoice=self.object,
                    treatment=treatment,
                    quantity=quantity,
                    unit_price=treatment.price
                )
                messages.success(request, f'Se agregó {treatment.name} a la factura.')
                
        except Treatment.DoesNotExist:
            messages.error(request, 'Tratamiento no encontrado.')
        except Exception as e:
            messages.error(request, f'Error al agregar tratamiento: {str(e)}')
        
        return redirect('invoicing:patient_invoice_detail', pk=self.object.pk)
    
    def update_quantity(self, request):
        """Update quantity of an existing treatment item"""
        item_id = request.POST.get('item_id')
        quantity = request.POST.get('quantity')
        
        try:
            item = PatientInvoiceItem.objects.get(
                id=item_id,
                patient_invoice=self.object
            )
            quantity = int(quantity)
            
            if quantity <= 0:
                messages.error(request, 'La cantidad debe ser mayor a cero.')
                return redirect('invoicing:patient_invoice_detail', pk=self.object.pk)
            
            item.quantity = quantity
            item.save()
            messages.success(request, f'Se actualizó la cantidad de {item.treatment.name} a {quantity}.')
            
        except PatientInvoiceItem.DoesNotExist:
            messages.error(request, 'Item no encontrado.')
        except ValueError:
            messages.error(request, 'Cantidad no válida.')
        except Exception as e:
            messages.error(request, f'Error al actualizar cantidad: {str(e)}')
        
        return redirect('invoicing:patient_invoice_detail', pk=self.object.pk)
    
    def delete_item(self, request):
        """Delete a treatment item from the patient invoice"""
        item_id = request.POST.get('item_id')
        
        try:
            item = PatientInvoiceItem.objects.get(
                id=item_id,
                patient_invoice=self.object
            )
            treatment_name = item.treatment.name
            item.delete()
            messages.success(request, f'Se eliminó {treatment_name} de la factura.')
            
        except PatientInvoiceItem.DoesNotExist:
            messages.error(request, 'Item no encontrado.')
        except Exception as e:
            messages.error(request, f'Error al eliminar item: {str(e)}')
        
        return redirect('invoicing:patient_invoice_detail', pk=self.object.pk)


class PatientInvoiceUpdateView(UpdateView):
    """Actualizar factura de paciente"""
    model = PatientInvoice
    form_class = PatientInvoiceForm
    template_name = 'invoicing/patient_invoice_form.html'

    def get_success_url(self):
        return reverse('invoicing:patient_invoice_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Factura de paciente actualizada exitosamente.')
        return super().form_valid(form)


# Ajax Views for dynamic functionality
def get_treatments_ajax(request):
    """API endpoint para obtener tratamientos activos"""
    search = request.GET.get('search', '')
    treatments = Treatment.objects.filter(is_active=True)
    
    if search:
        treatments = treatments.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search)
        )
    
    treatments = treatments[:10]  # Limit results
    
    data = [{
        'id': t.id,
        'code': t.code,
        'name': t.name,
        'price': str(t.price)
    } for t in treatments]
    
    return JsonResponse({'treatments': data})


def get_patients_ajax(request):
    """API endpoint para obtener pacientes"""
    search = request.GET.get('search', '')
    patients = Patient.objects.all()
    
    if search:
        patients = patients.filter(
            Q(name__icontains=search) |
            Q(lname1__icontains=search) |
            Q(lname2__icontains=search)
        )
    
    patients = patients[:10]  # Limit results
    
    data = [{
        'id': p.id,
        'full_name': p.full_name
    } for p in patients]
    
    return JsonResponse({'patients': data})


def create_patient_ajax(request):
    """API endpoint para crear pacientes via AJAX"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            name = data.get('name', '').strip()
            lname1 = data.get('lname1', '').strip()
            lname2 = data.get('lname2', '').strip()
            
            if not name or not lname1:
                return JsonResponse({
                    'success': False,
                    'error': 'Nombre y primer apellido son obligatorios.'
                })
            
            # Create patient
            patient = Patient.objects.create(
                name=name,
                lname1=lname1,
                lname2=lname2
            )
            
            return JsonResponse({
                'success': True,
                'patient': {
                    'id': patient.id,
                    'full_name': patient.full_name
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido.'})


# Update the existing function to remove cedula references
def get_patients_ajax_old(request):
    """API endpoint para obtener pacientes"""
    search = request.GET.get('search', '')
    patients = Patient.objects.all()
    
    if search:
        patients = patients.filter(
            Q(name__icontains=search) |
            Q(lname1__icontains=search) |
            Q(lname2__icontains=search) |
            Q(cedula__icontains=search)
        )
    
    patients = patients[:10]  # Limit results
    
    data = [{
        'id': p.id,
        'cedula': p.cedula,
        'full_name': p.full_name
    } for p in patients]
    
    return JsonResponse({'patients': data})