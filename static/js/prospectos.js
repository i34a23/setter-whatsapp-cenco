// Prospectos Module JavaScript - Version 4.0 FIXED

// ========================================
// ESTADO GLOBAL
// ========================================
let uploadedFile = null;
let previewData = null;
let suggestedMapping = null;

// Paginación
let currentPage = 1;
let pageSize = 50;
let totalRecords = 0;

// Selección múltiple
let selectedIds = new Set();
let selectMode = false;

// Filtros estilo Excel
let activeFilters = {};
let currentFilterColumn = null;
let allColumnValues = {};

// Ordenamiento
let sortColumn = 'fecha_creacion';
let sortOrder = 'DESC';

// ========================================
// CARGA DE DATOS
// ========================================

async function loadProspectos() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            sort_column: sortColumn,
            sort_order: sortOrder
        });
        
        for (const [column, values] of Object.entries(activeFilters)) {
            params.append(column, JSON.stringify(values));
        }
        
        const response = await fetch(`/prospectos/api/list?${params}`);
        const data = await response.json();
        
        if (data.success) {
            if (data.message) {
                console.log(data.message);
            }
            
            if (data.data.length > 0 || data.total > 0) {
                const emptyState = document.getElementById('emptyState');
                const prospectosTable = document.getElementById('prospectosTable');
                const statsGrid = document.getElementById('statsGrid');
                
                if (emptyState) emptyState.style.display = 'none';
                if (prospectosTable) prospectosTable.style.display = 'block';
                if (statsGrid) statsGrid.style.display = 'grid';
                
                renderProspectosTable(data.data);
                updatePagination(data.total, data.page, data.total_pages);
                updateFilterIndicators();
                updateSortIndicators();
            } else {
                const emptyState = document.getElementById('emptyState');
                const prospectosTable = document.getElementById('prospectosTable');
                
                if (emptyState) emptyState.style.display = 'flex';
                if (prospectosTable) prospectosTable.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error loading prospectos:', error);
    }
}

async function loadStats() {
    try {
        const response = await fetch('/prospectos/api/stats');
        const data = await response.json();
        
        if (data.success) {
            const totalElement = document.getElementById('totalProspectos');
            if (totalElement) {
                totalElement.textContent = data.stats.total;
            }
            
            if (data.stats.total > 0) {
                const statsGrid = document.getElementById('statsGrid');
                if (statsGrid) statsGrid.style.display = 'grid';
            }
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ========================================
// RENDER TABLA
// ========================================

function renderProspectosTable(prospectos) {
    const tbody = document.getElementById('prospectosTableBody');
    
    if (!tbody) {
        console.error('Elemento prospectosTableBody no encontrado');
        return;
    }
    
    tbody.innerHTML = '';
    
    prospectos.forEach(prospecto => {
        const tr = document.createElement('tr');
        const isSelected = selectedIds.has(prospecto.id);
        
        tr.innerHTML = `
            <td style="width: 50px; text-align: center;">
                <input type="checkbox" 
                       class="row-checkbox" 
                       data-id="${prospecto.id}"
                       ${isSelected ? 'checked' : ''}
                       ${!selectMode ? 'style="display: none;"' : ''}
                       onchange="toggleSelect(this)">
            </td>
            <td style="min-width: 120px;" title="${prospecto.nombre || ''}">${prospecto.nombre || '-'}</td>
            <td style="min-width: 120px;" title="${prospecto.apellidos || ''}">${prospecto.apellidos || '-'}</td>
            <td style="min-width: 200px;" title="${prospecto.email_1 || ''}">${prospecto.email_1 || '-'}</td>
            <td style="min-width: 130px;">${prospecto.telefono_1 || '-'}</td>
            <td style="min-width: 150px;" title="${prospecto.programa || ''}">${prospecto.programa || '-'}</td>
            <td style="min-width: 120px;">${prospecto.propietario || '-'}</td>
            <td style="min-width: 100px;">${prospecto.fecha_creacion ? new Date(prospecto.fecha_creacion).toLocaleDateString() : '-'}</td>
        `;
        tbody.appendChild(tr);
    });
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    updateSelectedCount();
}

// ========================================
// PAGINACIÓN
// ========================================

function updatePagination(total, page, totalPages) {
    totalRecords = total;
    currentPage = page;
    
    const elements = {
        currentPage: document.getElementById('currentPage'),
        totalPages: document.getElementById('totalPages'),
        showingCount: document.getElementById('showingCount'),
        totalCount: document.getElementById('totalCount'),
        btnPrev: document.getElementById('btnPrev'),
        btnNext: document.getElementById('btnNext')
    };
    
    if (elements.currentPage) elements.currentPage.textContent = page;
    if (elements.totalPages) elements.totalPages.textContent = totalPages;
    if (elements.showingCount) elements.showingCount.textContent = Math.min(page * pageSize, total);
    if (elements.totalCount) elements.totalCount.textContent = total;
    if (elements.btnPrev) elements.btnPrev.disabled = page <= 1;
    if (elements.btnNext) elements.btnNext.disabled = page >= totalPages;
}

function nextPage() {
    currentPage++;
    loadProspectos();
}

function previousPage() {
    currentPage--;
    loadProspectos();
}

// ========================================
// ORDENAMIENTO
// ========================================

function sortBy(column) {
    if (sortColumn === column) {
        sortOrder = sortOrder === 'ASC' ? 'DESC' : 'ASC';
    } else {
        sortColumn = column;
        sortOrder = 'DESC';
    }
    
    currentPage = 1;
    loadProspectos();
}

function updateSortIndicators() {
    document.querySelectorAll('.sort-indicator').forEach(indicator => {
        indicator.innerHTML = '<i data-feather="chevrons-up-down"></i>';
        indicator.classList.remove('active', 'asc', 'desc');
    });
    
    const activeIndicator = document.querySelector(`[data-sort="${sortColumn}"]`);
    if (activeIndicator) {
        activeIndicator.classList.add('active');
        activeIndicator.classList.add(sortOrder.toLowerCase());
        
        if (sortOrder === 'ASC') {
            activeIndicator.innerHTML = '<i data-feather="chevron-up"></i>';
        } else {
            activeIndicator.innerHTML = '<i data-feather="chevron-down"></i>';
        }
    }
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

// ========================================
// SELECCIÓN MÚLTIPLE
// ========================================

function toggleSelectMode() {
    selectMode = !selectMode;
    const btn = document.getElementById('btnToggleSelect');
    const selectAll = document.getElementById('selectAll');
    const checkboxes = document.querySelectorAll('.row-checkbox');
    
    if (!btn || !selectAll) {
        console.error('Elementos de selección no encontrados');
        return;
    }
    
    if (selectMode) {
        btn.classList.add('active');
        selectAll.style.display = 'block';
        checkboxes.forEach(cb => cb.style.display = 'block');
    } else {
        btn.classList.remove('active');
        selectAll.style.display = 'none';
        selectAll.checked = false;
        checkboxes.forEach(cb => {
            cb.style.display = 'none';
            cb.checked = false;
        });
        selectedIds.clear();
        updateSelectedCount();
    }
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

function toggleSelect(checkbox) {
    const id = parseInt(checkbox.dataset.id);
    if (checkbox.checked) {
        selectedIds.add(id);
    } else {
        selectedIds.delete(id);
    }
    updateSelectedCount();
}

function toggleSelectAll() {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    const selectAll = document.getElementById('selectAll');
    
    if (!selectAll) return;
    
    const isChecked = selectAll.checked;
    
    checkboxes.forEach(cb => {
        cb.checked = isChecked;
        const id = parseInt(cb.dataset.id);
        if (isChecked) {
            selectedIds.add(id);
        } else {
            selectedIds.delete(id);
        }
    });
    
    updateSelectedCount();
}

function updateSelectedCount() {
    const count = selectedIds.size;
    const selectedCountElement = document.getElementById('selectedCount');
    const btnActivar = document.getElementById('btnActivar');
    
    if (selectedCountElement) {
        selectedCountElement.textContent = count;
    }
    
    if (btnActivar) {
        btnActivar.disabled = count === 0;
    }
}

// ========================================
// ACTIVAR PROSPECTOS
// ========================================

async function activarSeleccionados() {
    if (selectedIds.size === 0) return;
    
    if (!confirm(`¿Activar ${selectedIds.size} prospectos y pasarlos a la tabla LEADS?`)) return;
    
    const btn = document.getElementById('btnActivar');
    if (!btn) return;
    
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `
        <svg class="spinner" width="16" height="16" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle class="spinner-circle" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
        </svg>
        Activando...
    `;
    
    try {
        const response = await fetch('/prospectos/api/activar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids: Array.from(selectedIds) })
        });
        
        const data = await response.json();
        
        if (data.success) {
            let message = data.message || `${data.activated} prospectos activados exitosamente`;
            
            if (data.warnings && data.warnings.length > 0) {
                message += '\n\nAdvertencias:\n' + data.warnings.join('\n');
            }
            
            alert(`✅ ${message}`);
            
            selectedIds.clear();
            if (selectMode) {
                toggleSelectMode();
            }
            loadProspectos();
            loadStats();
        } else {
            throw new Error(data.error || 'Error desconocido');
        }
    } catch (error) {
        alert('❌ Error: ' + error.message);
        console.error('Error:', error);
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

// ========================================
// FILTROS TIPO EXCEL
// ========================================

async function openFilterDropdown(column, event) {
    event.stopPropagation();
    
    const dropdown = document.getElementById('filterDropdown');
    const button = event.currentTarget;
    
    if (!dropdown) return;
    
    if (dropdown.style.display === 'block' && currentFilterColumn === column) {
        closeFilterDropdown();
        return;
    }
    
    currentFilterColumn = column;
    
    const rect = button.getBoundingClientRect();
    dropdown.style.top = `${rect.bottom + 5}px`;
    dropdown.style.left = `${rect.left - 120}px`;
    dropdown.style.display = 'block';
    
    await loadColumnValues(column);
    
    const filterSearch = document.getElementById('filterSearch');
    if (filterSearch) {
        filterSearch.value = '';
        filterSearch.focus();
    }
}

async function loadColumnValues(column) {
    try {
        const response = await fetch(`/prospectos/api/column-values?column=${column}`);
        const data = await response.json();
        
        if (data.success) {
            allColumnValues[column] = data.values;
            renderFilterOptions(data.values, column);
        }
    } catch (error) {
        console.error('Error loading column values:', error);
    }
}

function renderFilterOptions(values, column) {
    const container = document.getElementById('filterOptionsList');
    if (!container) return;
    
    const currentFilters = activeFilters[column] || [];
    container.innerHTML = '';
    
    const sortedValues = values.sort((a, b) => {
        if (a === null) return 1;
        if (b === null) return -1;
        return String(a).localeCompare(String(b));
    });
    
    sortedValues.forEach(value => {
        const displayValue = value === null ? '(Vacío)' : value;
        const isChecked = currentFilters.length === 0 || currentFilters.includes(value);
        
        const label = document.createElement('label');
        label.className = 'filter-option';
        label.innerHTML = `
            <input type="checkbox" value="${value}" ${isChecked ? 'checked' : ''}>
            <span>${displayValue}</span>
        `;
        container.appendChild(label);
    });
    
    updateSelectAllCheckbox();
}

function toggleFilterAll() {
    const checkAll = document.querySelector('.filter-checkbox-all');
    if (!checkAll) return;
    
    const isChecked = checkAll.checked;
    const checkboxes = document.querySelectorAll('.filter-options-list input[type="checkbox"]');
    
    checkboxes.forEach(cb => {
        if (cb.parentElement.style.display !== 'none') {
            cb.checked = isChecked;
        }
    });
}

function updateSelectAllCheckbox() {
    const checkboxes = document.querySelectorAll('.filter-options-list input[type="checkbox"]');
    const visibleCheckboxes = Array.from(checkboxes).filter(cb => 
        cb.parentElement.style.display !== 'none'
    );
    const checkedCount = visibleCheckboxes.filter(cb => cb.checked).length;
    
    const checkAll = document.querySelector('.filter-checkbox-all');
    if (checkAll) {
        checkAll.checked = checkedCount === visibleCheckboxes.length;
        checkAll.indeterminate = checkedCount > 0 && checkedCount < visibleCheckboxes.length;
    }
}

function applyColumnFilter() {
    const checkboxes = document.querySelectorAll('.filter-options-list input[type="checkbox"]');
    const selectedValues = [];
    
    checkboxes.forEach(cb => {
        if (cb.checked) {
            const value = cb.value === 'null' ? null : cb.value;
            selectedValues.push(value);
        }
    });
    
    if (selectedValues.length === 0 || selectedValues.length === checkboxes.length) {
        delete activeFilters[currentFilterColumn];
    } else {
        activeFilters[currentFilterColumn] = selectedValues;
    }
    
    closeFilterDropdown();
    currentPage = 1;
    loadProspectos();
    updateFilterIndicators();
}

function clearColumnFilter() {
    delete activeFilters[currentFilterColumn];
    closeFilterDropdown();
    currentPage = 1;
    loadProspectos();
    updateFilterIndicators();
}

function closeFilterDropdown() {
    const dropdown = document.getElementById('filterDropdown');
    if (dropdown) {
        dropdown.style.display = 'none';
    }
    currentFilterColumn = null;
}

function updateFilterIndicators() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    Object.keys(activeFilters).forEach(column => {
        const buttons = document.querySelectorAll('.filter-btn');
        buttons.forEach(btn => {
            const onclick = btn.getAttribute('onclick');
            if (onclick && onclick.includes(`'${column}'`)) {
                btn.classList.add('active');
            }
        });
    });
}

// ========================================
// REFRESH
// ========================================

function refreshProspectos() {
    loadProspectos();
    loadStats();
}

// ========================================
// MODAL DE CARGA
// ========================================

function openUploadModal() {
    const modal = document.getElementById('uploadModal');
    if (modal) {
        modal.classList.add('active');
        resetUploadModal();
    }
}

function closeUploadModal() {
    const modal = document.getElementById('uploadModal');
    if (modal) {
        modal.classList.remove('active');
        resetUploadModal();
        refreshProspectos();
    }
}

function resetUploadModal() {
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    const step3 = document.getElementById('step3');
    const uploadProgress = document.getElementById('uploadProgress');
    const fileInput = document.getElementById('fileInput');
    
    if (step1) step1.style.display = 'block';
    if (step2) step2.style.display = 'none';
    if (step3) step3.style.display = 'none';
    if (uploadProgress) uploadProgress.style.display = 'none';
    if (fileInput) fileInput.value = '';
    
    uploadedFile = null;
    previewData = null;
    suggestedMapping = null;
}

function backToStep1() {
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    
    if (step2) step2.style.display = 'none';
    if (step1) step1.style.display = 'block';
}

// ========================================
// FILE UPLOAD
// ========================================

async function handleFileUpload(file) {
    uploadedFile = file;
    
    const uploadZone = document.getElementById('uploadZone');
    const uploadProgress = document.getElementById('uploadProgress');
    
    if (uploadZone) uploadZone.style.display = 'none';
    if (uploadProgress) uploadProgress.style.display = 'block';
    
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    if (progressFill) progressFill.style.width = '30%';
    if (progressText) progressText.textContent = 'Subiendo archivo...';
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        if (progressFill) progressFill.style.width = '60%';
        if (progressText) progressText.textContent = 'Analizando columnas...';
        
        const response = await fetch('/prospectos/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (progressFill) progressFill.style.width = '100%';
            if (progressText) progressText.textContent = 'Archivo procesado correctamente';
            
            previewData = data.preview;
            suggestedMapping = data.suggested_mapping;
            
            setTimeout(() => {
                showMappingStep(data);
            }, 500);
        } else {
            throw new Error(data.error || 'Error al procesar archivo');
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('Error: ' + error.message);
        resetUploadModal();
    }
}

function showMappingStep(data) {
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    
    if (step1) step1.style.display = 'none';
    if (step2) step2.style.display = 'block';
    
    const previewFilename = document.getElementById('previewFilename');
    const previewRows = document.getElementById('previewRows');
    
    if (previewFilename) previewFilename.textContent = data.filename;
    if (previewRows) previewRows.textContent = `${data.preview.total_rows} filas detectadas`;
    
    const container = document.getElementById('mappingContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    const targetFields = {
        'nombre': 'Nombre',
        'apellidos': 'Apellidos',
        'fecha_creacion': 'Fecha Creación',
        'propietario': 'Propietario',
        'canal': 'Canal',
        'referrer': 'Referrer',
        'email_1': 'Email 1',
        'email_2': 'Email 2',
        'telefono_1': 'Teléfono 1',
        'telefono_2': 'Teléfono 2',
        'programa': 'Programa',
        'rut': 'RUT',
        'carrera_postula': 'Carrera que Postula',
        'experiencia': 'Experiencia',
        'urgencia': 'Urgencia'
    };
    
    for (const [field, label] of Object.entries(targetFields)) {
        const row = document.createElement('div');
        row.className = 'mapping-row';
        
        const sourceColumn = data.suggested_mapping[field] || '';
        
        row.innerHTML = `
            <div class="mapping-field">
                <label>Campo del Sistema</label>
                <input type="text" value="${label}" readonly>
            </div>
            <div class="mapping-arrow">
                <i data-feather="arrow-right"></i>
            </div>
            <div class="mapping-field">
                <label>Columna del Archivo</label>
                <select class="column-select" data-field="${field}">
                    <option value="">-- No mapear --</option>
                    ${data.preview.columns.map(col => 
                        `<option value="${col}" ${col === sourceColumn ? 'selected' : ''}>${col}</option>`
                    ).join('')}
                </select>
            </div>
        `;
        
        container.appendChild(row);
    }
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

async function importData() {
    const mapping = {};
    document.querySelectorAll('.column-select').forEach(select => {
        const field = select.dataset.field;
        const column = select.value;
        if (column) {
            mapping[field] = column;
        }
    });
    
    if (Object.keys(mapping).length === 0) {
        alert('Debes mapear al menos una columna');
        return;
    }
    
    const btn = document.getElementById('btnImport');
    if (!btn) return;
    
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `
        <svg class="spinner" width="16" height="16" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle class="spinner-circle" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
        </svg>
        Importando...
    `;
    
    try {
        const response = await fetch('/prospectos/api/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mapping })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccessStep(data);
        } else {
            throw new Error(data.error || 'Error al importar datos');
        }
    } catch (error) {
        console.error('Import error:', error);
        alert('Error: ' + error.message);
        btn.disabled = false;
        btn.innerHTML = originalHTML;
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

function showSuccessStep(data) {
    const step2 = document.getElementById('step2');
    const step3 = document.getElementById('step3');
    
    if (step2) step2.style.display = 'none';
    if (step3) step3.style.display = 'block';
    
    const successMessage = document.getElementById('successMessage');
    if (successMessage) {
        successMessage.textContent = `Se importaron ${data.imported_count} registros exitosamente`;
    }
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

// ========================================
// EVENT LISTENERS
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.style.display = 'none';
    }
    
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadZone && fileInput) {
        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });
        
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = 'var(--color-primary)';
            uploadZone.style.backgroundColor = 'var(--color-primary-light)';
        });
        
        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = 'var(--color-border-tertiary)';
            uploadZone.style.backgroundColor = 'transparent';
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = 'var(--color-border-tertiary)';
            uploadZone.style.backgroundColor = 'transparent';
            
            if (e.dataTransfer.files.length > 0) {
                handleFileUpload(e.dataTransfer.files[0]);
            }
        });
    }
    
    const filterSearch = document.getElementById('filterSearch');
    if (filterSearch) {
        filterSearch.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const options = document.querySelectorAll('.filter-options-list .filter-option');
            
            options.forEach(option => {
                const text = option.textContent.toLowerCase();
                option.style.display = text.includes(searchTerm) ? 'flex' : 'none';
            });
        });
    }
    
    document.addEventListener('click', (e) => {
        const dropdown = document.getElementById('filterDropdown');
        if (dropdown && dropdown.style.display === 'block' && 
            !dropdown.contains(e.target) && 
            !e.target.closest('.filter-btn')) {
            closeFilterDropdown();
        }
    });
});

// ========================================
// FORMULARIO MANUAL
// ========================================

function openManualModal() {
    const modal = document.getElementById('manualModal');
    if (modal) {
        modal.classList.add('active');
        document.getElementById('manualForm').reset();
        feather.replace();
    }
}

function closeManualModal() {
    const modal = document.getElementById('manualModal');
    if (modal) {
        modal.classList.remove('active');
        document.getElementById('manualForm').reset();
    }
}

// Manejar envío del formulario
document.addEventListener('DOMContentLoaded', function() {
    const manualForm = document.getElementById('manualForm');
    if (manualForm) {
        manualForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const btnSave = document.getElementById('btnSaveManual');
            const originalText = btnSave.innerHTML;
            btnSave.disabled = true;
            btnSave.innerHTML = '<i data-feather="loader" class="spinner"></i> Guardando...';
            feather.replace();
            
            try {
                // Recopilar datos del formulario
                const formData = new FormData(manualForm);
                const data = {};
                
                for (let [key, value] of formData.entries()) {
                    if (value.trim() !== '') {
                        data[key] = value.trim();
                    }
                }
                
                // Validar campos requeridos
                if (!data.nombre || !data.apellidos) {
                    alert('Por favor completa los campos obligatorios: Nombre y Apellidos');
                    btnSave.disabled = false;
                    btnSave.innerHTML = originalText;
                    feather.replace();
                    return;
                }
                
                // Enviar al backend
                const response = await fetch('/prospectos/api/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('✅ Prospecto creado exitosamente');
                    closeManualModal();
                    loadProspectos();
                    loadStats();
                } else {
                    alert('❌ Error: ' + result.error);
                }
                
            } catch (error) {
                console.error('Error al crear prospecto:', error);
                alert('❌ Error al crear prospecto: ' + error.message);
            } finally {
                btnSave.disabled = false;
                btnSave.innerHTML = originalText;
                feather.replace();
            }
        });
    }
});