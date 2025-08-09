/**
 * JavaScript para Plan de Cuentas - Funcionalidades avanzadas
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Plan de Cuentas JavaScript iniciado');
    
    // Variables globales
    let isTreeView = false;
    let currentSortColumn = -1;
    let currentSortDirection = 'asc';
    let originalTableData = [];
    
    // Inicializar funcionalidades
    initializeSearch();
    initializeFilters();
    initializeSorting();
    initializeKeyboardShortcuts();
    initializeTooltips();
    
    // Guardar datos originales de la tabla
    saveOriginalTableData();
    
    /**
     * Funcionalidad de búsqueda en tiempo real
     */
    function initializeSearch() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', debounce(performSearch, 300));
        }
    }
    
    function performSearch() {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();
        const tableBody = document.getElementById('cuentasTableBody');
        const rows = tableBody.querySelectorAll('tr');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const codigo = row.querySelector('code').textContent.toLowerCase();
            const descripcion = row.cells[3].textContent.toLowerCase();
            const empresa = row.cells[0].textContent.toLowerCase();
            
            const matches = codigo.includes(searchTerm) || 
                           descripcion.includes(searchTerm) || 
                           empresa.includes(searchTerm);
            
            if (matches || searchTerm === '') {
                row.style.display = '';
                highlightSearchTerm(row, searchTerm);
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        updateVisibleCount(visibleCount);
    }
    
    function highlightSearchTerm(row, searchTerm) {
        const cells = row.querySelectorAll('td');
        cells.forEach(cell => {
            const originalText = cell.textContent;
            if (searchTerm && originalText.toLowerCase().includes(searchTerm)) {
                const regex = new RegExp(`(${searchTerm})`, 'gi');
                const highlighted = originalText.replace(regex, '<span class="search-highlight">$1</span>');
                if (cell.querySelector('code')) {
                    // No modificar celdas con código
                    return;
                }
                cell.innerHTML = highlighted;
            }
        });
    }
    
    /**
     * Filtros dinámicos
     */
    function initializeFilters() {
        const grupoFilter = document.getElementById('grupoFilter');
        const empresaFilter = document.getElementById('empresaFilter');
        
        if (grupoFilter) {
            grupoFilter.addEventListener('change', applyFilters);
        }
        if (empresaFilter) {
            empresaFilter.addEventListener('change', applyFilters);
        }
    }
    
    function applyFilters() {
        const grupoFilter = document.getElementById('grupoFilter').value;
        const empresaFilter = document.getElementById('empresaFilter').value;
        const tableBody = document.getElementById('cuentasTableBody');
        const rows = tableBody.querySelectorAll('tr');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const grupo = row.getAttribute('data-grupo');
            const empresa = row.getAttribute('data-empresa');
            
            const grupoMatch = !grupoFilter || grupo === grupoFilter;
            const empresaMatch = !empresaFilter || empresa === empresaFilter;
            
            if (grupoMatch && empresaMatch) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        updateVisibleCount(visibleCount);
        updateFilterIndicators();
    }
    
    function clearFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('grupoFilter').value = '';
        document.getElementById('empresaFilter').value = '';
        
        const tableBody = document.getElementById('cuentasTableBody');
        const rows = tableBody.querySelectorAll('tr');
        
        rows.forEach(row => {
            row.style.display = '';
        });
        
        updateVisibleCount(rows.length);
        updateFilterIndicators();
    }
    
    function updateFilterIndicators() {
        const grupoFilter = document.getElementById('grupoFilter');
        const empresaFilter = document.getElementById('empresaFilter');
        
        grupoFilter.classList.toggle('filter-active', grupoFilter.value !== '');
        empresaFilter.classList.toggle('filter-active', empresaFilter.value !== '');
    }
    
    /**
     * Ordenamiento de tabla
     */
    function initializeSorting() {
        const headers = document.querySelectorAll('th[onclick]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
        });
    }
    
    function sortTable(columnIndex) {
        const table = document.getElementById('cuentasTable');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        // Determinar dirección de ordenamiento
        if (currentSortColumn === columnIndex) {
            currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            currentSortDirection = 'asc';
            currentSortColumn = columnIndex;
        }
        
        // Ordenar filas
        rows.sort((a, b) => {
            const aVal = a.cells[columnIndex].textContent.trim();
            const bVal = b.cells[columnIndex].textContent.trim();
            
            let comparison = 0;
            if (!isNaN(aVal) && !isNaN(bVal)) {
                comparison = parseFloat(aVal) - parseFloat(bVal);
            } else {
                comparison = aVal.localeCompare(bVal);
            }
            
            return currentSortDirection === 'asc' ? comparison : -comparison;
        });
        
        // Reordenar DOM
        rows.forEach(row => tbody.appendChild(row));
        
        // Actualizar indicadores visuales
        updateSortIndicators(columnIndex);
    }
    
    function updateSortIndicators(sortedColumn) {
        const headers = document.querySelectorAll('th i.fa-sort');
        headers.forEach((icon, index) => {
            icon.className = 'fas fa-sort text-gray-400';
            if (index === sortedColumn) {
                icon.className = currentSortDirection === 'asc' ? 
                    'fas fa-sort-up text-emerald-600' : 
                    'fas fa-sort-down text-emerald-600';
            }
        });
    }
    
    /**
     * Vista en árbol
     */
    function toggleTreeView() {
        const tableView = document.querySelector('.bg-white.shadow-sm.rounded-lg.overflow-hidden');
        const treeView = document.getElementById('treeView');
        
        if (isTreeView) {
            // Mostrar tabla, ocultar árbol
            tableView.classList.remove('hidden');
            treeView.classList.add('hidden');
            isTreeView = false;
            document.querySelector('button[onclick="toggleTreeView()"]').innerHTML = 
                '<i class="fas fa-sitemap mr-2"></i>Vista Árbol';
        } else {
            // Mostrar árbol, ocultar tabla
            tableView.classList.add('hidden');
            treeView.classList.remove('hidden');
            isTreeView = true;
            generateTreeView();
            document.querySelector('button[onclick="toggleTreeView()"]').innerHTML = 
                '<i class="fas fa-table mr-2"></i>Vista Tabla';
        }
    }
    
    function generateTreeView() {
        const treeContainer = document.getElementById('treeContainer');
        const tableRows = document.querySelectorAll('#cuentasTableBody tr');
        
        if (tableRows.length === 0) {
            treeContainer.innerHTML = '<p class="text-gray-500 italic">No hay cuentas para mostrar en vista árbol</p>';
            return;
        }
        
        // Construir estructura de árbol
        const accounts = [];
        tableRows.forEach(row => {
            if (row.style.display !== 'none') {
                const codigo = row.querySelector('code').textContent;
                const descripcion = row.cells[3].textContent;
                const cuentaMadre = row.cells[4].textContent.trim();
                const grupo = row.getAttribute('data-grupo');
                
                accounts.push({
                    codigo,
                    descripcion,
                    cuentaMadre: cuentaMadre === 'Cuenta principal' ? null : cuentaMadre,
                    grupo,
                    nivel: codigo.length
                });
            }
        });
        
        // Generar HTML del árbol
        const treeHtml = buildTreeHtml(accounts);
        treeContainer.innerHTML = treeHtml;
        
        // Agregar funcionalidad de expansión/colapso
        initializeTreeInteractions();
    }
    
    function buildTreeHtml(accounts) {
        const rootAccounts = accounts.filter(acc => !acc.cuentaMadre);
        let html = '<div class="tree-view">';
        
        rootAccounts.forEach(account => {
            html += buildTreeNode(account, accounts, 0);
        });
        
        html += '</div>';
        return html;
    }
    
    function buildTreeNode(account, allAccounts, level) {
        const children = allAccounts.filter(acc => acc.cuentaMadre === account.codigo);
        const hasChildren = children.length > 0;
        const indent = level * 20;
        
        let html = `
            <div class="tree-node" style="margin-left: ${indent}px;">
                <div class="tree-node-content" data-codigo="${account.codigo}">
                    ${hasChildren ? 
                        `<i class="fas fa-chevron-right tree-node-toggle" onclick="toggleTreeNode(this)"></i>` : 
                        `<i class="fas fa-circle text-xs text-gray-400 mr-2"></i>`
                    }
                    <code class="account-code mr-3">${account.codigo}</code>
                    <span class="font-medium">${account.descripcion}</span>
                    <span class="ml-auto text-xs text-gray-500">Grupo ${account.grupo}</span>
                </div>
        `;
        
        if (hasChildren) {
            html += '<div class="tree-children" style="display: none;">';
            children.forEach(child => {
                html += buildTreeNode(child, allAccounts, level + 1);
            });
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    }
    
    function toggleTreeNode(toggleIcon) {
        const treeNode = toggleIcon.closest('.tree-node');
        const children = treeNode.querySelector('.tree-children');
        
        if (children) {
            const isExpanded = children.style.display !== 'none';
            children.style.display = isExpanded ? 'none' : 'block';
            toggleIcon.classList.toggle('expanded', !isExpanded);
        }
    }
    
    function initializeTreeInteractions() {
        const treeNodes = document.querySelectorAll('.tree-node-content');
        treeNodes.forEach(node => {
            node.addEventListener('click', function(e) {
                if (!e.target.classList.contains('tree-node-toggle')) {
                    const codigo = this.getAttribute('data-codigo');
                    showAccountDetails(codigo);
                }
            });
        });
    }
    
    /**
     * Exportar funcionalidades
     */
    function exportToExcel() {
        const table = document.getElementById('cuentasTable');
        const visibleRows = Array.from(table.querySelectorAll('tbody tr')).filter(
            row => row.style.display !== 'none'
        );
        
        if (visibleRows.length === 0) {
            showNotification('No hay datos para exportar', 'warning');
            return;
        }
        
        // Crear CSV
        let csv = 'Empresa,Grupo,Código,Descripción,Cuenta Madre,Nivel\n';
        
        visibleRows.forEach(row => {
            const cells = row.cells;
            const empresa = cells[0].textContent.trim();
            const grupo = cells[1].textContent.trim();
            const codigo = cells[2].textContent.trim();
            const descripcion = cells[3].textContent.trim().replace(/,/g, ';');
            const cuentaMadre = cells[4].textContent.trim();
            const nivel = cells[5].textContent.trim();
            
            csv += `"${empresa}","${grupo}","${codigo}","${descripcion}","${cuentaMadre}","${nivel}"\n`;
        });
        
        // Descargar archivo
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `plan_cuentas_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        
        showNotification('Plan de cuentas exportado exitosamente', 'success');
    }
    
    function printTable() {
        const printWindow = window.open('', '_blank');
        const table = document.getElementById('cuentasTable').outerHTML;
        
        printWindow.document.write(`
            <html>
                <head>
                    <title>Plan de Cuentas</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        table { width: 100%; border-collapse: collapse; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background-color: #f5f5f5; font-weight: bold; }
                        .no-print { display: none; }
                        h1 { color: #333; margin-bottom: 20px; }
                    </style>
                </head>
                <body>
                    <h1>Plan de Cuentas - ${new Date().toLocaleDateString()}</h1>
                    ${table}
                </body>
            </html>
        `);
        
        printWindow.document.close();
        printWindow.print();
    }
    
    /**
     * Atajos de teclado
     */
    function initializeKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl + F para enfocar búsqueda
            if (e.ctrlKey && e.key === 'f') {
                e.preventDefault();
                document.getElementById('searchInput').focus();
            }
            
            // Ctrl + N para nueva cuenta
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                const newButton = document.querySelector('a[href*="create"]');
                if (newButton) newButton.click();
            }
            
            // Ctrl + T para alternar vista
            if (e.ctrlKey && e.key === 't') {
                e.preventDefault();
                toggleTreeView();
            }
            
            // Escape para limpiar filtros
            if (e.key === 'Escape') {
                clearFilters();
            }
        });
    }
    
    /**
     * Tooltips
     */
    function initializeTooltips() {
        const tooltipElements = document.querySelectorAll('[title]');
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', showTooltip);
            element.addEventListener('mouseleave', hideTooltip);
        });
    }
    
    function showTooltip(e) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip absolute bg-gray-800 text-white px-2 py-1 rounded text-sm z-50';
        tooltip.textContent = e.target.getAttribute('title');
        tooltip.style.top = e.target.offsetTop - 30 + 'px';
        tooltip.style.left = e.target.offsetLeft + 'px';
        document.body.appendChild(tooltip);
        e.target.removeAttribute('title');
        e.target.setAttribute('data-original-title', tooltip.textContent);
    }
    
    function hideTooltip(e) {
        const tooltip = document.querySelector('.tooltip');
        if (tooltip) {
            tooltip.remove();
        }
        if (e.target.getAttribute('data-original-title')) {
            e.target.setAttribute('title', e.target.getAttribute('data-original-title'));
            e.target.removeAttribute('data-original-title');
        }
    }
    
    /**
     * Utilidades
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    function updateVisibleCount(count) {
        const countElement = document.getElementById('totalCuentas');
        if (countElement) {
            countElement.textContent = count;
        }
    }
    
    function saveOriginalTableData() {
        const rows = document.querySelectorAll('#cuentasTableBody tr');
        rows.forEach(row => {
            originalTableData.push({
                element: row,
                innerHTML: row.innerHTML
            });
        });
    }
    
    function showAccountDetails(codigo) {
        // Esta función se puede expandir para mostrar detalles en un modal
        console.log('Mostrar detalles de cuenta:', codigo);
    }
    
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' :
            type === 'error' ? 'bg-red-100 text-red-800 border border-red-200' :
            type === 'warning' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
            'bg-blue-100 text-blue-800 border border-blue-200'
        }`;
        
        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-${
                    type === 'success' ? 'check-circle' : 
                    type === 'error' ? 'exclamation-circle' : 
                    type === 'warning' ? 'exclamation-triangle' :
                    'info-circle'
                }"></i>
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
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 500);
        }, 5000);
    }
    
    /**
     * Funcionalidad para formularios de cuenta
     */
    function initializeCuentaForm() {
        const planCuentasSelect = document.getElementById('id_plan_cuentas');
        const cuentaMadreSelect = document.getElementById('id_cuenta_madre');
        
        if (planCuentasSelect && cuentaMadreSelect) {
            planCuentasSelect.addEventListener('change', function() {
                updateCuentaMadreOptions(this.value);
            });
            
            // Cargar opciones iniciales si hay un plan seleccionado
            if (planCuentasSelect.value) {
                updateCuentaMadreOptions(planCuentasSelect.value);
            }
        }
    }
    
    function updateCuentaMadreOptions(planId) {
        const cuentaMadreSelect = document.getElementById('id_cuenta_madre');
        const cuentaActualId = document.querySelector('input[name="cuenta_id"]')?.value;
        
        if (!cuentaMadreSelect) return;
        
        // Limpiar opciones existentes
        cuentaMadreSelect.innerHTML = '<option value="">Seleccione una cuenta madre (opcional)</option>';
        
        if (!planId) return;
        
        // Mostrar loading
        cuentaMadreSelect.innerHTML = '<option value="">Cargando...</option>';
        cuentaMadreSelect.disabled = true;
        
        // Construir URL con parámetros
        let url = `/plan-cuentas/ajax/cuentas-madre/?plan_id=${planId}`;
        if (cuentaActualId) {
            url += `&cuenta_id=${cuentaActualId}`;
        }
        
        // Hacer petición AJAX
        fetch(url)
            .then(response => response.json())
            .then(data => {
                // Restaurar estado
                cuentaMadreSelect.disabled = false;
                cuentaMadreSelect.innerHTML = '<option value="">Seleccione una cuenta madre (opcional)</option>';
                
                if (data.cuentas) {
                    data.cuentas.forEach(cuenta => {
                        const option = document.createElement('option');
                        option.value = cuenta.id;
                        option.textContent = `${cuenta.cuenta} - ${cuenta.descripcion}`;
                        cuentaMadreSelect.appendChild(option);
                    });
                } else if (data.error) {
                    console.error('Error cargando cuentas madre:', data.error);
                    showNotification('Error al cargar las cuentas madre', 'error');
                }
            })
            .catch(error => {
                console.error('Error en la petición AJAX:', error);
                cuentaMadreSelect.disabled = false;
                cuentaMadreSelect.innerHTML = '<option value="">Error al cargar opciones</option>';
                showNotification('Error de conexión al cargar las cuentas madre', 'error');
            });
    }
    
    // Inicializar formulario de cuenta cuando se carga la página
    initializeCuentaForm();
    
    // Exponer funciones globales necesarias
    window.toggleTreeView = toggleTreeView;
    window.sortTable = sortTable;
    window.clearFilters = clearFilters;
    window.exportToExcel = exportToExcel;
    window.printTable = printTable;
    window.toggleTreeNode = toggleTreeNode;
    window.updateCuentaMadreOptions = updateCuentaMadreOptions;
    
    console.log('Plan de Cuentas JavaScript cargado exitosamente');
});
