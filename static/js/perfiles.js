/**
 * JavaScript para mejorar la funcionalidad de Perfiles Contables
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-hide messages after 5 seconds
    const messages = document.querySelectorAll('.alert');
    messages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.5s ease-out';
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000);
    });

    // Confirmation for delete actions
    const deleteButtons = document.querySelectorAll('a[href*="delete"]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('¿Está seguro de que desea eliminar este perfil? Esta acción no se puede deshacer.')) {
                e.preventDefault();
            }
        });
    });

    // Form validation enhancements
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
            let hasErrors = false;

            requiredFields.forEach(function(field) {
                const fieldContainer = field.closest('.space-y-2, .mb-3');
                const existingError = fieldContainer ? fieldContainer.querySelector('.error-message') : null;

                if (existingError) {
                    existingError.remove();
                }

                if (!field.value.trim()) {
                    hasErrors = true;
                    field.classList.add('border-red-500', 'ring-red-500');
                    
                    if (fieldContainer) {
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'flex items-center space-x-2 text-red-600 text-sm error-message';
                        errorDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i><span>Este campo es obligatorio</span>';
                        fieldContainer.appendChild(errorDiv);
                    }
                } else {
                    field.classList.remove('border-red-500', 'ring-red-500');
                    field.classList.add('border-green-500');
                }
            });

            if (hasErrors) {
                e.preventDefault();
                scrollToFirstError();
            }
        });
    });

    // Scroll to first error
    function scrollToFirstError() {
        const firstError = document.querySelector('.border-red-500');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstError.focus();
        }
    }

    // Real-time field validation
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            validateField(this);
        });

        input.addEventListener('input', function() {
            if (this.classList.contains('border-red-500')) {
                validateField(this);
            }
        });
    });

    function validateField(field) {
        const fieldContainer = field.closest('.space-y-2, .mb-3');
        const existingError = fieldContainer ? fieldContainer.querySelector('.error-message') : null;

        if (existingError) {
            existingError.remove();
        }

        field.classList.remove('border-red-500', 'ring-red-500', 'border-green-500');

        if (field.required && !field.value.trim()) {
            field.classList.add('border-red-500', 'ring-red-500');
            
            if (fieldContainer) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'flex items-center space-x-2 text-red-600 text-sm error-message';
                errorDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i><span>Este campo es obligatorio</span>';
                fieldContainer.appendChild(errorDiv);
            }
        } else if (field.value.trim()) {
            field.classList.add('border-green-500');
        }

        // Specific validation for secuencial (numbers only)
        if (field.name === 'secuencial' && field.value) {
            const isValid = /^\d+$/.test(field.value) && parseInt(field.value) > 0;
            if (!isValid) {
                field.classList.add('border-red-500', 'ring-red-500');
                
                if (fieldContainer) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'flex items-center space-x-2 text-red-600 text-sm error-message';
                    errorDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i><span>Debe ser un número positivo</span>';
                    fieldContainer.appendChild(errorDiv);
                }
            }
        }

        // Specific validation for empresa (no special characters)
        if (field.name === 'empresa' && field.value) {
            const isValid = /^[A-Z0-9_-]+$/.test(field.value.toUpperCase());
            if (!isValid) {
                field.classList.add('border-red-500', 'ring-red-500');
                
                if (fieldContainer) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'flex items-center space-x-2 text-red-600 text-sm error-message';
                    errorDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i><span>Solo letras, números, guiones y guiones bajos</span>';
                    fieldContainer.appendChild(errorDiv);
                }
            }
        }
    }

    // Uppercase empresa field
    const empresaField = document.querySelector('input[name="empresa"]');
    if (empresaField) {
        empresaField.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    }

    // Enhanced table interactions
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(function(row) {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });

        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });

    // Loading state for form submissions
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const form = this.closest('form');
            if (form && form.checkValidity()) {
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Procesando...';
                
                // Re-enable after 10 seconds as fallback
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = this.innerHTML.replace('<i class="fas fa-spinner fa-spin mr-2"></i>Procesando...', 'Guardar');
                }, 10000);
            }
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl + N for new profile (only on list page)
        if (e.ctrlKey && e.key === 'n' && window.location.pathname.includes('list')) {
            e.preventDefault();
            const newButton = document.querySelector('a[href*="create"]');
            if (newButton) {
                newButton.click();
            }
        }

        // Escape to go back
        if (e.key === 'Escape') {
            const backButton = document.querySelector('a[href*="list"]');
            if (backButton && !window.location.pathname.includes('list')) {
                backButton.click();
            }
        }
    });

    // Print functionality
    function printProfile() {
        window.print();
    }

    // Add print button if needed
    const printButton = document.querySelector('.print-button');
    if (printButton) {
        printButton.addEventListener('click', printProfile);
    }

    console.log('Perfiles JavaScript loaded successfully');
});

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' :
        type === 'error' ? 'bg-red-100 text-red-800 border border-red-200' :
        'bg-blue-100 text-blue-800 border border-blue-200'
    }`;
    
    notification.innerHTML = `
        <div class="flex items-center space-x-2">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-gray-500 hover:text-gray-700">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.5s ease-out';
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 5000);
}
