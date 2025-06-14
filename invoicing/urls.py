# invoicing/urls.py
from django.urls import path
from . import views

app_name = 'invoicing'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Branch URLs
    path('branches/', views.BranchListView.as_view(), name='branch_list'),
    path('branches/create/', views.BranchCreateView.as_view(), name='branch_create'),
    path('branches/<int:pk>/update/', views.BranchUpdateView.as_view(), name='branch_update'),
    
    # Patient URLs
    path('patients/', views.PatientListView.as_view(), name='patient_list'),
    path('patients/create/', views.PatientCreateView.as_view(), name='patient_create'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient_detail'),
    path('patients/<int:pk>/update/', views.PatientUpdateView.as_view(), name='patient_update'),
    
    # Treatment URLs
    path('treatments/', views.TreatmentListView.as_view(), name='treatment_list'),
    path('treatments/create/', views.TreatmentCreateView.as_view(), name='treatment_create'),
    path('treatments/<int:pk>/update/', views.TreatmentUpdateView.as_view(), name='treatment_update'),
    
    # Electronic Invoice URLs
    path('electronic-invoices/', views.ElectronicInvoiceListView.as_view(), name='electronic_invoice_list'),
    path('electronic-invoices/create/', views.ElectronicInvoiceCreateView.as_view(), name='electronic_invoice_create'),
    path('electronic-invoices/<int:pk>/', views.ElectronicInvoiceDetailView.as_view(), name='electronic_invoice_detail'),
    path('electronic-invoices/<int:pk>/pdf/', views.ElectronicInvoicePDFView.as_view(), name='electronic_invoice_pdf'),
    
    # Patient Invoice URLs
    path('patient-invoices/<int:pk>/', views.PatientInvoiceDetailView.as_view(), name='patient_invoice_detail'),
    path('patient-invoices/<int:pk>/update/', views.PatientInvoiceUpdateView.as_view(), name='patient_invoice_update'),
    path('electronic-invoices/<int:electronic_invoice_id>/patient-invoices/create/', 
         views.PatientInvoiceCreateView.as_view(), name='patient_invoice_create'),
    
    # AJAX endpoints
    path('ajax/treatments/', views.get_treatments_ajax, name='get_treatments_ajax'),
    path('ajax/patients/', views.get_patients_ajax, name='get_patients_ajax'),
    path('ajax/create-patient/', views.create_patient_ajax, name='create_patient_ajax'),
]


# core/urls.py (Main project URLs)
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('invoicing.urls')),
]
"""