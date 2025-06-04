// app/static/js/script.js
document.addEventListener('DOMContentLoaded', function () {
    // Lógica para alternância de tema
    const themeToggleButton = document.getElementById('theme-toggle-button');
    const bodyElement = document.body;
    const documentElement = document.documentElement; // Para aplicar a classe no <html> também
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');

    const THEME_KEY = 'themePreference';
    const LIGHT_THEME_CLASS = 'light-theme';
    const DARK_THEME_CLASS = 'dark-theme';

    function updateTogglerIcon(theme) {
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

    function applyTheme(theme) {
        // Limpa classes antigas de ambos os elementos
        bodyElement.classList.remove(LIGHT_THEME_CLASS, DARK_THEME_CLASS);
        documentElement.classList.remove(LIGHT_THEME_CLASS, DARK_THEME_CLASS);

        if (theme === 'dark') {
            bodyElement.classList.add(DARK_THEME_CLASS);
            documentElement.classList.add(DARK_THEME_CLASS);
        } else {
            bodyElement.classList.add(LIGHT_THEME_CLASS);
            documentElement.classList.add(LIGHT_THEME_CLASS);
        }
        updateTogglerIcon(theme);
        localStorage.setItem(THEME_KEY, theme);
        console.log(`Tema aplicado: ${theme}`);

        // Atualiza o ícone do navbar-toggler dinamicamente
        const navbarTogglerIcon = document.querySelector('.navbar-toggler-icon');
        if (navbarTogglerIcon) {
            const strokeColor = getComputedStyle(documentElement).getPropertyValue('--navbar-toggler-icon-color').trim() || 'rgba(255, 255, 255, 0.55)';
            navbarTogglerIcon.style.backgroundImage = `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3e%3cpath stroke='${strokeColor}' stroke-linecap='round' stroke-miterlimit='10' stroke-width='2' d='M4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e")`;
        }
    }

    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', () => {
            // Verifica a classe no body ou no localStorage para decidir qual tema aplicar
            const currentTheme = localStorage.getItem(THEME_KEY) || (bodyElement.classList.contains(DARK_THEME_CLASS) ? 'dark' : 'light');
            if (currentTheme === 'dark') {
                applyTheme('light');
            } else {
                applyTheme('dark');
            }
        });
    }

    // Aplica o tema inicial ao carregar a página
    const savedTheme = localStorage.getItem(THEME_KEY);
    const prefersDarkScheme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme) {
        applyTheme(savedTheme);
    } else if (prefersDarkScheme) {
        applyTheme('dark');
    } else {
        applyTheme('light'); // Tema claro como padrão se nada estiver definido
    }

    // Listener para mudanças na preferência de tema do sistema
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
            // Só muda se o usuário não tiver uma preferência explícita salva no localStorage
            if (!localStorage.getItem(THEME_KEY)) {
                const newColorScheme = event.matches ? "dark" : "light";
                applyTheme(newColorScheme);
            }
        });
    }

    // Adicione aqui qualquer outra lógica global do seu script.js original, se houver.
    // Por exemplo, a lógica de CONFIG e DOMElements do seu script.js anterior
    // NÃO deve estar aqui se ela é específica para a index_page.js.
    // Mantenha este script.js para funcionalidades globais como o theme switcher.

    console.log("script.js carregado e funcionalidade de tema inicializada.");
});