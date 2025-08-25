/**
 * Fix para dropdowns das tabelas - Posicionamento correto
 */

document.addEventListener('DOMContentLoaded', function() {
    // Interceptar todos os cliques em botões dropdown das tabelas
    document.addEventListener('click', function(e) {
        const dropdownButton = e.target.closest('.professional-table .dropdown-toggle');
        if (dropdownButton) {
            e.preventDefault();
            e.stopPropagation();
            
            // Fechar outros dropdowns primeiro
            document.querySelectorAll('.professional-table .dropdown-menu.show').forEach(menu => {
                menu.classList.remove('show');
            });
            
            // Encontrar o menu correspondente
            const dropdown = dropdownButton.closest('.dropdown');
            const menu = dropdown.querySelector('.dropdown-menu');
            
            if (menu) {
                // Posicionar o menu usando coordenadas fixas
                const buttonRect = dropdownButton.getBoundingClientRect();
                const menuWidth = 280;
                const menuHeight = menu.scrollHeight || 200;
                
                // Calcular posição ideal
                let left = buttonRect.right - menuWidth;
                let top = buttonRect.bottom + 5;
                
                // Ajustar se sair da tela
                if (left < 10) {
                    left = buttonRect.left;
                }
                if (left + menuWidth > window.innerWidth - 10) {
                    left = window.innerWidth - menuWidth - 10;
                }
                if (top + menuHeight > window.innerHeight - 10) {
                    top = buttonRect.top - menuHeight - 5;
                }
                if (top < 10) {
                    top = 10;
                }
                
                // Aplicar posição
                menu.style.left = left + 'px';
                menu.style.top = top + 'px';
                menu.style.right = 'auto';
                menu.style.bottom = 'auto';
                
                // Mostrar o menu
                menu.classList.add('show');
                
                // Adicionar listener para fechar ao clicar fora
                setTimeout(() => {
                    document.addEventListener('click', closeDropdownOnClickOutside, { once: true });
                }, 10);
            }
        }
    });
    
    function closeDropdownOnClickOutside(e) {
        if (!e.target.closest('.professional-table .dropdown')) {
            document.querySelectorAll('.professional-table .dropdown-menu.show').forEach(menu => {
                menu.classList.remove('show');
            });
        } else {
            // Se clicou dentro do dropdown, manter listener ativo
            setTimeout(() => {
                document.addEventListener('click', closeDropdownOnClickOutside, { once: true });
            }, 10);
        }
    }
    
    // Fechar dropdowns ao pressionar ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.professional-table .dropdown-menu.show').forEach(menu => {
                menu.classList.remove('show');
            });
        }
    });
    
    // Reposicionar dropdowns ao fazer scroll
    window.addEventListener('scroll', function() {
        document.querySelectorAll('.professional-table .dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
    });
    
    // Fechar dropdowns ao redimensionar janela
    window.addEventListener('resize', function() {
        document.querySelectorAll('.professional-table .dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
    });
});