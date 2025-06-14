// Main JavaScript for Medical Billing System

document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Currency formatting function
    window.formatCurrency = function(amount) {
        return new Intl.NumberFormat('es-CR', {
            style: 'currency',
            currency: 'CRC',
            minimumFractionDigits: 2
        }).format(amount);
    };

    // Format all elements with currency class
    const currencyElements = document.querySelectorAll('.format-currency');
    currencyElements.forEach(function(element) {
        const amount = parseFloat(element.textContent);
        if (!isNaN(amount)) {
            element.textContent = formatCurrency(amount);
        }
    });

    // Form validation helpers
    window.showFieldError = function(fieldName, message) {
        const field = document.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.classList.add('is-invalid');
            let feedback = field.parentNode.querySelector('.invalid-feedback');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                field.parentNode.appendChild(feedback);
            }
            feedback.textContent = message;
        }
    };

    window.clearFieldErrors = function() {
        document.querySelectorAll('.is-invalid').forEach(function(field) {
            field.classList.remove('is-invalid');
        });
        document.querySelectorAll('.invalid-feedback').forEach(function(feedback) {
            feedback.remove();
        });
    };

    // Loading state helpers
    window.showLoading = function(element) {
        element.classList.add('loading');
        const originalText = element.textContent;
        element.setAttribute('data-original-text', originalText);
        element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Cargando...';
    };

    window.hideLoading = function(element) {
        element.classList.remove('loading');
        const originalText = element.getAttribute('data-original-text');
        if (originalText) {
            element.textContent = originalText;
            element.removeAttribute('data-original-text');
        }
    };

    // Search functionality
    window.initializeSearch = function(searchInput, searchCallback) {
        let timeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                searchCallback(searchInput.value);
            }, 300);
        });
    };

    console.log('Medical Billing System - JavaScript loaded successfully');
});