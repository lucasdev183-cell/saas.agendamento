/**
 * Sistema Profissional de Tabelas Interativas
 * JT Sistemas - Professional Interactive Tables System
 */

class ProfessionalTablesSystem {
    constructor() {
        this.tables = new Map();
        this.isResizing = false;
        this.currentResizer = null;
        this.startX = 0;
        this.startWidth = 0;
        this.init();
    }

    init() {
        this.initializeTables();
        this.bindEvents();
        this.addTableStyles();
    }

    initializeTables() {
        document.querySelectorAll('.professional-table').forEach(table => {
            this.setupTable(table);
        });
    }

    setupTable(table) {
        const tableId = table.id || `table-${Date.now()}`;
        table.id = tableId;

        // Adicionar classes profissionais
        table.classList.add('table', 'table-hover', 'table-responsive-table');
        
        // Configurar cabeçalho
        this.setupTableHeader(table);
        
        // Configurar corpo da tabela
        this.setupTableBody(table);
        
        // Adicionar funcionalidades de redimensionamento
        this.makeColumnsResizable(table);
        
        // Armazenar configurações
        this.tables.set(tableId, {
            table: table,
            columnWidths: this.getColumnWidths(table),
            sortState: {},
            filterState: {}
        });
    }

    setupTableHeader(table) {
        const thead = table.querySelector('thead');
        if (!thead) return;

        thead.classList.add('table-header-professional');
        
        // Adicionar ícones de ordenação
        thead.querySelectorAll('th').forEach((th, index) => {
            if (index === 0) {
                // Primeira coluna reservada para ações, sem ícone no cabeçalho
                th.classList.add('actions-column');
                // Mantém espaço vazio conforme solicitado
                return;
            }

            if (th.dataset.sortable !== 'false') {
                th.classList.add('sortable-column');
                th.innerHTML += ' <i class="fas fa-sort sort-icon"></i>';
                th.style.cursor = 'pointer';
            }
        });
    }

    setupTableBody(table) {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        tbody.classList.add('table-body-professional');
        
        // Adicionar efeitos hover e seleção
        tbody.querySelectorAll('tr').forEach(row => {
            row.classList.add('table-row-professional');
            row.setAttribute('draggable', 'true');
            
            // Adicionar evento de hover
            row.addEventListener('mouseenter', () => {
                row.classList.add('row-hover');
            });
            
            row.addEventListener('mouseleave', () => {
                row.classList.remove('row-hover');
            });

            // Drag & Drop reordenação de linhas
            row.addEventListener('dragstart', (e) => {
                row.classList.add('row-dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', '');
                tbody._draggingRow = row;
            });

            row.addEventListener('dragover', (e) => {
                e.preventDefault();
                const dragging = tbody._draggingRow;
                if (!dragging || dragging === row) return;
                const bounding = row.getBoundingClientRect();
                const offset = e.clientY - bounding.top;
                const halfway = bounding.height / 2;
                if (offset > halfway) {
                    row.classList.add('drop-after');
                    row.classList.remove('drop-before');
                } else {
                    row.classList.add('drop-before');
                    row.classList.remove('drop-after');
                }
            });

            row.addEventListener('dragleave', () => {
                row.classList.remove('drop-before', 'drop-after');
            });

            row.addEventListener('drop', (e) => {
                e.preventDefault();
                const dragging = tbody._draggingRow;
                if (!dragging || dragging === row) return;
                const insertAfter = row.classList.contains('drop-after');
                row.classList.remove('drop-before', 'drop-after');
                if (insertAfter) {
                    row.after(dragging);
                } else {
                    row.before(dragging);
                }
            });

            row.addEventListener('dragend', () => {
                row.classList.remove('row-dragging');
                delete tbody._draggingRow;
                tbody.querySelectorAll('tr').forEach(r => r.classList.remove('drop-before', 'drop-after'));
            });
        });
    }

    makeColumnsResizable(table) {
        const thead = table.querySelector('thead tr');
        if (!thead) return;

        thead.querySelectorAll('th').forEach((th, index) => {
            // Não adicionar resizer na última coluna
            if (index === thead.children.length - 1) return;

            const resizer = document.createElement('div');
            resizer.className = 'column-resizer';
            resizer.innerHTML = '<div class="resizer-line"></div>';
            
            resizer.addEventListener('mousedown', (e) => {
                this.startResize(e, th, table);
            });

            th.style.position = 'relative';
            th.appendChild(resizer);
        });
    }

    startResize(e, column, table) {
        e.preventDefault();
        this.isResizing = true;
        this.currentResizer = e.target.closest('.column-resizer');
        this.startX = e.pageX;
        this.startWidth = parseInt(document.defaultView.getComputedStyle(column).width, 10);
        
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        
        // Adicionar overlay para capturar mouse
        const overlay = document.createElement('div');
        overlay.className = 'resize-overlay';
        document.body.appendChild(overlay);
        
        const mouseMoveHandler = (e) => this.doResize(e, column);
        const mouseUpHandler = () => this.stopResize(overlay, mouseMoveHandler, mouseUpHandler);
        
        document.addEventListener('mousemove', mouseMoveHandler);
        document.addEventListener('mouseup', mouseUpHandler);
    }

    doResize(e, column) {
        if (!this.isResizing) return;
        
        const width = this.startWidth + e.pageX - this.startX;
        const minWidth = 80; // Largura mínima
        const maxWidth = 400; // Largura máxima
        
        if (width >= minWidth && width <= maxWidth) {
            column.style.width = width + 'px';
            
            // Atualizar todas as células da coluna
            const table = column.closest('table');
            const columnIndex = Array.from(column.parentNode.children).indexOf(column);
            
            table.querySelectorAll(`tbody tr td:nth-child(${columnIndex + 1})`).forEach(cell => {
                cell.style.width = width + 'px';
            });
        }
    }

    stopResize(overlay, mouseMoveHandler, mouseUpHandler) {
        this.isResizing = false;
        this.currentResizer = null;
        
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        
        document.removeEventListener('mousemove', mouseMoveHandler);
        document.removeEventListener('mouseup', mouseUpHandler);
        
        if (overlay.parentNode) {
            overlay.parentNode.removeChild(overlay);
        }
    }

    getColumnWidths(table) {
        const widths = [];
        const thead = table.querySelector('thead tr');
        if (thead) {
            thead.querySelectorAll('th').forEach(th => {
                widths.push(th.offsetWidth);
            });
        }
        return widths;
    }

    sortTable(table, columnIndex, direction = 'asc') {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        rows.sort((a, b) => {
            const aVal = a.cells[columnIndex].textContent.trim();
            const bVal = b.cells[columnIndex].textContent.trim();
            
            // Tentar converter para número
            const aNum = parseFloat(aVal);
            const bNum = parseFloat(bVal);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return direction === 'asc' ? aNum - bNum : bNum - aNum;
            }
            
            // Comparação de string
            return direction === 'asc' 
                ? aVal.localeCompare(bVal, 'pt-BR')
                : bVal.localeCompare(aVal, 'pt-BR');
        });
        
        // Reordenar as linhas
        rows.forEach(row => tbody.appendChild(row));
        
        // Atualizar ícones de ordenação
        this.updateSortIcons(table, columnIndex, direction);
    }

    updateSortIcons(table, activeColumn, direction) {
        const thead = table.querySelector('thead');
        thead.querySelectorAll('th .sort-icon').forEach((icon, index) => {
            if (index === activeColumn) {
                icon.className = direction === 'asc' ? 'fas fa-sort-up sort-icon active' : 'fas fa-sort-down sort-icon active';
            } else {
                icon.className = 'fas fa-sort sort-icon';
            }
        });
    }

    addTableStyles() {
        if (document.getElementById('professional-tables-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'professional-tables-styles';
        styles.textContent = `
            /* Professional Tables System Styles */
            .professional-table {
                width: 100%;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border: 1px solid var(--gray-200);
                border-radius: var(--border-radius-lg);
                box-shadow: var(--shadow-lg);
                overflow: visible; /* evita clipping de dropdowns */
                font-size: 14px;
            }

            .table-header-professional {
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                position: sticky;
                top: 0;
                z-index: 10;
            }

            .table-header-professional th {
                padding: 1rem 0.75rem;
                font-weight: 700;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border: none;
                position: relative;
                white-space: nowrap;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }

            .table-header-professional th:last-child {
                border-right: none;
            }

            .actions-column {
                width: 60px !important;
                min-width: 60px !important;
                max-width: 60px !important;
                text-align: center !important;
            }

            .sortable-column:hover {
                background: rgba(255, 255, 255, 0.1);
                transition: background-color 0.2s ease;
            }

            .sort-icon {
                opacity: 0.5;
                margin-left: 0.5rem;
                font-size: 11px;
                transition: all 0.2s ease;
            }

            .sort-icon.active {
                opacity: 1;
                color: var(--primary-color);
            }

            .table-body-professional {
                background: rgba(255, 255, 255, 0.8);
            }

            .table-row-professional {
                transition: all 0.2s ease;
                border-bottom: 1px solid var(--gray-200);
            }

            .table-row-professional:hover {
                background: linear-gradient(135deg, rgba(37, 99, 235, 0.05) 0%, rgba(6, 182, 212, 0.03) 100%);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            }

            .table-row-professional td {
                padding: 1rem 0.75rem;
                vertical-align: middle;
                border: none;
                border-right: 1px solid var(--gray-200);
                font-weight: 500;
                color: var(--gray-700);
            }

            .table-row-professional td:last-child {
                border-right: none;
            }

            .table-row-professional td:first-child {
                text-align: center;
                width: 60px;
                padding: 0.5rem;
            }

            /* Drag & Drop cues */
            .table-row-professional.row-dragging {
                opacity: 0.6;
                background: rgba(37, 99, 235, 0.08);
            }
            .table-row-professional.drop-before {
                box-shadow: inset 0 4px 0 0 var(--primary-color);
            }
            .table-row-professional.drop-after {
                box-shadow: inset 0 -4px 0 0 var(--primary-color);
            }

            /* Column Resizer */
            .column-resizer {
                position: absolute;
                top: 0;
                right: -2px;
                width: 6px;
                height: 100%;
                cursor: col-resize;
                z-index: 20;
                opacity: 0.2; /* visível para facilitar interação */
                transition: opacity 0.2s ease, background-color 0.2s ease;
            }

            .column-resizer:hover,
            .column-resizer.active {
                opacity: 0.9;
            }

            .resizer-line {
                width: 2px;
                height: 100%;
                background: var(--primary-color);
                margin: 0 auto;
                border-radius: 1px;
            }

            th:hover .column-resizer {
                opacity: 0.6;
            }

            .resize-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 9999;
                cursor: col-resize;
            }

            /* Professional Action Buttons */
            .action-buttons {
                display: flex;
                gap: 0.25rem;
                justify-content: center;
                align-items: center;
            }

            .action-btn {
                width: 32px;
                height: 32px;
                border-radius: 6px;
                border: none;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                font-size: 12px;
                cursor: pointer;
            }

            .action-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            }

            .action-btn.btn-view {
                background: linear-gradient(135deg, var(--info-color) 0%, var(--info-light) 100%);
                color: white;
            }

            .action-btn.btn-edit {
                background: linear-gradient(135deg, var(--warning-color) 0%, var(--warning-light) 100%);
                color: white;
            }

            .action-btn.btn-delete {
                background: linear-gradient(135deg, var(--danger-color) 0%, var(--danger-light) 100%);
                color: white;
            }

            /* Status Badges */
            .status-badge {
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border: 2px solid transparent;
            }

            .status-badge.active {
                background: linear-gradient(135deg, var(--success-color) 0%, var(--success-light) 100%);
                color: white;
            }

            .status-badge.inactive {
                background: linear-gradient(135deg, var(--gray-400) 0%, var(--gray-500) 100%);
                color: white;
            }

            .status-badge.pending {
                background: linear-gradient(135deg, var(--warning-color) 0%, var(--warning-light) 100%);
                color: white;
            }

            /* Table Container */
            .table-container-professional {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: var(--border-radius-lg);
                padding: 1.5rem;
                box-shadow: var(--shadow-lg);
                margin-bottom: 2rem;
            }

            .table-header-actions {
                display: flex;
                justify-content: between;
                align-items: center;
                margin-bottom: 1.5rem;
                padding-bottom: 1rem;
                border-bottom: 2px solid var(--gray-200);
            }

            .table-title {
                font-size: 1.5rem;
                font-weight: 800;
                color: var(--gray-900);
                margin: 0;
            }

            .table-subtitle {
                color: var(--gray-600);
                font-size: 0.9rem;
                margin: 0;
            }

            /* Responsive */
            @media (max-width: 768px) {
                .professional-table {
                    font-size: 12px;
                }
                
                .table-header-professional th,
                .table-row-professional td {
                    padding: 0.75rem 0.5rem;
                }
                
                .action-btn {
                    width: 28px;
                    height: 28px;
                    font-size: 11px;
                }
            }

            /* Corrige clipping e sobreposição dos dropdowns de ações */
            .table-responsive { overflow-y: visible; }
            .professional-table .dropdown-menu {
                z-index: 5000; /* acima de toggles e cabeçalhos */
                min-width: 220px;
                font-size: 14px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            }
            .professional-table .dropdown-toggle { position: relative; z-index: 1000; }
            .professional-table .table-row-professional { position: relative; z-index: 1; }
            .professional-table .dropdown-item { padding: 0.5rem 0.75rem; }

            /* Evitar clipping por containers */
            .card, .content-wrapper, .table-responsive { overflow: visible; }
        `;
        
        document.head.appendChild(styles);
    }

    bindEvents() {
        // Evento para ordenação
        document.addEventListener('click', (e) => {
            if (e.target.closest('.sortable-column')) {
                const th = e.target.closest('.sortable-column');
                const table = th.closest('table');
                const columnIndex = Array.from(th.parentNode.children).indexOf(th);
                
                // Determinar direção da ordenação
                const currentDirection = th.dataset.sortDirection || 'asc';
                const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
                th.dataset.sortDirection = newDirection;
                
                this.sortTable(table, columnIndex, newDirection);
            }
        });

        // Auto-inicializar novas tabelas
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        const tables = node.querySelectorAll ? node.querySelectorAll('.professional-table') : [];
                        tables.forEach(table => {
                            if (!this.tables.has(table.id)) {
                                this.setupTable(table);
                            }
                        });
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
}

// Inicializar o sistema quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.professionalTables = new ProfessionalTablesSystem();
});