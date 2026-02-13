// Gerenciador de tema em TypeScript
interface ThemeElements {
    themeToggleButton: HTMLElement | null;
    bodyElement: HTMLElement;
    documentElement: HTMLElement;
    sunIcon: HTMLElement | null;
    moonIcon: HTMLElement | null;
}

class ThemeManager {
    private elements: ThemeElements;
    private readonly THEME_KEY = 'themePreference';
    private readonly LIGHT_THEME_CLASS = 'light-theme';
    private readonly DARK_THEME_CLASS = 'dark-theme';

    constructor() {
        this.elements = {
            themeToggleButton: document.getElementById('theme-toggle-button'),
            bodyElement: document.body,
            documentElement: document.documentElement,
            sunIcon: document.getElementById('theme-icon-sun'),
            moonIcon: document.getElementById('theme-icon-moon')
        };

        this.init();
    }

    private updateTogglerIcon(theme: 'light' | 'dark'): void {
        const { sunIcon, moonIcon } = this.elements;

        if (sunIcon && moonIcon) {
            if (theme === 'dark') {
                sunIcon.style.display = 'none';
                moonIcon.style.display = 'inline-block';
            } else {
                sunIcon.style.display = 'inline-block';
                moonIcon.style.display = 'none';
            }
        }
    }

    private applyTheme(theme: 'light' | 'dark'): void {
        const { bodyElement, documentElement } = this.elements;

        // Limpa classes antigas de ambos os elementos
        bodyElement.classList.remove(this.LIGHT_THEME_CLASS, this.DARK_THEME_CLASS);
        documentElement.classList.remove(this.LIGHT_THEME_CLASS, this.DARK_THEME_CLASS);

        if (theme === 'dark') {
            bodyElement.classList.add(this.DARK_THEME_CLASS);
            documentElement.classList.add(this.DARK_THEME_CLASS);
        } else {
            bodyElement.classList.add(this.LIGHT_THEME_CLASS);
            documentElement.classList.add(this.LIGHT_THEME_CLASS);
        }

        this.updateTogglerIcon(theme);
        localStorage.setItem(this.THEME_KEY, theme);
        console.log(`Tema aplicado: ${theme}`);

        // Atualiza o ícone do navbar-toggler dinamicamente
        this.updateNavbarTogglerIcon();
    }

    private updateNavbarTogglerIcon(): void {
        const navbarTogglerIcon = document.querySelector('.navbar-toggler-icon') as HTMLElement;
        if (navbarTogglerIcon) {
            const strokeColor = getComputedStyle(this.elements.documentElement)
                .getPropertyValue('--navbar-toggler-icon-color')
                .trim() || 'rgba(255, 255, 255, 0.55)';

            navbarTogglerIcon.style.backgroundImage =
                `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3e%3cpath stroke='${strokeColor}' stroke-linecap='round' stroke-miterlimit='10' stroke-width='2' d='M4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e")`;
        }
    }

    private handleThemeToggle = (): void => {
        const currentTheme = localStorage.getItem(this.THEME_KEY) ||
            (this.elements.bodyElement.classList.contains(this.DARK_THEME_CLASS) ? 'dark' : 'light');

        const newTheme: 'light' | 'dark' = currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
    };

    private handleSystemThemeChange = (event: MediaQueryListEvent): void => {
        // Só muda se o usuário não tiver uma preferência explícita salva no localStorage
        if (!localStorage.getItem(this.THEME_KEY)) {
            const newColorScheme: 'light' | 'dark' = event.matches ? 'dark' : 'light';
            this.applyTheme(newColorScheme);
        }
    };

    private applyInitialTheme(): void {
        const savedTheme = localStorage.getItem(this.THEME_KEY) as 'light' | 'dark' | null;
        const prefersDarkScheme = window.matchMedia &&
            window.matchMedia('(prefers-color-scheme: dark)').matches;

        if (savedTheme) {
            this.applyTheme(savedTheme);
        } else if (prefersDarkScheme) {
            this.applyTheme('dark');
        } else {
            this.applyTheme('light'); // Tema claro como padrão
        }
    }

    private setupEventListeners(): void {
        if (this.elements.themeToggleButton) {
            this.elements.themeToggleButton.addEventListener('click', this.handleThemeToggle);
        }

        // Listener para mudanças na preferência de tema do sistema
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)')
                .addEventListener('change', this.handleSystemThemeChange);
        }
    }

    private init(): void {
        this.applyInitialTheme();
        this.setupEventListeners();
        console.log("ThemeManager inicializado com sucesso.");
    }

    // Método público para aplicar tema programaticamente
    public setTheme(theme: 'light' | 'dark'): void {
        this.applyTheme(theme);
    }

    // Método público para obter tema atual
    public getCurrentTheme(): 'light' | 'dark' {
        return localStorage.getItem(this.THEME_KEY) as 'light' | 'dark' ||
            (this.elements.bodyElement.classList.contains(this.DARK_THEME_CLASS) ? 'dark' : 'light');
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new ThemeManager();
});

export default ThemeManager; 