// ========================================
// KNOWLEDGE BASE DETAIL - GESTIÓN DE PUNTOS
// ========================================

let currentKbId = null;
let currentPoints = [];
let currentPage = 1;
let totalPages = 1;
let selectedPointId = null;

// ========================================
// INITIALIZATION
// ========================================

async function loadBaseInfo() {
    currentKbId = document.getElementById('kbId').value;
    
    try {
        const response = await fetch(`/knowledge_base/api/bases/${currentKbId}`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('baseName').textContent = data.base.nombre;
            document.getElementById('baseDescription').textContent = data.base.descripcion || '';
        } else {
            console.error('Error loading base info:', data.error);
        }
    } catch (error) {
        console.error('Error loading base info:', error);
    }
}

async function loadBaseStats() {
    try {
        const response = await fetch(`/knowledge_base/api/bases/${currentKbId}`);
        const data = await response.json();
        
        if (data.success) {
            renderBaseStats(data.base);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function renderBaseStats(base) {
    const container = document.getElementById('statsCardsContainer');
    
    const html = `
        <div class="stats-card">
            <div class="stats-card-header">
                <div class="stats-card-title">Total Puntos</div>
                <div class="stats-card-icon primary">
                    <i data-feather="layers"></i>
                </div>
            </div>
            <div class="stats-card-body">
                <div class="stats-card-value">${base.total_points}</div>
                <div class="stats-card-label">Puntos en la base</div>
            </div>
        </div>

        <div class="stats-card">
            <div class="stats-card-header">
                <div class="stats-card-title">Sincronizados</div>
                <div class="stats-card-icon success">
                    <i data-feather="check-circle"></i>
                </div>
            </div>
            <div class="stats-card-body">
                <div class="stats-card-value">${base.synced_points}</div>
                <div class="stats-card-label">En Qdrant</div>
            </div>
        </div>

        <div class="stats-card">
            <div class="stats-card-header">
                <div class="stats-card-title">Pendientes</div>
                <div class="stats-card-icon warning">
                    <i data-feather="clock"></i>
                </div>
            </div>
            <div class="stats-card-body">
                <div class="stats-card-value">${base.pending_points}</div>
                <div class="stats-card-label">Por sincronizar</div>
            </div>
        </div>

        <div class="stats-card">
            <div class="stats-card-header">
                <div class="stats-card-title">Última Sync</div>
                <div class="stats-card-icon info">
                    <i data-feather="refresh-cw"></i>
                </div>
            </div>
            <div class="stats-card-body">
                <div class="stats-card-value" style="font-size: 1rem;">
                    ${base.last_synced_at ? formatRelativeTime(base.last_synced_at) : 'Nunca'}
                </div>
                <div class="stats-card-label">
                    ${base.last_synced_at ? formatDateTime(base.last_synced_at) : 'Sin sincronizar'}
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    feather.replace();
}

// ========================================
// LOAD POINTS
// ========================================

async function loadPoints(page = 1) {
    currentPage = page;
    const search = document.getElementById('searchPoints').value;
    
    const url = `/knowledge_base/api/bases/${currentKbId}/points?page=${page}&page_size=50&search=${encodeURIComponent(search)}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            currentPoints = data.points;
            totalPages = data.total_pages;
            renderPoints(data.points);
            updatePagination(data);
        } else {
            console.error('Error loading points:', data.error);
        }
    } catch (error) {
        console.error('Error loading points:', error);
    }
}

function renderPoints(points) {
    const container = document.getElementById('pointsList');
    
    if (!points || points.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i data-feather="inbox" style="width: 48px; height: 48px; opacity: 0.3;"></i>
                <p class="mt-3 text-muted">No hay puntos</p>
            </div>
        `;
        feather.replace();
        return;
    }
    
    const html = points.map(point => `
        <div class="point-item ${selectedPointId === point.id ? 'active' : ''}" 
             onclick="selectPoint('${point.id}')">
            <div class="point-item-header">
                <span class="point-item-id">${point.id.substring(0, 8)}...</span>
                <span class="point-item-badge ${point.synced ? 'synced' : 'pending'}">
                    ${point.synced ? 'Sync' : 'Pendiente'}
                </span>
            </div>
            <div class="point-item-content">
                ${point.content_preview}
            </div>
            <div class="point-item-footer">
                ${formatRelativeTime(point.created_at)}
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
    feather.replace();
}

function updatePagination(data) {
    document.getElementById('paginationInfo').textContent = 
        `Página ${data.page} de ${data.total_pages} (${data.total} puntos)`;
    
    document.getElementById('btnPrev').disabled = data.page <= 1;
    document.getElementById('btnNext').disabled = data.page >= data.total_pages;
}

// ========================================
// POINT SELECTION & DETAIL
// ========================================

async function selectPoint(pointId) {
    selectedPointId = pointId;
    
    // Actualizar UI de lista
    document.querySelectorAll('.point-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.point-item').classList.add('active');
    
    // Cargar detalle
    try {
        const response = await fetch(`/knowledge_base/api/points/${pointId}`);
        const data = await response.json();
        
        if (data.success) {
            showPointDetail(data.point);
        } else {
            showNotification('error', 'Error al cargar punto: ' + data.error);
        }
    } catch (error) {
        console.error('Error loading point detail:', error);
        showNotification('error', 'Error al cargar punto');
    }
}

function showPointDetail(point) {
    document.getElementById('panelEmpty').style.display = 'none';
    document.getElementById('panelContent').style.display = 'flex';
    
    document.getElementById('currentPointId').value = point.id;
    document.getElementById('pageContent').value = point.page_content;
    document.getElementById('metadata').value = JSON.stringify(point.metadata, null, 2);
    
    // Update sync badge
    const syncBadge = document.getElementById('syncBadge');
    if (point.synced) {
        syncBadge.className = 'badge bg-success';
        syncBadge.innerHTML = '<i data-feather="check-circle"></i> Sincronizado';
    } else {
        syncBadge.className = 'badge bg-warning';
        syncBadge.innerHTML = '<i data-feather="clock"></i> Pendiente';
    }
    
    updateCharCount();
    feather.replace();
}

// ========================================
// CRUD OPERATIONS
// ========================================

function openCreatePointModal() {
    const modal = new bootstrap.Modal(document.getElementById('createPointModal'));
    document.getElementById('newPageContent').value = '';
    document.getElementById('newMetadata').value = '';
    modal.show();
    feather.replace();
}

async function createPoint() {
    const pageContent = document.getElementById('newPageContent').value.trim();
    const metadataStr = document.getElementById('newMetadata').value.trim();
    
    if (!pageContent) {
        showNotification('error', 'El contenido (pageContent) es obligatorio');
        return;
    }
    
    let metadata = {};
    if (metadataStr) {
        try {
            metadata = JSON.parse(metadataStr);
        } catch (e) {
            showNotification('error', 'El metadata no es un JSON válido');
            return;
        }
    }
    
    try {
        const response = await fetch(`/knowledge_base/api/bases/${currentKbId}/points/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                page_content: pageContent,
                metadata: metadata
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('createPointModal'));
            modal.hide();
            
            await loadPoints(currentPage);
            await loadBaseStats();
            
            showNotification('success', data.message);
        } else {
            showNotification('error', data.error || 'Error al crear punto');
        }
    } catch (error) {
        console.error('Error creating point:', error);
        showNotification('error', 'Error al crear punto');
    }
}

async function savePoint() {
    const pointId = document.getElementById('currentPointId').value;
    const pageContent = document.getElementById('pageContent').value.trim();
    const metadataStr = document.getElementById('metadata').value.trim();
    
    if (!pageContent) {
        showNotification('error', 'El contenido no puede estar vacío');
        return;
    }
    
    let metadata = {};
    if (metadataStr) {
        try {
            metadata = JSON.parse(metadataStr);
        } catch (e) {
            showNotification('error', 'El metadata no es un JSON válido');
            return;
        }
    }
    
    try {
        const response = await fetch(`/knowledge_base/api/points/${pointId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                page_content: pageContent,
                metadata: metadata
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            await loadPoints(currentPage);
            await loadBaseStats();
            await selectPoint(pointId);
            
            showNotification('success', data.message);
        } else {
            showNotification('error', data.error || 'Error al guardar punto');
        }
    } catch (error) {
        console.error('Error saving point:', error);
        showNotification('error', 'Error al guardar punto');
    }
}

async function deleteCurrentPoint() {
    const pointId = document.getElementById('currentPointId').value;
    
    if (!confirm('¿Estás seguro que deseas eliminar este punto?')) {
        return;
    }
    
    try {
        const response = await fetch(`/knowledge_base/api/points/${pointId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('panelEmpty').style.display = 'flex';
            document.getElementById('panelContent').style.display = 'none';
            
            await loadPoints(currentPage);
            await loadBaseStats();
            
            showNotification('success', data.message);
        } else {
            showNotification('error', data.error || 'Error al eliminar punto');
        }
    } catch (error) {
        console.error('Error deleting point:', error);
        showNotification('error', 'Error al eliminar punto');
    }
}

// ========================================
// SYNC OPERATIONS
// ========================================

async function syncCurrentPoint() {
    const pointId = document.getElementById('currentPointId').value;
    const btn = document.getElementById('btnSync');
    
    btn.classList.add('syncing');
    btn.disabled = true;
    
    try {
        // TODO: Implementar endpoint de sincronización individual
        showNotification('info', 'Función de sincronización individual próximamente');
    } catch (error) {
        console.error('Error syncing point:', error);
        showNotification('error', 'Error al sincronizar punto');
    } finally {
        btn.classList.remove('syncing');
        btn.disabled = false;
    }
}

async function syncAllPoints() {
    // Obtener referencia al botón
    const btnSync = document.querySelector('button[onclick="syncAllPoints()"]');
    
    // Verificar que hay puntos pendientes
    try {
        const response = await fetch(`/knowledge_base/api/bases/${currentKbId}`);
        const data = await response.json();
        
        if (!data.success) {
            showNotification('error', 'Error al verificar estado de la base');
            return;
        }
        
        const pendingCount = data.base.pending_points;
        
        if (pendingCount === 0) {
            showNotification('info', 'No hay puntos pendientes de sincronización');
            return;
        }
        
        // Confirmación con información de costo estimado
        const estimatedTokens = pendingCount * 500; // Promedio 500 tokens por punto
        const estimatedCost = (estimatedTokens / 1000000) * 0.13;
        
        const confirmar = confirm(
            `Sincronización Masiva\n\n` +
            `Puntos a sincronizar: ${pendingCount}\n` +
            `Costo estimado: $${estimatedCost.toFixed(4)} USD\n` +
            `Tiempo estimado: ${Math.ceil(pendingCount / 50)} minutos\n\n` +
            `¿Deseas continuar?`
        );
        
        if (!confirmar) return;
        
        // Deshabilitar botón y mostrar loading
        let originalHTML = '';
        if (btnSync) {
            originalHTML = btnSync.innerHTML;
            btnSync.disabled = true;
            btnSync.innerHTML = '<i data-feather="loader"></i> Sincronizando...';
            feather.replace();
            
            // Agregar clase de animación
            const icon = btnSync.querySelector('i');
            if (icon) {
                icon.style.animation = 'spin 1s linear infinite';
            }
        }
        
        // Mostrar notificación de progreso
        showNotification('info', `Sincronizando ${pendingCount} puntos... Esto puede tomar varios minutos.`);
        
        // Llamar al endpoint
        const syncResponse = await fetch(`/knowledge_base/api/bases/${currentKbId}/sync`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await syncResponse.json();
        
        // Restaurar botón
        if (btnSync) {
            btnSync.disabled = false;
            btnSync.innerHTML = originalHTML;
            feather.replace();
        }
        
        if (result.success) {
            // Recargar datos
            await loadPoints(currentPage);
            await loadBaseStats();
            
            // Mostrar resultado detallado
            let message = `✓ ${result.synced} puntos sincronizados exitosamente`;
            
            if (result.errors > 0) {
                message += `\n⚠ ${result.errors} errores`;
                console.error('Errores de sincronización:', result.errors_detail);
            }
            
            if (result.cost) {
                message += `\n💰 Costo: ${result.cost.cost_formatted}`;
            }
            
            showNotification('success', message);
            
            // Log detallado
            console.log('Sincronización completada:', {
                sincronizados: result.synced,
                errores: result.errors,
                total: result.total_points,
                costo: result.cost
            });
            
        } else {
            showNotification('error', result.error || 'Error al sincronizar puntos');
        }
        
    } catch (error) {
        console.error('Error syncing all points:', error);
        showNotification('error', 'Error al sincronizar puntos: ' + error.message);
        
        // Restaurar botón en caso de error
        if (btnSync) {
            btnSync.disabled = false;
            btnSync.innerHTML = '<i data-feather="refresh-cw"></i> Sincronizar Todo';
            feather.replace();
        }
    }
}

// ========================================
// IMPORT JSON
// ========================================

function openImportModal() {
    const modal = new bootstrap.Modal(document.getElementById('importModal'));
    document.getElementById('jsonFile').value = '';
    modal.show();
    feather.replace();
}

async function importJSON() {
    const fileInput = document.getElementById('jsonFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showNotification('error', 'Selecciona un archivo JSON');
        return;
    }
    
    try {
        const text = await file.text();
        let points = JSON.parse(text);
        
        if (!Array.isArray(points)) {
            showNotification('error', 'El JSON debe ser un array de objetos');
            return;
        }
        
        // Detectar formato del JSON
        let formatoDetectado = 'desconocido';
        if (points.length > 0) {
            const primerPunto = points[0];
            if (primerPunto.contenidoPagina) {
                formatoDetectado = 'español';
            } else if (primerPunto.pageContent) {
                formatoDetectado = 'inglés';
            }
        }
        
        console.log(`Formato detectado: ${formatoDetectado}`);
        
        // Validar y normalizar puntos (soporta español e inglés)
        const validPoints = [];
        const invalidPoints = [];
        
        points.forEach((point, idx) => {
            if (point && typeof point === 'object') {
                // Soportar tanto español (contenidoPagina/metadatos) como inglés (pageContent/metadata)
                const pageContent = String(point.pageContent || point.contenidoPagina || '').trim();
                const metadata = point.metadata || point.metadatos || {};
                
                if (pageContent) {
                    validPoints.push({
                        pageContent: pageContent,
                        metadata: metadata
                    });
                } else {
                    invalidPoints.push({
                        index: idx + 1,
                        reason: 'contenido vacío'
                    });
                }
            } else {
                invalidPoints.push({
                    index: idx + 1,
                    reason: 'no es un objeto válido'
                });
            }
        });
        
        console.log(`Puntos válidos: ${validPoints.length}`);
        console.log(`Puntos inválidos: ${invalidPoints.length}`);
        
        if (validPoints.length === 0) {
            showNotification('error', `No se encontraron puntos válidos en el JSON (Formato: ${formatoDetectado})`);
            console.log('Primer punto del archivo:', points[0]);
            console.log('Puntos inválidos:', invalidPoints);
            return;
        }
        
        // Mostrar advertencia si hay puntos inválidos
        if (invalidPoints.length > 0) {
            console.warn('Puntos inválidos encontrados:', invalidPoints);
            const continuar = confirm(
                `Formato: ${formatoDetectado}\n` +
                `Puntos válidos: ${validPoints.length}\n` +
                `Puntos inválidos: ${invalidPoints.length}\n\n` +
                `¿Deseas continuar importando los ${validPoints.length} puntos válidos?`
            );
            if (!continuar) return;
        } else {
            // Confirmación normal
            const continuar = confirm(
                `Formato detectado: ${formatoDetectado}\n` +
                `Total de puntos: ${validPoints.length}\n\n` +
                `¿Importar estos puntos a la base de conocimiento?`
            );
            if (!continuar) return;
        }
        
        // Mostrar indicador de carga
        showNotification('info', `Importando ${validPoints.length} puntos...`);
        
        // Enviar al backend
        const response = await fetch(`/knowledge_base/api/bases/${currentKbId}/points/import`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                points: validPoints
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('importModal'));
            modal.hide();
            
            // Recargar datos
            await loadPoints(currentPage);
            await loadBaseStats();
            
            // Mostrar resultado detallado
            let message = `✓ ${result.imported} puntos importados exitosamente`;
            if (result.errors && result.errors.length > 0) {
                message += `\n⚠ ${result.errors.length} errores`;
                console.error('Errores de importación:', result.errors);
            }
            
            showNotification('success', message);
            
            // Log final
            console.log('Importación completada:', {
                formato: formatoDetectado,
                importados: result.imported,
                errores: result.errors?.length || 0
            });
            
        } else {
            showNotification('error', result.error || 'Error al importar puntos');
        }
        
    } catch (error) {
        console.error('Error importing JSON:', error);
        
        if (error instanceof SyntaxError) {
            showNotification('error', 'El archivo no es un JSON válido');
        } else {
            showNotification('error', 'Error al procesar el archivo: ' + error.message);
        }
    }
}

// ========================================
// SEARCH & PAGINATION
// ========================================

function searchPoints() {
    loadPoints(1);
}

function previousPage() {
    if (currentPage > 1) {
        loadPoints(currentPage - 1);
    }
}

function nextPage() {
    if (currentPage < totalPages) {
        loadPoints(currentPage + 1);
    }
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

function updateCharCount() {
    const content = document.getElementById('pageContent').value;
    const charCount = content.length;
    const tokenCount = Math.ceil(charCount / 4); // Aproximación
    
    document.getElementById('charCount').textContent = charCount;
    document.getElementById('tokenCount').textContent = tokenCount;
}

// Event listener para contador
document.addEventListener('DOMContentLoaded', function() {
    const pageContent = document.getElementById('pageContent');
    if (pageContent) {
        pageContent.addEventListener('input', updateCharCount);
    }
});

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
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : type === 'info' ? 'info' : 'danger'} position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i data-feather="${type === 'success' ? 'check-circle' : type === 'info' ? 'info' : 'x-circle'}" class="me-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    feather.replace();
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}