# invoicing/urls.py
from django.urls import path
from . import views

app_name = 'invoicing'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # NEW MAIN WORKFLOW: Patient Invoices (now the starting point)
    path('invoices/', views.PatientInvoiceListView.as_view(), name='patient_invoice_list'),
    path('invoices/create/', views.PatientInvoiceCreateView.as_view(), name='patient_invoice_create'),
    path('invoices/<int:pk>/', views.PatientInvoiceDetailView.as_view(), name='patient_invoice_detail'),
    path('invoices/<int:pk>/update/', views.PatientInvoiceUpdateView.as_view(), name='patient_invoice_update'),
    
    # Branch URLs
    path('branches/', views.BranchListView.as_view(), name='branch_list'),
    path('branches/create/', views.BranchCreateView.as_view(), name='branch_create'),
    path('branches/<int:pk>/update/', views.BranchUpdateView.as_view(), name='branch_update'),
    
    path('treatments/', views.TreatmentListView.as_view(), name='treatment_list'),
    path('treatments/create/', views.TreatmentCreateView.as_view(), name='treatment_create'),
    path('treatments/<int:pk>/update/', views.TreatmentUpdateView.as_view(), name='treatment_update'),
    
    # Electronic Invoice URLs (now for grouping existing invoices)
    path('electronic-invoices/', views.ElectronicInvoiceListView.as_view(), name='electronic_invoice_list'),
    path('electronic-invoices/create/', views.ElectronicInvoiceCreateView.as_view(), name='electronic_invoice_create'),
    path('electronic-invoices/<int:pk>/', views.ElectronicInvoiceDetailView.as_view(), name='electronic_invoice_detail'),
    path('electronic-invoices/<int:pk>/pdf/', views.ElectronicInvoicePDFView.as_view(), name='electronic_invoice_pdf'),
    
    # NEW: Assign patient invoices to electronic invoice
    path('electronic-invoices/<int:electronic_invoice_id>/assign/', views.assign_to_electronic_invoice, name='assign_to_electronic_invoice'),
    
    # AJAX endpoints
    path('ajax/treatments/', views.get_treatments_ajax, name='get_treatments_ajax'),
]