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
    Branch, Treatment, ElectronicInvoice, 
    PatientInvoice, PatientInvoiceItem
)
from .forms import (
    ElectronicInvoiceForm, PatientInvoiceForm, StandalonePatientInvoiceForm,
    PatientInvoiceItemForm, TreatmentForm
)


class DashboardView(LoginRequiredMixin, ListView):
    """Dashboard principal con resumen de facturas - Updated for new workflow"""
    template_name = 'invoicing/dashboard.html'
    context_object_name = 'recent_invoices'
    paginate_by = 10

    def get_queryset(self):
        # Show recent patient invoices instead of electronic invoices
        return PatientInvoice.objects.order_by('-date')[:10]

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
            'total_treatments': Treatment.objects.filter(is_active=True).count(),
            'monthly_invoices': PatientInvoice.objects.filter(
                date__month=current_month,
                date__year=current_year
            ).count(),
            'monthly_revenue': monthly_stats['total_revenue'] or Decimal('0.00'),
            'monthly_items': monthly_stats['total_items'] or 0,
            'unassigned_invoices': PatientInvoice.objects.filter(electronic_invoice__isnull=True).count(),
        })
        
        return context


# NEW: Main Patient Invoice Views (new workflow starting point)
class PatientInvoiceListView(LoginRequiredMixin, ListView):
    """Lista de todas las facturas de pacientes"""
    model = PatientInvoice
    template_name = 'invoicing/invoice_list.html'  # ADD THIS LINE
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        queryset = PatientInvoice.objects.select_related('branch', 'electronic_invoice').prefetch_related('items').order_by('-date')
        
        # Filtros
        search = self.request.GET.get('search')
        assigned = self.request.GET.get('assigned')
        branch = self.request.GET.get('branch')
        
        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search) |
                Q(patient_name__icontains=search)
            )
            
        if assigned == 'yes':
            queryset = queryset.filter(electronic_invoice__isnull=False)
        elif assigned == 'no':
            queryset = queryset.filter(electronic_invoice__isnull=True)
            
        if branch:
            queryset = queryset.filter(branch_id=branch)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['branches'] = Branch.objects.all()
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'assigned': self.request.GET.get('assigned', ''),
            'branch': self.request.GET.get('branch', ''),
        }
        return context


class PatientInvoiceCreateView(LoginRequiredMixin, CreateView):
    """Crear nueva factura de paciente - NEW MAIN WORKFLOW START"""
    model = PatientInvoice
    form_class = StandalonePatientInvoiceForm
    template_name = 'invoicing/invoice_form.html'

    def get_success_url(self):
        return reverse('invoicing:patient_invoice_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Factura de paciente creada exitosamente. Ahora puede agregar tratamientos.')
        return super().form_valid(form)


class PatientInvoiceDetailView(LoginRequiredMixin, DetailView):
    """Detalle de factura de paciente con items"""
    model = PatientInvoice
    template_name = 'invoicing/invoice_detail.html'
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


class PatientInvoiceUpdateView(LoginRequiredMixin, UpdateView):
    """Actualizar factura de paciente"""
    model = PatientInvoice
    form_class = StandalonePatientInvoiceForm
    template_name = 'invoicing/invoice_form.html'

    def get_success_url(self):
        return reverse('invoicing:patient_invoice_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Factura de paciente actualizada exitosamente.')
        return super().form_valid(form)


# Electronic Invoice Views (now for grouping)
class ElectronicInvoiceListView(LoginRequiredMixin, ListView):
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
        context['unassigned_count'] = PatientInvoice.objects.filter(electronic_invoice__isnull=True).count()
        return context


class ElectronicInvoiceCreateView(LoginRequiredMixin, CreateView):
    """Crear nueva factura electrónica"""
    model = ElectronicInvoice
    form_class = ElectronicInvoiceForm
    template_name = 'invoicing/electronic_invoice_form.html'

    def get_success_url(self):
        return reverse('invoicing:electronic_invoice_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Factura electrónica creada exitosamente.')
        return super().form_valid(form)


class ElectronicInvoiceDetailView(LoginRequiredMixin, DetailView):
    """Detalle de factura electrónica"""
    model = ElectronicInvoice
    template_name = 'invoicing/electronic_invoice_detail.html'
    context_object_name = 'electronic_invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient_invoices = self.object.patient_invoices.select_related('branch').prefetch_related('items__treatment')
        
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
            },
            'unassigned_invoices': PatientInvoice.objects.filter(electronic_invoice__isnull=True).order_by('-date')
        })
        
        return context


class ElectronicInvoicePDFView(LoginRequiredMixin, DetailView):
    """Export electronic invoice as PDF"""
    model = ElectronicInvoice
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        patient_invoices = self.object.patient_invoices.select_related('branch').prefetch_related('items__treatment')
        
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


# NEW: Assign invoices to electronic invoice
@login_required
def assign_to_electronic_invoice(request, electronic_invoice_id):
    """Assign patient invoices to an electronic invoice"""
    electronic_invoice = get_object_or_404(ElectronicInvoice, id=electronic_invoice_id)
    
    if request.method == 'POST':
        invoice_ids = request.POST.getlist('invoice_ids')
        if invoice_ids:
            PatientInvoice.objects.filter(
                id__in=invoice_ids,
                electronic_invoice__isnull=True
            ).update(electronic_invoice=electronic_invoice)
            
            messages.success(request, f'Se asignaron {len(invoice_ids)} facturas a la factura electrónica.')
        else:
            messages.warning(request, 'No se seleccionaron facturas para asignar.')
    
    return redirect('invoicing:electronic_invoice_detail', pk=electronic_invoice_id)


# Branch Views
class BranchListView(LoginRequiredMixin, ListView):
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


class BranchCreateView(LoginRequiredMixin, CreateView):
    """Crear nueva sucursal"""
    model = Branch
    fields = ['name']
    template_name = 'invoicing/branch_form.html'
    success_url = reverse_lazy('invoicing:branch_list')

    def form_valid(self, form):
        messages.success(self.request, 'Sucursal creada exitosamente.')
        return super().form_valid(form)


class BranchUpdateView(LoginRequiredMixin, UpdateView):
    """Actualizar sucursal"""
    model = Branch
    fields = ['name']
    template_name = 'invoicing/branch_form.html'
    success_url = reverse_lazy('invoicing:branch_list')

    def form_valid(self, form):
        messages.success(self.request, 'Sucursal actualizada exitosamente.')
        return super().form_valid(form)

# Treatment Views
class TreatmentListView(LoginRequiredMixin, ListView):
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


class TreatmentCreateView(LoginRequiredMixin, CreateView):
    """Crear nuevo tratamiento"""
    model = Treatment
    form_class = TreatmentForm
    template_name = 'invoicing/treatment_form.html'
    success_url = reverse_lazy('invoicing:treatment_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tratamiento creado exitosamente.')
        return super().form_valid(form)


class TreatmentUpdateView(LoginRequiredMixin, UpdateView):
    """Actualizar tratamiento"""
    model = Treatment
    form_class = TreatmentForm
    template_name = 'invoicing/treatment_form.html'
    success_url = reverse_lazy('invoicing:treatment_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tratamiento actualizado exitosamente.')
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