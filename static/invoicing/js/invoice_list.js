// Invoice List JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-submit filters when dropdowns change
    const filterSelects = document.querySelectorAll('select[name="assigned"], select[name="branch"]');
    filterSelects.forEach(function(select) {
        select.addEventListener('change', function() {
            document.getElementById('filter-form').submit();
        });
    });
    
    // Search functionality with debounce
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                if (searchInput.value.length >= 2 || searchInput.value.length === 0) {
                    document.getElementById('filter-form').submit();
                }
            }, 500);
        });
    }
    
    console.log('Invoice list JavaScript loaded');
});