// Invoice Detail JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const addTreatmentModal = new bootstrap.Modal(document.getElementById('addTreatmentModal'));
    const treatmentSelect = document.getElementById('treatment-select');
    const saveTreatmentBtn = document.getElementById('save-treatment-btn');
    
    // Load treatments when modal opens
    document.getElementById('add-treatment-btn').addEventListener('click', function() {
        loadTreatments();
        addTreatmentModal.show();
    });
    
    // Also handle the "add first treatment" button
    const addFirstBtn = document.getElementById('add-first-treatment-btn');
    if (addFirstBtn) {
        addFirstBtn.addEventListener('click', function() {
            loadTreatments();
            addTreatmentModal.show();
        });
    }
    
    function loadTreatments() {
        fetch('/ajax/treatments/')
            .then(response => response.json())
            .then(data => {
                treatmentSelect.innerHTML = '<option value="">Seleccione un tratamiento...</option>';
                data.treatments.forEach(treatment => {
                    const option = document.createElement('option');
                    option.value = treatment.id;
                    option.textContent = `${treatment.code} - ${treatment.name} (₡${parseFloat(treatment.price).toFixed(2)})`;
                    option.dataset.code = treatment.code;
                    option.dataset.name = treatment.name;
                    option.dataset.price = treatment.price;
                    treatmentSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error loading treatments:', error);
                treatmentSelect.innerHTML = '<option value="">Error cargando tratamientos</option>';
            });
    }
    
    // Treatment selection preview
    treatmentSelect.addEventListener('change', function() {
        const option = this.selectedOptions[0];
        const preview = document.getElementById('treatment-preview');
        
        if (this.value && option) {
            document.getElementById('preview-code').textContent = option.dataset.code;
            document.getElementById('preview-name').textContent = option.dataset.name;
            document.getElementById('preview-price').textContent = formatCurrency(parseFloat(option.dataset.price));
            preview.classList.remove('d-none');
            saveTreatmentBtn.disabled = false;
        } else {
            preview.classList.add('d-none');
            saveTreatmentBtn.disabled = true;
        }
    });
    
    // Save treatment
    saveTreatmentBtn.addEventListener('click', function() {
        const treatmentId = treatmentSelect.value;
        
        if (!treatmentId) {
            alert('Por favor seleccione un tratamiento.');
            return;
        }
        
        showLoading(this);
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        if (!csrfToken) {
            console.error('CSRF token not found');
            hideLoading(this);
            alert('Error: Token de seguridad no encontrado. Recargue la página.');
            return;
        }
        
        // Create form and submit
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = window.location.href;
        
        form.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
            <input type="hidden" name="action" value="add_treatment">
            <input type="hidden" name="treatment_id" value="${treatmentId}">
        `;
        
        document.body.appendChild(form);
        form.submit();
    });
    
    // Delete item functionality
    document.querySelectorAll('.delete-item-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (confirmAction('¿Está seguro de que desea eliminar este tratamiento?')) {
                const itemId = this.closest('tr').dataset.itemId;
                deleteItem(itemId);
            }
        });
    });
    
    function deleteItem(itemId) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        if (!csrfToken) {
            alert('Error: Token de seguridad no encontrado. Recargue la página.');
            return;
        }
        
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = window.location.href;
        
        form.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
            <input type="hidden" name="action" value="delete_item">
            <input type="hidden" name="item_id" value="${itemId}">
        `;
        
        document.body.appendChild(form);
        form.submit();
    }
    
    console.log('Invoice detail JavaScript loaded');
});