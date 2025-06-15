// Invoice Form JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('invoice-form');
    const submitBtn = document.getElementById('submit-btn');
    
    // Set today's date as default
    const dateField = document.querySelector('[name="date"]');
    if (dateField && !dateField.value) {
        const today = new Date().toISOString().split('T')[0];
        dateField.value = today;
    }
    
    // Auto-generate invoice number suggestion
    const invoiceNumberField = document.querySelector('[name="invoice_number"]');
    if (invoiceNumberField && !invoiceNumberField.value) {
        const now = new Date();
        const suggestion = 'FAC-' + String(now.getTime()).slice(-6);
        invoiceNumberField.placeholder = `Ejemplo: ${suggestion}`;
    }
    
    // Form submission handling
    form.addEventListener('submit', function(e) {
        showLoading(submitBtn);
    });
    
    console.log('Invoice form JavaScript loaded');
});