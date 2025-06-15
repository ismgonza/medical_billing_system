// Clean Medical Billing System JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Currency formatting
    window.formatCurrency = function(amount) {
        return new Intl.NumberFormat('es-CR', {
            style: 'currency',
            currency: 'CRC',
            minimumFractionDigits: 2
        }).format(amount);
    };

    // Format currency elements
    const currencyElements = document.querySelectorAll('.format-currency');
    currencyElements.forEach(function(element) {
        const amount = parseFloat(element.textContent);
        if (!isNaN(amount)) {
            element.textContent = formatCurrency(amount);
        }
    });

    // Loading states
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

    // Search functionality with debounce
    window.initializeSearch = function(searchInput, searchCallback) {
        let timeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                searchCallback(searchInput.value);
            }, 300);
        });
    };

    // Confirmation dialogs
    window.confirmAction = function(message) {
        return confirm(message || '¿Está seguro de que desea realizar esta acción?');
    };

    console.log('Sistema de Facturación - JavaScript cargado correctamente');
});