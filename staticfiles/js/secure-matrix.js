// Variables globales
let spreadsheet;
let lastUpdateTime = new Date();
let hasUnsavedChanges = false;
let undoStack = [];
let redoStack = [];
let isLoggingOut = false;
let securityInitialized = false;

// Función para obtener el token CSRF
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    
    return cookieValue || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

// Configuración del spreadsheet
const spreadsheetConfig = {
    mode: 'edit',
    showToolbar: true,
    showGrid: true,
    showContextmenu: true,
    view: {
        height: () => window.innerHeight,
        width: () => window.innerWidth,
    },
    row: {
        len: 50,
        height: 25,
    },
    col: {
        len: 26,
        width: 100,
        indexWidth: 60,
        minWidth: 60,
    },
    style: {
        align: 'left',
        valign: 'middle',
        textwrap: false,
        strike: false,
        underline: false,
        color: '#000000',
        font: {
            name: 'Arial',
            size: 10,
            bold: false,
            italic: false,
        },
    },
};

// Configurar event listeners para los botones
function setupButtonEventListeners() {
    console.log('Setting up button event listeners...');
    
    // Configurar botón de guardar
    const saveBtn = document.getElementById('save-all-btn');
    if (saveBtn) {
        console.log('Found save button, setting up listener');
        saveBtn.onclick = function() {
            console.log('Save button clicked!');
            saveMatrix();
        };
    } else {
        console.log('Save button not found!');
    }
}

// Inicializar spreadsheet
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    spreadsheet = new x_spreadsheet('#x-spreadsheet-container', spreadsheetConfig);
    
    if (typeof initialData !== 'undefined') {
        loadInitialData(initialData);
    }
    
    setupEventListeners();
    updateUndoRedoButtons();
    
    // Configurar event listeners para los botones
    setTimeout(function() {
        setupButtonEventListeners();
        initializeSecurity();
    }, 500);
});

// Inicializar medidas de seguridad
function initializeSecurity() {
    if (securityInitialized) {
        console.log('Security already initialized');
        return;
    }
    
    console.log('Initializing security measures...');
    securityInitialized = true;
    
    // Configurar prevención de navegación hacia atrás inmediatamente
    setupBackButtonPrevention();
    
    // Configurar detección de recarga/cierre
    setupUnloadHandlers();
    
    // Configurar timer de inactividad
    setupInactivityTimer();
    
    // Configurar detección de pérdida de foco
    setupVisibilityHandlers();
    
    console.log('Security measures initialized successfully');
}

function setupBackButtonPrevention() {
    // Prevenir navegación hacia atrás añadiendo un estado al historial
    history.pushState(null, null, window.location.pathname);
    
    // Interceptar el botón "atrás" del navegador
    window.addEventListener('popstate', function(e) {
        console.log('Popstate event detected');
        // Prevenir la navegación hacia atrás
        e.preventDefault();
        
        let message = hasUnsavedChanges 
            ? '¿Está seguro de que desea salir del modo seguro? Hay cambios sin guardar.'
            : '¿Está seguro de que desea salir del modo seguro?';
            
        if (confirm(message)) {
            performSecureLogout();
        } else {
            // Volver a empujar el estado actual para mantener al usuario en la página
            history.pushState(null, null, window.location.pathname);
        }
    });
}

function setupUnloadHandlers() {
    // Interceptar navegación hacia atrás y recarga de página
    window.addEventListener('beforeunload', function(e) {
        console.log('Beforeunload event detected, hasUnsavedChanges:', hasUnsavedChanges);
        
        let message = hasUnsavedChanges 
            ? '¿Está seguro de que desea salir? Hay cambios sin guardar.'
            : '¿Está seguro de que desea salir del modo seguro?';
        
        // Siempre preguntar antes de salir
        e.preventDefault();
        e.returnValue = message;
        return message;
    });

    // Detectar cuando el usuario realmente está saliendo (después de confirmar)
    window.addEventListener('unload', function(e) {
        console.log('Unload event detected - performing secure logout');
        
        // Usar sendBeacon para logout garantizado
        if (!isLoggingOut && navigator.sendBeacon) {
            try {
                navigator.sendBeacon('/secure/api/logout-beacon/', 
                    JSON.stringify({logout: true})
                );
                console.log('Beacon sent on unload');
            } catch (error) {
                console.error('Error sending beacon on unload:', error);
            }
        }
    });
}

function loadInitialData(data) {
    // Convertir los datos al formato que espera X-Spreadsheet
    const sheetData = {
        name: 'Hoja1',
        rows: {}
    };
    
    Object.keys(data).forEach(rowIndex => {
        const rowData = data[rowIndex];
        if (!sheetData.rows[rowIndex]) {
            sheetData.rows[rowIndex] = { cells: {} };
        }
        
        Object.keys(rowData).forEach(colIndex => {
            sheetData.rows[rowIndex].cells[colIndex] = {
                text: rowData[colIndex]
            };
        });
    });
    
    // Cargar los datos en X-Spreadsheet
    spreadsheet.loadData([sheetData]);
}

function setupEventListeners() {
    // Redimensionar spreadsheet cuando cambie el tamaño de la ventana
    window.addEventListener('resize', function() {
        if (spreadsheet && typeof spreadsheet.resize === 'function') {
            spreadsheet.resize();
        }
    });
    
    // Escuchar cambios en la matriz
    if (spreadsheet && spreadsheet.sheet) {
        spreadsheet.sheet.on('change', function(changes) {
            console.log('Matrix changed:', changes);
            hasUnsavedChanges = true;
            updateUndoRedoButtons();
        });
    }
    
    // Atajos de teclado
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key.toLowerCase()) {
                case 's':
                    e.preventDefault();
                    saveMatrix();
                    break;
                case 'z':
                    e.preventDefault();
                    if (e.shiftKey) {
                        redoAction();
                    } else {
                        undoAction();
                    }
                    break;
                case 'y':
                    e.preventDefault();
                    redoAction();
                    break;
            }
        }
        
        // Tecla Escape para salir del modo seguro
        if (e.key === 'Escape') {
            e.preventDefault();
            if (confirm('¿Desea salir del modo seguro?')) {
                window.logoutSecure();
            }
        }
    });
    
    // Auto-guardado cada 30 segundos si hay cambios
    setInterval(function() {
        if (hasUnsavedChanges) {
            console.log('Auto-guardando cambios...');
            saveMatrix();
        }
    }, 30000);
}

function updateUndoRedoButtons() {
    // Los botones de undo/redo ahora se manejan solo por shortcuts de teclado
    // Esta función se mantiene para compatibilidad pero no hace nada
}

async function undoAction() {
    console.log('undoAction called via keyboard shortcut');
    
    try {
        const csrfToken = getCsrfToken();
        console.log('CSRF Token:', csrfToken);
        
        const response = await fetch('/secure/matrix/undo/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        console.log('Undo response status:', response.status);
        
        if (!response.ok) {
            const responseText = await response.text();
            console.error('Undo error response:', responseText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Undo response data:', data);
        
        if (data.success) {
            if (data.matrix_data) {
                loadInitialData(data.matrix_data);
            } else {
                location.reload();
            }
            showNotification('Acción deshecha exitosamente', 'success');
        } else {
            showNotification(data.error || 'Error al deshacer', 'error');
        }
    } catch (error) {
        console.error('Error en undoAction:', error);
        showNotification('Error al deshacer la acción', 'error');
    }
}

async function redoAction() {
    console.log('redoAction called via keyboard shortcut');
    
    try {
        const csrfToken = getCsrfToken();
        console.log('CSRF Token:', csrfToken);
        
        const response = await fetch('/secure/matrix/redo/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        console.log('Redo response status:', response.status);
        
        if (!response.ok) {
            const responseText = await response.text();
            console.error('Redo error response:', responseText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Redo response data:', data);
        
        if (data.success) {
            if (data.matrix_data) {
                loadInitialData(data.matrix_data);
            } else {
                location.reload();
            }
            showNotification('Acción rehecha exitosamente', 'success');
        } else {
            showNotification(data.error || 'Error al rehacer', 'error');
        }
    } catch (error) {
        console.error('Error en redoAction:', error);
        showNotification('Error al rehacer la acción', 'error');
    }
}

async function saveMatrix() {
    console.log('saveMatrix called');
    const saveBtn = document.getElementById('save-all-btn');
    const saveIcon = document.getElementById('save-btn-icon');
    const saveText = document.getElementById('save-btn-text');
    
    try {
        if (saveBtn) {
            saveBtn.disabled = true;
        }
        if (saveIcon && saveIcon.classList) {
            saveIcon.className = 'fas fa-spinner fa-spin';
        }
        if (saveText) {
            saveText.textContent = 'Guardando...';
        }
        
        // Obtener datos del spreadsheet
        const rawData = spreadsheet.getData();
        console.log('Raw spreadsheet data:', rawData);
        console.log('Tipo de rawData:', typeof rawData, 'Array:', Array.isArray(rawData), 'Longitud:', rawData?.length);
        
        // Convertir los datos a formato compatible con el backend
        const matrixData = {};
        
        if (Array.isArray(rawData) && rawData.length > 0) {
            const sheetData = rawData[0];
            
            if (sheetData && sheetData.rows) {
                Object.keys(sheetData.rows).forEach(rowIndex => {
                    const row = sheetData.rows[rowIndex];
                    if (row && row.cells) {
                        Object.keys(row.cells).forEach(colIndex => {
                            const cell = row.cells[colIndex];
                            if (cell && cell.text) {
                                if (!matrixData[rowIndex]) {
                                    matrixData[rowIndex] = {};
                                }
                                matrixData[rowIndex][colIndex] = cell.text;
                            }
                        });
                    }
                });
            }
        }
        
        console.log('Datos a enviar:', matrixData);
        
        if (Object.keys(matrixData).length === 0) {
            hasUnsavedChanges = false;
            showNotification('No hay cambios que guardar', 'info');
            return;
        }
        
        console.log('Enviando datos al servidor...');
        
        const csrfToken = getCsrfToken();
        console.log('CSRF Token para guardado:', csrfToken);
        
        const payload = {
            matrix_data: matrixData
        };
        console.log('Payload completo a enviar:', JSON.stringify(payload, null, 2));
        
        const response = await fetch('/secure/api/save-matrix/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(payload)
        });
        
        console.log('Save response status:', response.status);
        
        if (!response.ok) {
            const responseText = await response.text();
            console.error('Save error response:', responseText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Save response data:', data);
        
        if (data.success) {
            hasUnsavedChanges = false;
            lastUpdateTime = new Date();
            const lastUpdateElement = document.getElementById('last-update');
            if (lastUpdateElement) {
                lastUpdateElement.textContent = lastUpdateTime.toLocaleTimeString();
            }
            console.log('Guardado exitoso! Celdas actualizadas:', data.cells_updated);
            showNotification(`Matriz guardada: ${data.cells_updated || 0} celdas actualizadas`, 'success');
        } else {
            console.error('Error del servidor al guardar:', data.error);
            showNotification(data.error || 'Error al guardar', 'error');
        }
    } catch (error) {
        console.error('Error en saveMatrix:', error);
        showNotification('Error al guardar la matriz: ' + error.message, 'error');
    } finally {
        if (saveBtn) {
            saveBtn.disabled = false;
        }
        if (saveIcon && saveIcon.classList) {
            saveIcon.className = 'fas fa-save';
        }
        if (saveText) {
            saveText.textContent = 'Guardar';
        }
    }
}

function showNotification(message, type = 'success') {
    // Remover notificaciones existentes con animación
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        if (!notification.classList.contains('closing')) {
            notification.classList.add('closing');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    });
    
    // Crear nueva notificación
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Crear el contenido del mensaje
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    notification.appendChild(messageSpan);
    
    // Agregar al DOM
    document.body.appendChild(notification);
    
    // Auto-remover después de 4 segundos
    setTimeout(() => {
        if (notification.parentNode && !notification.classList.contains('closing')) {
            notification.classList.add('closing');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, 4000);
}

// Hacer las funciones globalmente accesibles
window.undoAction = undoAction;
window.redoAction = redoAction;
window.saveMatrix = saveMatrix;

// Función para salir de la matriz segura
window.logoutSecure = function() {
    if (hasUnsavedChanges) {
        if (confirm('¿Está seguro de que desea salir? Hay cambios sin guardar.')) {
            performSecureLogout();
        }
    } else {
        performSecureLogout();
    }
};

// Función para realizar el logout seguro
function performSecureLogout() {
    if (isLoggingOut) {
        console.log('Logout already in progress, skipping...');
        return;
    }
    
    isLoggingOut = true;
    console.log('Performing secure logout...');
    
    // Usar sendBeacon para asegurar que la petición se envíe aunque se cierre la página
    if (navigator.sendBeacon) {
        try {
            const success = navigator.sendBeacon('/secure/api/logout-beacon/', 
                JSON.stringify({logout: true})
            );
            console.log('Beacon sent:', success);
        } catch (error) {
            console.error('Error sending beacon:', error);
        }
    }
    
    // También hacer una petición normal como respaldo
    try {
        fetch('/secure/logout-secure/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({logout: true})
        }).catch(err => console.log('Logout request error (expected):', err));
    } catch (error) {
        console.error('Error in logout request:', error);
    }
    
    // Limpiar datos locales
    hasUnsavedChanges = false;
    
    // Redirigir
    window.location.href = '/secure/logout-secure/';
}

function setupInactivityTimer() {
    // Detectar inactividad y pérdida de foco para mayor seguridad
    let inactivityTimer;
    const INACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 minutos

    function resetInactivityTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(() => {
            alert('Sesión expirada por inactividad. Será redirigido por seguridad.');
            performSecureLogout();
        }, INACTIVITY_TIMEOUT);
    }

    // Eventos para detectar actividad del usuario
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'].forEach(event => {
        document.addEventListener(event, resetInactivityTimer, true);
    });

    // Iniciar el timer de inactividad
    resetInactivityTimer();
}

function setupVisibilityHandlers() {
    // Detectar pérdida de foco de la ventana
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            console.log('Page hidden - user switched tabs/minimized');
            // Opcional: guardar automáticamente cuando se oculta la página
            if (hasUnsavedChanges) {
                console.log('Auto-saving due to page hidden...');
                saveMatrix();
            }
        } else {
            console.log('Page visible again');
        }
    });
}

console.log('secure-matrix.js loaded successfully');