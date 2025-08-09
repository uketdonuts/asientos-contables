/**
 * Sistema de Asientos Contables - JavaScript Principal
 * Funcionalidades generales y utilidades para la interfaz
 */

$(document).ready(function() {
    // Configuración inicial
    initializeComponents();
    
    // Manejadores de eventos
    setupEventHandlers();
    
    // Inicializar tooltips
    initializeTooltips();
    
    // Configurar animaciones
    setupAnimations();
});

/**
 * Inicializa todos los componentes de la interfaz
 */
function initializeComponents() {
    // Configurar Select2 con tema Bootstrap
    $('.select2').select2({
        theme: 'bootstrap4',
        language: 'es',
        placeholder: 'Seleccione una opción...',
        allowClear: true
    });
    
    // Configurar DateTimePicker
    $('.datetimepicker').datetimepicker({
        format: 'YYYY-MM-DD HH:mm',
        locale: 'es',
        icons: {
            time: 'fas fa-clock',
            date: 'fas fa-calendar',
            up: 'fas fa-chevron-up',
            down: 'fas fa-chevron-down',
            previous: 'fas fa-chevron-left',
            next: 'fas fa-chevron-right',
            today: 'fas fa-calendar-check',
            clear: 'fas fa-trash',
            close: 'fas fa-times'
        }
    });
    
    // Configurar DatePicker
    $('.datepicker').datetimepicker({
        format: 'YYYY-MM-DD',
        locale: 'es',
        icons: {
            time: 'fas fa-clock',
            date: 'fas fa-calendar',
            up: 'fas fa-chevron-up',
            down: 'fas fa-chevron-down',
            previous: 'fas fa-chevron-left',
            next: 'fas fa-chevron-right',
            today: 'fas fa-calendar-check',
            clear: 'fas fa-trash',
            close: 'fas fa-times'
        }
    });
}

/**
 * Configura todos los manejadores de eventos
 */
function setupEventHandlers() {
    // Confirmación de eliminación con SweetAlert2
    $(document).on('click', '.delete-button-swal', function(e) {
        e.preventDefault();
        var deleteUrl = $(this).attr('href');
        var itemName = $(this).data('item-name') || 'este elemento';

        Swal.fire({
            title: '¿Está seguro?',
            text: `¿Realmente desea eliminar ${itemName}? Esta acción no se puede deshacer.`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#e74c3c',
            cancelButtonColor: '#95a5a6',
            confirmButtonText: '<i class="fas fa-trash"></i> Sí, eliminar',
            cancelButtonText: '<i class="fas fa-times"></i> Cancelar',
            customClass: {
                confirmButton: 'btn btn-danger',
                cancelButton: 'btn btn-secondary'
            },
            buttonsStyling: false
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = deleteUrl;
            }
        });
    });
    
    // Animación de carga para formularios
    $('form').on('submit', function() {
        var submitBtn = $(this).find('button[type="submit"]');
        var originalText = submitBtn.html();
        
        submitBtn.prop('disabled', true);
        submitBtn.html('<i class="fas fa-spinner fa-spin"></i> Procesando...');
        
        // Restaurar el botón después de 10 segundos si no se redirige
        setTimeout(function() {
            submitBtn.prop('disabled', false);
            submitBtn.html(originalText);
        }, 10000);
    });
    
    // Validación de balance contable en tiempo real
    $(document).on('input', '.valor-debe, .valor-haber', function() {
        calcularBalance();
    });
    
    // Auto-formateo de números
    $(document).on('blur', '.currency-input', function() {
        var value = parseFloat($(this).val().replace(/[^\d.-]/g, ''));
        if (!isNaN(value)) {
            $(this).val(value.toLocaleString('es-CO', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }));
        }
    });
    
    // Mostrar/ocultar contraseña
    $(document).on('click', '.toggle-password', function() {
        var input = $($(this).data('target'));
        var icon = $(this).find('i');
        
        if (input.attr('type') === 'password') {
            input.attr('type', 'text');
            icon.removeClass('fa-eye').addClass('fa-eye-slash');
        } else {
            input.attr('type', 'password');
            icon.removeClass('fa-eye-slash').addClass('fa-eye');
        }
    });
}

/**
 * Inicializa los tooltips de Bootstrap
 */
function initializeTooltips() {
    $('[data-toggle="tooltip"]').tooltip({
        container: 'body',
        html: true
    });
}

/**
 * Configura las animaciones de la interfaz
 */
function setupAnimations() {
    // Animación de entrada para las tarjetas
    $('.card').addClass('animate__animated animate__fadeInUp');
    
    // Animación para los botones al hacer hover
    $('.btn').on('mouseenter', function() {
        $(this).addClass('animate__animated animate__pulse');
    }).on('mouseleave', function() {
        $(this).removeClass('animate__animated animate__pulse');
    });
}

/**
 * Calcula el balance contable en tiempo real
 */
function calcularBalance() {
    var totalDebe = 0;
    var totalHaber = 0;
    
    $('.valor-debe').each(function() {
        var valor = parseFloat($(this).val()) || 0;
        totalDebe += valor;
    });
    
    $('.valor-haber').each(function() {
        var valor = parseFloat($(this).val()) || 0;
        totalHaber += valor;
    });
    
    var balance = totalDebe - totalHaber;
    
    // Actualizar indicadores visuales
    $('#total-debe').text(totalDebe.toLocaleString('es-CO', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }));
    
    $('#total-haber').text(totalHaber.toLocaleString('es-CO', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }));
    
    var balanceElement = $('#balance');
    if (balanceElement.length) {
        balanceElement.text(balance.toLocaleString('es-CO', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }));
        
        // Cambiar color según el balance
        balanceElement.removeClass('text-success text-danger text-warning');
        if (balance === 0) {
            balanceElement.addClass('text-success');
        } else {
            balanceElement.addClass('text-danger');
        }
    }
    
    // Habilitar/deshabilitar botón de guardar
    var saveBtn = $('#save-asiento');
    if (saveBtn.length) {
        if (balance === 0 && totalDebe > 0) {
            saveBtn.prop('disabled', false).removeClass('btn-secondary').addClass('btn-success');
        } else {
            saveBtn.prop('disabled', true).removeClass('btn-success').addClass('btn-secondary');
        }
    }
}

/**
 * Muestra un mensaje de éxito con SweetAlert2
 */
function showSuccessMessage(title, message) {
    Swal.fire({
        title: title,
        text: message,
        icon: 'success',
        confirmButtonText: 'Aceptar',
        customClass: {
            confirmButton: 'btn btn-success'
        },
        buttonsStyling: false
    });
}

/**
 * Muestra un mensaje de error con SweetAlert2
 */
function showErrorMessage(title, message) {
    Swal.fire({
        title: title,
        text: message,
        icon: 'error',
        confirmButtonText: 'Aceptar',
        customClass: {
            confirmButton: 'btn btn-danger'
        },
        buttonsStyling: false
    });
}

/**
 * Muestra un mensaje de advertencia con SweetAlert2
 */
function showWarningMessage(title, message) {
    Swal.fire({
        title: title,
        text: message,
        icon: 'warning',
        confirmButtonText: 'Aceptar',
        customClass: {
            confirmButton: 'btn btn-warning'
        },
        buttonsStyling: false
    });
}

/**
 * Formatea un número como moneda colombiana
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Valida si un email es válido
 */
function isValidEmail(email) {
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Muestra un loading overlay
 */
function showLoading(message = 'Cargando...') {
    Swal.fire({
        title: message,
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
}

/**
 * Oculta el loading overlay
 */
function hideLoading() {
    Swal.close();
}
