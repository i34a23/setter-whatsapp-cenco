// ========================================
// KNOWLEDGE BASE - LISTA DE BASES
// ========================================

let currentBases = [];

// ========================================
// LOAD FUNCTIONS
// ========================================

async function loadStats() {
    try {
        const response = await fetch('/knowledge_base/api/bases/list');
        const data = await response.json();
        
        if (data.success) {
            renderStats(data.stats);
        } else {
            console.error('Error loading stats:', data.error);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadBases() {
    try {
        const response = await fetch('/knowledge_base/api/bases/list');
        const data = await response.json();
        
        if (data.success) {
            currentBases = data.bases;
            renderBases(data.bases);
        } else {
            console.error('Error loading bases:', data.error);
            showEmptyState();
        }
    } catch (error) {
        console.error('Error loading bases:', error);
        showEmptyState();
    }
}

// ========================================
// RENDER FUNCTIONS
// ========================================

function renderStats(stats) {
    const container = document.getElementById('statsCardsContainer');
    
    const html = `
        <div class="stats-card" onclick="filterBases('all')">
            <div class="stats-card-header">
                <div class="stats-card-title">Total Bases</div>
                <div class="stats-card-icon primary">
                    <i data-feather="database"></i>
                </div>
            </div>
            <div class="stats-card-body">
                <div class="stats-card-value">${stats.total_bases}</div>
                <div class="stats-card-label">Bases de Conocimiento</div>
            </div>
        </div>

        <div class="stats-card" onclick="filterBases('synced')">
            <div class="stats-card-header">
                <div class="stats-card-title">Total Puntos</div>
                <div class="stats-card-icon success">
                    <i data-feather="layers"></i>
                </div>
            </div>
            <div class="stats-card-body">
                <div class="stats-card-value">${stats.total_points}</div>
                <div class="stats-card-label">Puntos totales</div>
            </div>
        </div>

        <div class="stats-card" onclick="filterBases('synced')">
            <div class="stats-card-header">
                <div class="stats-card-title">Sincronizados</div>
                <div class="stats-card-icon success">
                    <i data-feather="check-circle"></i>
                </div>
            </div>
            <div class="stats-card-body">
                <div class="stats-card-value">${stats.synced_points}</div>
                <div class="stats-card-label">En Qdrant</div>
            </div>
        </div>

        <div class="stats-card" onclick="filterBases('pending')">
            <div class="stats-card-header">
                <div class="stats-card-title">Pendientes</div>
                <div class="stats-card-icon warning">
                    <i data-feather="clock"></i>
                </div>
            </div>
            <div class="stats-card-body">
                <div class="stats-card-value">${stats.pending_points}</div>
                <div class="stats-card-label">Por sincronizar</div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    feather.replace();
}

function renderBases(bases) {
    const container = document.getElementById('kbGridContainer');
    const emptyState = document.getElementById('emptyState');
    const basesGrid = document.getElementById('basesGrid');
    
    if (!bases || bases.length === 0) {
        showEmptyState();
        return;
    }
    
    emptyState.style.display = 'none';
    basesGrid.style.display = 'block';
    
    const html = bases.map(base => `
        <div class="kb-card" onclick="goToBase('${base.id}')">
            <div class="kb-card-header">
                <div class="kb-card-icon">
                    <i data-feather="database"></i>
                </div>
                <div class="kb-card-actions">
                    <button class="kb-card-btn delete" onclick="event.stopPropagation(); openDeleteModal('${base.id}', '${base.nombre}')" title="Eliminar">
                        <i data-feather="trash-2"></i>
                    </button>
                </div>
            </div>
            
            <h3 class="kb-card-title">${base.nombre}</h3>
            
            ${base.descripcion ? `<p class="kb-card-description">${base.descripcion}</p>` : ''}
            
            <div class="kb-card-stats">
                <div class="kb-stat">
                    <span class="kb-stat-label">Total Puntos</span>
                    <span class="kb-stat-value">${base.total_points}</span>
                </div>
                <div class="kb-stat">
                    <span class="kb-stat-label">Sincronizados</span>
                    <span class="kb-stat-value synced">${base.synced_points}</span>
                </div>
            </div>
            
            <div class="kb-card-footer">
                <span class="kb-sync-status ${base.sync_status}">
                    <i data-feather="${getSyncIcon(base.sync_status)}"></i>
                    ${base.sync_label}
                </span>
                ${base.last_synced_at ? `
                    <span class="kb-last-sync" title="${formatDateTime(base.last_synced_at)}">
                        ${formatRelativeTime(base.last_synced_at)}
                    </span>
                ` : ''}
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
    feather.replace();
}

function showEmptyState() {
    const emptyState = document.getElementById('emptyState');
    const basesGrid = document.getElementById('basesGrid');
    
    emptyState.style.display = 'flex';
    basesGrid.style.display = 'none';
    feather.replace();
}

// ========================================
// MODAL FUNCTIONS
// ========================================

function openCreateModal() {
    const modal = new bootstrap.Modal(document.getElementById('createModal'));
    document.getElementById('createForm').reset();
    modal.show();
    feather.replace();
}

function openDeleteModal(id, nombre) {
    document.getElementById('deleteBaseId').value = id;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
    feather.replace();
}

// ========================================
// CRUD OPERATIONS
// ========================================

async function createBase() {
    const form = document.getElementById('createForm');
    const formData = new FormData(form);
    
    const data = {
        nombre: formData.get('nombre').trim(),
        descripcion: formData.get('descripcion').trim(),
        collection_name: formData.get('collection_name').trim()
    };
    
    if (!data.nombre) {
        alert('El nombre es obligatorio');
        return;
    }
    
    try {
        const response = await fetch('/knowledge_base/api/bases/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('createModal'));
            modal.hide();
            
            // Recargar lista
            await loadStats();
            await loadBases();
            
            // Mostrar mensaje de éxito
            showNotification('success', result.message);
        } else {
            showNotification('error', result.error || 'Error al crear base de conocimiento');
        }
    } catch (error) {
        console.error('Error creating base:', error);
        showNotification('error', 'Error al crear base de conocimiento');
    }
}

async function confirmDelete() {
    const id = document.getElementById('deleteBaseId').value;
    
    try {
        const response = await fetch(`/knowledge_base/api/bases/${id}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
            modal.hide();
            
            // Recargar lista
            await loadStats();
            await loadBases();
            
            // Mostrar mensaje de éxito
            showNotification('success', result.message);
        } else {
            showNotification('error', result.error || 'Error al eliminar base de conocimiento');
        }
    } catch (error) {
        console.error('Error deleting base:', error);
        showNotification('error', 'Error al eliminar base de conocimiento');
    }
}

// ========================================
// NAVIGATION
// ========================================

function goToBase(id) {
    window.location.href = `/knowledge_base/${id}`;
}

function filterBases(filter) {
    // TODO: Implementar filtros
    console.log('Filter:', filter);
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

function getSyncIcon(status) {
    const icons = {
        'synced': 'check-circle',
        'partial': 'alert-circle',
        'pending': 'clock',
        'empty': 'inbox'
    };
    return icons[status] || 'help-circle';
}

function formatRelativeTime(isoDate) {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Justo ahora';
    if (diffMins < 60) return `Hace ${diffMins} min`;
    if (diffHours < 24) return `Hace ${diffHours}h`;
    if (diffDays < 7) return `Hace ${diffDays}d`;
    
    return date.toLocaleDateString('es-CL');
}

function formatDateTime(isoDate) {
    const date = new Date(isoDate);
    return date.toLocaleString('es-CL', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showNotification(type, message) {
    // Crear notificación temporal
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i data-feather="${type === 'success' ? 'check-circle' : 'x-circle'}" class="me-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    feather.replace();
    
    // Remover después de 3 segundos
    setTimeout(() => {
        notification.remove();
    }, 3000);
}