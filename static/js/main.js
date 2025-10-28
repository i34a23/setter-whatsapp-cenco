// Main Application JavaScript

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    console.log('WhatsApp Dashboard initialized');
    
    // Initialize Feather Icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
});

// Utility function for API calls
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    // TODO: Implement toast notification system
    console.log(`[${type.toUpperCase()}] ${message}`);
}

