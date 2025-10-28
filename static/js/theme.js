// Theme Management System
class ThemeManager {
    constructor() {
        this.currentTheme = null;
        this.colors = [];
        this.init();
    }

    async init() {
        // Cargar tema guardado
        await this.loadTheme();
        // Cargar colores personalizados
        this.loadCustomColors();
        // Configurar event listeners
        this.setupEventListeners();
    }

    async loadTheme() {
        try {
            const response = await fetch('/api/theme');
            const data = await response.json();
            this.currentTheme = data.theme || '#25D366';
            this.applyTheme(this.currentTheme);
            this.setActiveColorButton(this.currentTheme);
        } catch (error) {
            console.error('Error loading theme:', error);
            this.currentTheme = '#25D366';
        }
    }

    async saveTheme(color) {
        try {
            const response = await fetch('/api/theme', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ theme: color })
            });
            const data = await response.json();
            if (data.success) {
                this.currentTheme = color;
                this.applyTheme(color);
                this.setActiveColorButton(color);
            }
        } catch (error) {
            console.error('Error saving theme:', error);
        }
    }

    applyTheme(color) {
        // Convertir HEX a RGB para variaciones
        const rgb = this.hexToRgb(color);
        const hoverColor = this.adjustBrightness(color, -10);
        
        // Aplicar CSS variables
        document.documentElement.style.setProperty('--color-primary', color);
        document.documentElement.style.setProperty('--color-primary-hover', hoverColor);
        document.documentElement.style.setProperty('--color-primary-light', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.1)`);
    }

    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    }

    adjustBrightness(hex, percent) {
        const rgb = this.hexToRgb(hex);
        const adjust = (value) => {
            const adjusted = value + (value * percent / 100);
            return Math.max(0, Math.min(255, Math.round(adjusted)));
        };
        
        const r = adjust(rgb.r).toString(16).padStart(2, '0');
        const g = adjust(rgb.g).toString(16).padStart(2, '0');
        const b = adjust(rgb.b).toString(16).padStart(2, '0');
        
        return `#${r}${g}${b}`;
    }

    setActiveColorButton(color) {
        document.querySelectorAll('.theme-color').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.color === color) {
                btn.classList.add('active');
            }
        });
    }

    setupEventListeners() {
        // Theme color buttons
        document.querySelectorAll('.theme-color').forEach(button => {
            button.addEventListener('click', (e) => {
                const color = e.currentTarget.dataset.color;
                this.saveTheme(color);
            });
        });

        // Add custom color button
        const addButton = document.querySelector('.theme-color-add');
        if (addButton) {
            addButton.addEventListener('click', () => {
                this.openColorPicker();
            });
        }
    }

    openColorPicker() {
        const modal = document.getElementById('colorPickerModal');
        const picker = document.getElementById('customColorPicker');
        picker.value = this.currentTheme;
        modal.classList.add('active');
    }

    loadCustomColors() {
        const saved = localStorage.getItem('customThemeColors');
        if (saved) {
            this.colors = JSON.parse(saved);
            this.renderCustomColors();
        }
    }

    addCustomColor(color) {
        if (!this.colors.includes(color)) {
            this.colors.push(color);
            localStorage.setItem('customThemeColors', JSON.stringify(this.colors));
            this.renderCustomColors();
        }
        this.saveTheme(color);
    }

    renderCustomColors() {
        const container = document.querySelector('.theme-colors');
        const addButton = container.querySelector('.theme-color-add');
        
        // Remover colores personalizados anteriores
        container.querySelectorAll('.theme-color.custom').forEach(el => el.remove());
        
        // Agregar nuevos colores personalizados
        this.colors.forEach(color => {
            const button = document.createElement('button');
            button.className = 'theme-color custom';
            button.dataset.color = color;
            button.style.backgroundColor = color;
            button.title = 'Color personalizado';
            button.addEventListener('click', () => this.saveTheme(color));
            
            container.insertBefore(button, addButton);
        });
    }
}

// Funciones globales para el modal
function closeColorPicker() {
    document.getElementById('colorPickerModal').classList.remove('active');
}

function addCustomColor() {
    const picker = document.getElementById('customColorPicker');
    const color = picker.value;
    window.themeManager.addCustomColor(color);
    closeColorPicker();
}

// Cerrar modal al hacer click fuera
document.addEventListener('click', (e) => {
    const modal = document.getElementById('colorPickerModal');
    if (e.target === modal) {
        closeColorPicker();
    }
});

// Inicializar Theme Manager
window.themeManager = new ThemeManager();
