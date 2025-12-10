// Prospectos Activos - JavaScript Completo

let prospectos = [];
let filteredProspectos = [];
let selectedIds = new Set();
let currentPage = 1;
let pageSize = 50;
let totalPages = 1;
let selectMode = false;
let sortColumn = 'dias_transcurridos';
let sortOrder = 'DESC';
let chatModal = null;

// Filtros activos
let activeFilters = {
    estado: null,
    carrera: [],
    plan: []
};

// Opciones de filtro disponibles
let filterOptions = {
    carreras: [],
    planes: [],
    estados: []
};

// Estado del dropdown de filtros
let currentFilterType = null;
let currentFilterButton = null;

// Inicializar modal de Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    const chatModalElement = document.getElementById('chatModal');
    if (chatModalElement) {
        chatModal = new bootstrap.Modal(chatModalElement, {
            backdrop: true,
            keyboard: true,
            focus: true
        });
        
        // Limpiar cuando se cierra el modal
        chatModalElement.addEventListener('hidden.bs.modal', function () {
            document.getElementById('chatLoading').style.display = 'flex';
            document.getElementById('chatMessages').style.display = 'none';
            document.getElementById('chatEmpty').style.display = 'none';
            document.getElementById('chatMessages').innerHTML = '';
            document.getElementById('prospectoInfo').innerHTML = '<div class="info-loading" id="infoLoading"><div class="spinner-border text-primary spinner-border-sm" role="status"></div></div>';
        });
    }
    
    // Cerrar dropdown de filtros al hacer click fuera
    document.addEventListener('click', function(e) {
        const dropdown = document.getElementById('filterDropdown');
        if (dropdown && dropdown.classList.contains('show')) {
            if (!dropdown.contains(e.target) && !e.target.closest('.filter-indicator')) {
                closeFilterDropdown();
            }
        }
    });
    
    // Cargar opciones de filtros
    loadFilterOptions();
});

// ====================================
// TARJETAS DE ESTADÍSTICAS
// ====================================

async function loadStats() {
    try {
        const response = await fetch('/prospectos_activos/api/stats');
        const result = await response.json();
        
        if (result.success) {
            renderStatsCards(result.stats);
        }
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

function renderStatsCards(stats) {
    const container = document.getElementById('statsCardsContainer');
    
    if (!stats.por_estado || stats.por_estado.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6c757d;">No hay estadísticas disponibles</p>';
        return;
    }
    
    // Mapeo de iconos por estado
    const iconos = {
        'nuevo': 'user-plus',
        'calificando': 'clipboard',
        'persuadiendo': 'target',
        'listo_matricula': 'check-circle',
        'perdido': 'x-circle',
        'en_proceso': 'activity'
    };
    
    container.innerHTML = stats.por_estado.map(stat => `
        <div class="stats-card ${activeFilters.estado === stat.estado ? 'active' : ''}" 
             onclick="filterByEstado('${stat.estado}')"
             data-estado="${stat.estado}">
            <div class="stats-card-header">
                <div class="stats-card-title">${stat.nombre}</div>
                <div class="stats-card-icon ${stat.color}">
                    <i data-feather="${iconos[stat.estado] || 'circle'}"></i>
                </div>
            </div>
            <div class="stats-card-body">
                <div class="stats-card-value">${stat.count}</div>
                <div class="stats-card-label">Prospectos</div>
            </div>
        </div>
    `).join('');
    
    feather.replace();
}

function filterByEstado(estado) {
    // Toggle: si ya está activo, desactivar
    if (activeFilters.estado === estado) {
        activeFilters.estado = null;
    } else {
        activeFilters.estado = estado;
    }
    
    // Actualizar visualización de tarjetas
    document.querySelectorAll('.stats-card').forEach(card => {
        card.classList.toggle('active', card.dataset.estado === activeFilters.estado);
    });
    
    // Recargar datos con filtro
    currentPage = 1;
    loadProspectos();
}

// ====================================
// FILTROS TIPO EXCEL
// ====================================

async function loadFilterOptions() {
    try {
        const response = await fetch('/prospectos_activos/api/filter-options');
        const result = await response.json();
        
        if (result.success) {
            filterOptions = result.options;
        }
    } catch (error) {
        console.error('Error cargando opciones de filtros:', error);
    }
}

function toggleFilter(filterType) {
    const button = event.currentTarget;
    const dropdown = document.getElementById('filterDropdown');
    
    // Si ya está abierto el mismo filtro, cerrarlo
    if (dropdown.classList.contains('show') && currentFilterType === filterType) {
        closeFilterDropdown();
        return;
    }
    
    currentFilterType = filterType;
    currentFilterButton = button;
    
    // Obtener opciones según el tipo de filtro
    let options = [];
    let selectedValues = [];
    
    switch(filterType) {
        case 'carrera':
            options = filterOptions.carreras;
            selectedValues = activeFilters.carrera;
            break;
        case 'plan':
            options = filterOptions.planes;
            selectedValues = activeFilters.plan;
            break;
        case 'estado':
            options = filterOptions.estados;
            selectedValues = activeFilters.estado ? [activeFilters.estado] : [];
            break;
    }
    
    // Renderizar opciones
    const dropdownBody = document.getElementById('filterDropdownBody');
    dropdownBody.innerHTML = options.map(option => `
        <div class="filter-option">
            <input type="checkbox" 
                   id="filter_${filterType}_${option}" 
                   value="${option}"
                   ${selectedValues.includes(option) ? 'checked' : ''}>
            <label class="filter-option-label" for="filter_${filterType}_${option}">
                ${option}
            </label>
        </div>
    `).join('');
    
    // Posicionar dropdown
    const rect = button.getBoundingClientRect();
    dropdown.style.top = (rect.bottom + 5) + 'px';
    dropdown.style.left = rect.left + 'px';
    dropdown.classList.add('show');
    
    // Focus en el buscador
    const searchInput = document.getElementById('filterSearch');
    searchInput.value = '';
    searchInput.focus();
    
    // Event listener para búsqueda
    searchInput.oninput = function() {
        filterDropdownOptions(this.value);
    };
}

function filterDropdownOptions(searchTerm) {
    const options = document.querySelectorAll('.filter-option');
    const term = searchTerm.toLowerCase();
    
    options.forEach(option => {
        const label = option.querySelector('.filter-option-label').textContent.toLowerCase();
        option.style.display = label.includes(term) ? 'flex' : 'none';
    });
}

function closeFilterDropdown() {
    const dropdown = document.getElementById('filterDropdown');
    dropdown.classList.remove('show');
    currentFilterType = null;
    currentFilterButton = null;
}

function applyFilter() {
    if (!currentFilterType) return;
    
    // Obtener valores seleccionados
    const checkboxes = document.querySelectorAll(`#filterDropdownBody input[type="checkbox"]:checked`);
    const selectedValues = Array.from(checkboxes).map(cb => cb.value);
    
    // Actualizar filtros activos
    if (currentFilterType === 'estado') {
        activeFilters.estado = selectedValues.length > 0 ? selectedValues[0] : null;
    } else {
        activeFilters[currentFilterType] = selectedValues;
    }
    
    // Actualizar indicador visual del botón
    if (currentFilterButton) {
        if (selectedValues.length > 0) {
            currentFilterButton.classList.add('active');
        } else {
            currentFilterButton.classList.remove('active');
        }
    }
    
    // Cerrar dropdown
    closeFilterDropdown();
    
    // Recargar datos
    currentPage = 1;
    loadProspectos();
}

function clearAllFilters() {
    // Limpiar filtros
    activeFilters = {
        estado: null,
        carrera: [],
        plan: []
    };
    
    // Limpiar indicadores visuales
    document.querySelectorAll('.filter-indicator').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.querySelectorAll('.stats-card').forEach(card => {
        card.classList.remove('active');
    });
    
    // Recargar datos
    currentPage = 1;
    loadProspectos();
}

// ====================================
// CARGAR PROSPECTOS
// ====================================

async function loadProspectos() {
    try {
        const searchTerm = document.getElementById('searchInput')?.value || '';
        
        // Construir parámetros de URL con filtros
        let url = `/prospectos_activos/api/list?page=${currentPage}&page_size=${pageSize}&search=${encodeURIComponent(searchTerm)}&sort_by=${sortColumn}&sort_order=${sortOrder}`;
        
        // Agregar filtros
        if (activeFilters.estado) {
            url += `&estado=${encodeURIComponent(activeFilters.estado)}`;
        }
        if (activeFilters.carrera.length > 0) {
            url += `&carrera=${encodeURIComponent(activeFilters.carrera[0])}`;
        }
        if (activeFilters.plan.length > 0) {
            url += `&plan=${encodeURIComponent(activeFilters.plan[0])}`;
        }
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success) {
            prospectos = result.data;
            filteredProspectos = prospectos;
            totalPages = result.total_pages;
            renderProspectos();
            updatePaginationInfo(result.total, result.page);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// ====================================
// RENDERIZAR TABLA
// ====================================

function renderProspectos() {
    const tbody = document.getElementById('prospectosTableBody');
    
    if (filteredProspectos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="11" style="text-align: center; padding: 40px; color: var(--color-text-secondary);">
                    No hay prospectos para mostrar
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = filteredProspectos.map(p => `
        <tr class="${selectedIds.has(p.id) ? 'selected' : ''}" onclick="handleRowClick(event, '${p.telefono}')">
            <td style="text-align: center;" onclick="event.stopPropagation();">
                ${selectMode ? `<input type="checkbox" class="row-checkbox" data-id="${p.id}" 
                    ${selectedIds.has(p.id) ? 'checked' : ''} onchange="toggleRowSelection('${p.id}')">` : ''}
            </td>
            <td>${p.nombre || '-'}</td>
            <td>${p.apellido || '-'}</td>
            <td>${p.carrera || '-'}</td>
            <td>${renderPlan(p.plan)}</td>
            <td>${p.experiencia || 0} años</td>
            <td>${renderEstado(p.estado)}</td>
            <td>${p.fecha_primer_contacto || '-'}</td>
            <td><strong>${p.dias_transcurridos || 0}</strong></td>
            <td>${renderMensajeCount(p.mensaje_count, p.telefono)}</td>
            <td>${renderFollowups(p.followups)}</td>
        </tr>
    `).join('');
    
    feather.replace();
}

// Manejar click en fila
function handleRowClick(event, telefono) {
    if (selectMode) return;
    if (event.target.type === 'checkbox' || event.target.closest('button')) return;
    
    openChatModal(telefono);
}

// Renderizar contador de mensajes
function renderMensajeCount(count, telefono) {
    const displayCount = count || 0;
    const color = displayCount > 0 ? 'var(--color-primary)' : 'var(--color-text-tertiary)';
    const bgColor = displayCount > 0 ? 'var(--color-primary-light)' : 'var(--color-bg-tertiary)';
    
    return `
        <button class="mensaje-count-badge" 
                onclick="event.stopPropagation(); openChatModal('${telefono}')" 
                title="Ver conversación"
                style="background: ${bgColor}; color: ${color}; border: 1px solid ${color};">
            <i data-feather="message-circle" style="width: 14px; height: 14px;"></i>
            <span style="font-weight: 600;">${displayCount}</span>
        </button>
    `;
}

// Renderizar plan
function renderPlan(plan) {
    if (!plan) return '-';
    const color = plan.toLowerCase() === 'regular' ? '#3b82f6' : '#8b5cf6';
    return `<span style="color: ${color}; font-weight: 500;">${plan}</span>`;
}

// Renderizar estado
function renderEstado(estado) {
    const estados = {
        'nuevo': { label: 'Nuevo', bg: '#dbeafe', color: '#1e40af' },
        'calificando': { label: 'Calificando', bg: '#fef3c7', color: '#92400e' },
        'persuadiendo': { label: 'Persuadiendo', bg: '#fce7f3', color: '#831843' },
        'listo_matricula': { label: 'Listo', bg: '#d1fae5', color: '#065f46' },
        'en_proceso': { label: 'En proceso primer contacto', bg: '#dbeafe', color: '#1e40af' },
        'perdido': { label: 'Perdido', bg: '#fee2e2', color: '#991b1b' },
        'primer_contacto': { label: 'Primer Contacto', bg: '#d1fae5', color: '#166534' }
    };
    
    const e = estados[estado] || { label: estado, bg: '#e5e7eb', color: '#374151' };
    return `<span style="background: ${e.bg}; color: ${e.color}; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 500; display: inline-block;">${e.label}</span>`;
}

// Renderizar followups
function renderFollowups(followups) {
    const dias = [
        { num: 3, data: followups.dia3 },
        { num: 5, data: followups.dia5 },
        { num: 6, data: followups.dia6 },
        { num: 8, data: followups.dia8 }
    ];
    
    return dias.map(d => {
        const enviado = d.data.enviado;
        const bg = enviado ? '#10b981' : 'var(--color-bg-secondary)';
        const border = enviado ? '#059669' : 'var(--color-border-primary)';
        const color = enviado ? 'white' : 'var(--color-text-secondary)';
        const title = `Día ${d.num}: ${enviado ? 'Enviado' : 'Pendiente'}`;
        
        return `<span style="width: 30px; height: 30px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.6875rem; font-weight: 600; border: 2px solid ${border}; background: ${bg}; color: ${color}; margin-right: 4px;" title="${title}">${d.num}</span>`;
    }).join('');
}

// ====================================
// MODAL DE CHAT CON DOS COLUMNAS
// ====================================

async function openChatModal(telefono) {
    if (!telefono) {
        console.error('Teléfono no proporcionado');
        return;
    }
    
    // Mostrar modal
    if (chatModal) {
        chatModal.show();
    }
    
    // Mostrar loading en ambas columnas
    document.getElementById('chatLoading').style.display = 'flex';
    document.getElementById('chatMessages').style.display = 'none';
    document.getElementById('chatEmpty').style.display = 'none';
    document.getElementById('prospectoInfo').innerHTML = '<div class="info-loading"><div class="spinner-border text-primary spinner-border-sm" role="status"></div></div>';
    
    try {
        const response = await fetch(`/prospectos_activos/api/mensajes/${telefono}`);
        const result = await response.json();
        
        if (result.success) {
            displayChatMessages(result.mensajes, result.prospecto);
            displayProspectoInfo(result.prospecto);
        } else {
            console.error('Error al cargar mensajes:', result.error);
            showChatError();
        }
    } catch (error) {
        console.error('Error:', error);
        showChatError();
    }
}

function displayChatMessages(mensajes, prospecto) {
    document.getElementById('chatLoading').style.display = 'none';
    
    // Actualizar header
    if (prospecto) {
        document.getElementById('chatProspectoNombre').textContent = `${prospecto.nombre} ${prospecto.apellido}`;
        
        document.getElementById('chatProspectoDetails').innerHTML = `
            <div class="prospecto-detail">
                <i data-feather="mail"></i>
                <span>${prospecto.email || 'Sin email'}</span>
            </div>
            <div class="prospecto-detail">
                <i data-feather="phone"></i>
                <span>${prospecto.telefono || 'Sin teléfono'}</span>
            </div>
        `;
    }
    
    // Verificar mensajes
    if (!mensajes || mensajes.length === 0) {
        document.getElementById('chatEmpty').style.display = 'flex';
        document.getElementById('chatMessages').style.display = 'none';
        feather.replace();
        return;
    }
    
    // Renderizar mensajes
    const chatContainer = document.getElementById('chatMessages');
    chatContainer.style.display = 'flex';
    
    chatContainer.innerHTML = mensajes.map((msg) => {
        const isUser = msg.role === 'user';
        const avatar = isUser ? (prospecto?.nombre?.charAt(0) || 'U') : 'AI';
        
        return `
            <div class="chat-message ${isUser ? 'user' : 'assistant'}">
                <div class="chat-message-avatar">${avatar}</div>
                <div class="chat-message-content">
                    <div class="chat-message-bubble">
                        ${escapeHtml(msg.content)}
                    </div>
                    <div class="chat-message-time">${formatTimestamp(msg.timestamp)}</div>
                </div>
            </div>
        `;
    }).join('');
    
    feather.replace();
    
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 100);
}

function displayProspectoInfo(prospecto) {
    if (!prospecto) {
        document.getElementById('prospectoInfo').innerHTML = '<p style="text-align: center; color: #6c757d;">No hay información disponible</p>';
        return;
    }
    
    const infoContainer = document.getElementById('prospectoInfo');
    
    infoContainer.innerHTML = `
        <!-- Estado General -->
        <div class="info-section">
            <div class="info-section-title">
                <i data-feather="info"></i>
                Estado General
            </div>
            <div class="info-row">
                <span class="info-label">Estado:</span>
                <span class="info-value">${renderEstadoBadge(prospecto.estado)}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Nivel de Intención:</span>
                <span class="info-value">${renderIntencionBadge(prospecto.nivel_intencion)}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Descuento Actual:</span>
                <span class="info-value"><strong>${prospecto.descuento_actual || 0}%</strong></span>
            </div>
        </div>
        
        <!-- Información Académica -->
        <div class="info-section">
            <div class="info-section-title">
                <i data-feather="book-open"></i>
                Información Académica
            </div>
            <div class="info-row">
                <span class="info-label">Carrera:</span>
                <span class="info-value">${prospecto.carrera || 'No especificada'}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Plan:</span>
                <span class="info-value">${renderPlanBadge(prospecto.plan)}</span>
            </div>
        </div>
        
        <!-- Fechas -->
        <div class="info-section">
            <div class="info-section-title">
                <i data-feather="calendar"></i>
                Fechas Importantes
            </div>
            <div class="info-row">
                <span class="info-label">Primer Contacto:</span>
                <span class="info-value">${prospecto.fecha_primer_contacto || 'No registrado'}</span>
            </div>
        </div>
        
        <!-- Follow-ups -->
        <div class="info-section">
            <div class="info-section-title">
                <i data-feather="send"></i>
                Follow-ups
            </div>
            <div class="followup-list">
                ${renderFollowupList(prospecto.followups)}
            </div>
        </div>
        
        <!-- Estado del Chat -->
        <div class="info-section">
            <div class="info-section-title">
                <i data-feather="message-square"></i>
                Estado del Chat
            </div>
            <div class="info-row">
                <span class="info-label">Status:</span>
                <span class="info-value">${renderChatStatusBadge(prospecto.chat_status)}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Derivado a Humano:</span>
                <span class="info-value">${prospecto.derivado_a_humano ? '<span class="info-badge success">Sí</span>' : '<span class="info-badge secondary">No</span>'}</span>
            </div>
            ${prospecto.derivado_a_humano ? `
                <div class="info-row">
                    <span class="info-label">Agente:</span>
                    <span class="info-value">${prospecto.agente_asignado || 'No asignado'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Fecha Derivación:</span>
                    <span class="info-value">${prospecto.fecha_derivacion || '-'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Razón:</span>
                    <span class="info-value">${prospecto.razon_derivacion || '-'}</span>
                </div>
            ` : ''}
        </div>
        
        <!-- Notas -->
        <div class="info-section">
            <div class="info-section-title">
                <i data-feather="file-text"></i>
                Notas
            </div>
            <div class="info-notes">${prospecto.notas || ''}</div>
        </div>
    `;
    
    feather.replace();
}

function renderFollowupList(followups) {
    const dias = [
        { num: 3, data: followups.dia3 },
        { num: 5, data: followups.dia5 },
        { num: 6, data: followups.dia6 },
        { num: 8, data: followups.dia8 }
    ];
    
    return dias.map(d => {
        const enviado = d.data.enviado;
        const clase = enviado ? 'sent' : 'pending';
        const icono = enviado ? 'check-circle' : 'circle';
        
        return `
            <div class="followup-item ${clase}">
                <i data-feather="${icono}"></i>
                <span class="followup-label">Día ${d.num}</span>
                <span class="followup-date">${d.data.fecha || 'Pendiente'}</span>
            </div>
        `;
    }).join('');
}

function renderEstadoBadge(estado) {
    const estados = {
        'nuevo': 'primary',
        'calificando': 'info',
        'persuadiendo': 'warning',
        'listo_matricula': 'success',
        'en_proceso': 'secondary',
        'perdido': 'danger'
    };
    const clase = estados[estado] || 'secondary';
    return `<span class="info-badge ${clase}">${estado || 'Sin estado'}</span>`;
}

function renderIntencionBadge(intencion) {
    const intenciones = {
        'alta': 'success',
        'media': 'warning',
        'baja': 'secondary'
    };
    const clase = intenciones[intencion?.toLowerCase()] || 'secondary';
    return `<span class="info-badge ${clase}">${intencion || 'No definida'}</span>`;
}

function renderPlanBadge(plan) {
    if (!plan) return '<span class="info-badge secondary">Sin plan</span>';
    const color = plan.toLowerCase() === 'regular' ? 'primary' : 'info';
    return `<span class="info-badge ${color}">${plan}</span>`;
}

function renderChatStatusBadge(status) {
    if (!status) return '<span class="info-badge secondary">Sin status</span>';
    return `<span class="info-badge info">${status}</span>`;
}

function showChatError() {
    document.getElementById('chatLoading').style.display = 'none';
    document.getElementById('chatMessages').style.display = 'none';
    
    const emptyDiv = document.getElementById('chatEmpty');
    emptyDiv.style.display = 'flex';
    emptyDiv.innerHTML = `
        <i data-feather="alert-circle" style="color: var(--color-error);"></i>
        <p style="color: var(--color-error);">Error al cargar los mensajes</p>
    `;
    feather.replace();
}

function closeChatModal() {
    if (chatModal) {
        chatModal.hide();
    }
}

// ====================================
// UTILIDADES
// ====================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString('es-CL', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ====================================
// SELECCIÓN MÚLTIPLE
// ====================================

function toggleSelectMode() {
    selectMode = !selectMode;
    const btn = document.getElementById('btnToggleSelect');
    const selectAll = document.getElementById('selectAll');
    
    if (selectMode) {
        btn.classList.add('active');
        selectAll.style.display = 'block';
        btn.style.display = 'none';
    } else {
        btn.classList.remove('active');
        selectAll.style.display = 'none';
        btn.style.display = 'block';
        selectedIds.clear();
    }
    
    renderProspectos();
    updateActivarButton();
}

function toggleSelectAll() {
    const checked = document.getElementById('selectAll').checked;
    
    if (checked) {
        filteredProspectos.forEach(p => selectedIds.add(p.id));
    } else {
        selectedIds.clear();
    }
    
    renderProspectos();
    updateActivarButton();
}

function toggleRowSelection(id) {
    if (selectedIds.has(id)) {
        selectedIds.delete(id);
    } else {
        selectedIds.add(id);
    }
    
    updateActivarButton();
    updateSelectAllCheckbox();
}

function updateSelectAllCheckbox() {
    const selectAll = document.getElementById('selectAll');
    const allSelected = filteredProspectos.length > 0 && 
                       filteredProspectos.every(p => selectedIds.has(p.id));
    selectAll.checked = allSelected;
}

function updateActivarButton() {
    const btn = document.getElementById('btnActivar');
    const count = document.getElementById('selectedCount');
    
    count.textContent = selectedIds.size;
    btn.disabled = selectedIds.size === 0;
}

async function activarSeleccionados() {
    if (selectedIds.size === 0) return;
    
    if (!confirm(`¿Activar ${selectedIds.size} prospecto(s)?`)) return;
    
    try {
        const response = await fetch('/prospectos_activos/api/activar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids: Array.from(selectedIds) })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            selectedIds.clear();
            loadProspectos();
            loadStats();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al activar prospectos');
    }
}

// ====================================
// ORDENAMIENTO
// ====================================

function sortBy(column) {
    if (sortColumn === column) {
        sortOrder = sortOrder === 'ASC' ? 'DESC' : 'ASC';
    } else {
        sortColumn = column;
        sortOrder = 'ASC';
    }
    
    updateSortIndicators();
    loadProspectos();
}

function updateSortIndicators() {
    document.querySelectorAll('.sort-indicator').forEach(btn => {
        btn.classList.remove('active', 'asc', 'desc');
        const icon = btn.querySelector('i');
        icon.setAttribute('data-feather', 'chevrons-up-down');
    });
    
    const activeBtn = document.querySelector(`.sort-indicator[data-sort="${sortColumn}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active', sortOrder.toLowerCase());
        const icon = activeBtn.querySelector('i');
        icon.setAttribute('data-feather', sortOrder === 'ASC' ? 'chevron-up' : 'chevron-down');
    }
    
    feather.replace();
}

// ====================================
// PAGINACIÓN
// ====================================

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        loadProspectos();
    }
}

function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        loadProspectos();
    }
}

function updatePaginationInfo(total, page) {
    document.getElementById('currentPage').textContent = page;
    document.getElementById('totalPages').textContent = totalPages;
    document.getElementById('showingCount').textContent = filteredProspectos.length;
    document.getElementById('totalCount').textContent = total;
    
    document.getElementById('btnPrev').disabled = page <= 1;
    document.getElementById('btnNext').disabled = page >= totalPages;
}

function refreshProspectos() {
    currentPage = 1;
    loadProspectos();
    loadStats();
}