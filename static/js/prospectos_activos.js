// Prospectos Activos - JavaScript

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
        });
    }
});

// Cargar prospectos
async function loadProspectos() {
    try {
        const searchTerm = document.getElementById('searchInput')?.value || '';
        const url = `/prospectos_activos/api/list?page=${currentPage}&page_size=${pageSize}&search=${encodeURIComponent(searchTerm)}&sort_column=${sortColumn}&sort_order=${sortOrder}`;
        
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

// Renderizar tabla
function renderProspectos() {
    const tbody = document.getElementById('prospectosTableBody');
    
    if (filteredProspectos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" style="text-align: center; padding: 40px; color: var(--color-text-secondary);">
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
            <td><strong>${p.dias_transcurridos || 0}</strong></td>
            <td>${renderMensajeCount(p.mensaje_count, p.telefono)}</td>
            <td>${renderFollowups(p.followups)}</td>
        </tr>
    `).join('');
    
    feather.replace();
}

// Manejar click en fila
function handleRowClick(event, telefono) {
    // No abrir modal si se está en modo selección
    if (selectMode) {
        return;
    }
    
    // No abrir si se clickeó en un checkbox o botón
    if (event.target.type === 'checkbox' || event.target.closest('button')) {
        return;
    }
    
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

// Abrir modal de chat
async function openChatModal(telefono) {
    if (!telefono) {
        console.error('Teléfono no proporcionado');
        return;
    }
    
    // Mostrar modal
    if (chatModal) {
        chatModal.show();
    }
    
    // Mostrar loading
    document.getElementById('chatLoading').style.display = 'flex';
    document.getElementById('chatMessages').style.display = 'none';
    document.getElementById('chatEmpty').style.display = 'none';
    
    try {
        const response = await fetch(`/prospectos_activos/api/mensajes/${telefono}`);
        const result = await response.json();
        
        if (result.success) {
            displayChatMessages(result.mensajes, result.prospecto);
        } else {
            console.error('Error al cargar mensajes:', result.error);
            showChatError();
        }
    } catch (error) {
        console.error('Error:', error);
        showChatError();
    }
}

// Mostrar mensajes en el chat
function displayChatMessages(mensajes, prospecto) {
    // Ocultar loading
    document.getElementById('chatLoading').style.display = 'none';
    
    // Actualizar header con información del prospecto
    if (prospecto) {
        document.getElementById('chatProspectoNombre').innerHTML = `
            <i data-feather="message-circle"></i>
            ${prospecto.nombre} ${prospecto.apellido}
        `;
        
        document.getElementById('chatProspectoDetails').innerHTML = `
            <div class="prospecto-detail">
                <i data-feather="mail"></i>
                <span>${prospecto.email || 'Sin email'}</span>
            </div>
            <div class="prospecto-detail">
                <i data-feather="phone"></i>
                <span>${prospecto.telefono || 'Sin teléfono'}</span>
            </div>
            <div class="prospecto-detail">
                <i data-feather="book-open"></i>
                <span>${prospecto.carrera || 'Sin carrera'}</span>
            </div>
            <div class="prospecto-detail">
                ${renderPlanBadge(prospecto.plan)}
            </div>
        `;
    }
    
    // Verificar si hay mensajes
    if (!mensajes || mensajes.length === 0) {
        document.getElementById('chatEmpty').style.display = 'flex';
        document.getElementById('chatMessages').style.display = 'none';
        feather.replace();
        return;
    }
    
    // Renderizar mensajes
    const chatContainer = document.getElementById('chatMessages');
    chatContainer.style.display = 'block';
    
    chatContainer.innerHTML = mensajes.map((msg, index) => {
        const isAI = msg.type === 'ai';
        const isHuman = msg.type === 'human';
        const messageClass = isAI ? 'message-ai' : isHuman ? 'message-human' : 'message-system';
        const alignClass = isAI ? 'message-left' : 'message-right';
        
        // Mostrar número de mensaje en lugar de timestamp
        const messageNumber = `Mensaje #${index + 1}`;
        
        return `
            <div class="chat-message ${alignClass}">
                <div class="message-bubble ${messageClass}">
                    <div class="message-header">
                        <span class="message-sender">
                            ${isAI ? '<i data-feather="cpu"></i> AI Assistant' : isHuman ? '<i data-feather="user"></i> ' + (prospecto?.nombre || 'Usuario') : 'Sistema'}
                        </span>
                        <span class="message-time">${messageNumber}</span>
                    </div>
                    <div class="message-content">
                        ${escapeHtml(msg.content)}
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Reemplazar iconos de Feather
    feather.replace();
    
    // Scroll al final
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 100);
}

// Mostrar error en el chat
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

// Escapar HTML para prevenir XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Renderizar plan badge
function renderPlanBadge(plan) {
    if (!plan) return '<span class="badge bg-secondary">Sin plan</span>';
    const color = plan.toLowerCase() === 'regular' ? 'primary' : 'info';
    return `<span class="badge bg-${color}">${plan}</span>`;
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
        'en_proceso': { label: 'Activo', bg: '#dbeafe', color: '#1e40af' },
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

// Toggle select mode
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

// Toggle select all
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

// Toggle row selection
function toggleRowSelection(id) {
    if (selectedIds.has(id)) {
        selectedIds.delete(id);
    } else {
        selectedIds.add(id);
    }
    
    updateActivarButton();
    updateSelectAllCheckbox();
}

// Update select all checkbox
function updateSelectAllCheckbox() {
    const selectAll = document.getElementById('selectAll');
    const allSelected = filteredProspectos.length > 0 && 
                       filteredProspectos.every(p => selectedIds.has(p.id));
    selectAll.checked = allSelected;
}

// Update activar button
function updateActivarButton() {
    const btn = document.getElementById('btnActivar');
    const count = document.getElementById('selectedCount');
    
    count.textContent = selectedIds.size;
    btn.disabled = selectedIds.size === 0;
}

// Activar seleccionados
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
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al activar prospectos');
    }
}

// Refresh
function refreshProspectos() {
    currentPage = 1;
    loadProspectos();
}

// Sorting
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

// Pagination
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