/**
 * JT Sistemas - Table Dropdowns Manager
 * Handles dropdown positioning, visibility, and interactions in professional tables
 */

class TableDropdownManager {
    constructor() {
        this.activeDropdown = null;
        this.init();
    }

    init() {
        this.setupDropdownListeners();
        this.setupClickOutsideHandler();
        this.setupKeyboardHandlers();
        this.setupScrollHandler();
    }

    /**
     * Setup dropdown button listeners
     */
    setupDropdownListeners() {
        document.addEventListener('click', (e) => {
            const dropdownButton = e.target.closest('.dropdown-toggle');
            if (dropdownButton) {
                e.preventDefault();
                e.stopPropagation();
                this.toggleDropdown(dropdownButton);
            }
        });
    }

    /**
     * Toggle dropdown visibility with proper positioning
     */
    toggleDropdown(button) {
        const dropdown = button.closest('.dropdown');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (!menu) return;

        // Close other dropdowns first
        this.closeAllDropdowns();

        // Toggle current dropdown
        const isShown = menu.classList.contains('show');
        
        if (!isShown) {
            this.showDropdown(dropdown, button, menu);
        }
    }

    /**
     * Show dropdown with smart positioning
     */
    showDropdown(dropdown, button, menu) {
        // Add show class
        menu.classList.add('show');
        button.setAttribute('aria-expanded', 'true');
        
        // Calculate optimal position
        this.positionDropdown(button, menu);
        
        // Set as active dropdown
        this.activeDropdown = dropdown;
        
        // Add animation class
        setTimeout(() => {
            menu.style.opacity = '1';
            menu.style.visibility = 'visible';
            menu.style.transform = 'translateY(0)';
        }, 10);
    }

    /**
     * Position dropdown intelligently to avoid viewport edges
     */
    positionDropdown(button, menu) {
        const buttonRect = button.getBoundingClientRect();
        const menuWidth = 280; // Match CSS min-width
        const menuHeight = menu.scrollHeight || 250;
        const viewport = {
            width: window.innerWidth,
            height: window.innerHeight
        };
        
        // Calculate initial position (below button, aligned to right)
        let left = buttonRect.right - menuWidth;
        let top = buttonRect.bottom + 8;
        
        // Adjust horizontal position if menu would go off-screen
        if (left < 10) {
            left = buttonRect.left; // Align to left edge of button
        }
        if (left + menuWidth > viewport.width - 10) {
            left = viewport.width - menuWidth - 10;
        }
        
        // Adjust vertical position if menu would go off-screen
        if (top + menuHeight > viewport.height - 10) {
            top = buttonRect.top - menuHeight - 8; // Show above button
        }
        
        // Ensure menu doesn't go above viewport
        if (top < 10) {
            top = 10;
        }
        
        // Apply position
        menu.style.left = `${left}px`;
        menu.style.top = `${top}px`;
    }

    /**
     * Close all open dropdowns
     */
    closeAllDropdowns() {
        const openMenus = document.querySelectorAll('.professional-table .dropdown-menu.show');
        
        openMenus.forEach(menu => {
            const dropdown = menu.closest('.dropdown');
            const button = dropdown.querySelector('.dropdown-toggle');
            
            menu.style.opacity = '0';
            menu.style.visibility = 'hidden';
            menu.style.transform = 'translateY(5px)';
            
            setTimeout(() => {
                menu.classList.remove('show');
                if (button) {
                    button.setAttribute('aria-expanded', 'false');
                }
            }, 200);
        });
        
        this.activeDropdown = null;
    }

    /**
     * Setup click outside handler
     */
    setupClickOutsideHandler() {
        document.addEventListener('click', (e) => {
            // Don't close if clicking inside a dropdown menu
            if (e.target.closest('.dropdown-menu')) {
                return;
            }
            
            // Don't close if clicking a dropdown button (handled separately)
            if (e.target.closest('.dropdown-toggle')) {
                return;
            }
            
            // Close all dropdowns
            this.closeAllDropdowns();
        });
    }

    /**
     * Setup keyboard handlers
     */
    setupKeyboardHandlers() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllDropdowns();
            }
            
            // Handle arrow navigation within dropdown
            if (this.activeDropdown && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
                e.preventDefault();
                this.navigateDropdown(e.key === 'ArrowDown');
            }
            
            // Handle Enter key
            if (this.activeDropdown && e.key === 'Enter') {
                const focused = this.activeDropdown.querySelector('.dropdown-item:focus');
                if (focused) {
                    focused.click();
                }
            }
        });
    }

    /**
     * Navigate dropdown items with keyboard
     */
    navigateDropdown(down) {
        const menu = this.activeDropdown.querySelector('.dropdown-menu');
        const items = menu.querySelectorAll('.dropdown-item:not(.disabled)');
        const currentIndex = Array.from(items).findIndex(item => item === document.activeElement);
        
        let nextIndex;
        if (currentIndex === -1) {
            nextIndex = down ? 0 : items.length - 1;
        } else {
            nextIndex = down 
                ? (currentIndex + 1) % items.length
                : (currentIndex - 1 + items.length) % items.length;
        }
        
        items[nextIndex].focus();
    }

    /**
     * Setup scroll handler to reposition dropdowns
     */
    setupScrollHandler() {
        let scrollTimeout;
        
        window.addEventListener('scroll', () => {
            if (this.activeDropdown) {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    const button = this.activeDropdown.querySelector('.dropdown-toggle');
                    const menu = this.activeDropdown.querySelector('.dropdown-menu');
                    if (button && menu && menu.classList.contains('show')) {
                        this.positionDropdown(button, menu);
                    }
                }, 10);
            }
        }, { passive: true });
        
        // Also handle window resize
        window.addEventListener('resize', () => {
            this.closeAllDropdowns();
        });
    }

    /**
     * Add loading state to dropdown item
     */
    setItemLoading(item, loading = true) {
        if (loading) {
            const originalContent = item.innerHTML;
            item.dataset.originalContent = originalContent;
            item.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processando...';
            item.style.pointerEvents = 'none';
        } else {
            if (item.dataset.originalContent) {
                item.innerHTML = item.dataset.originalContent;
                delete item.dataset.originalContent;
            }
            item.style.pointerEvents = '';
        }
    }

    /**
     * Show confirmation for dangerous actions
     */
    confirmAction(message, callback) {
        // Create modern confirmation modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-gradient-danger text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Confirmar Ação
                        </h5>
                    </div>
                    <div class="modal-body text-center">
                        <div class="delete-confirmation">
                            <i class="fas fa-exclamation-triangle warning-icon"></i>
                            <h4>Atenção!</h4>
                            <p>${message}</p>
                            <div class="alert alert-warning">
                                <strong>Esta ação não pode ser desfeita.</strong>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-1"></i>Cancelar
                        </button>
                        <button type="button" class="btn btn-danger confirm-btn">
                            <i class="fas fa-trash me-1"></i>Confirmar Exclusão
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Initialize Bootstrap modal
        const bsModal = new bootstrap.Modal(modal);
        
        // Handle confirmation
        modal.querySelector('.confirm-btn').addEventListener('click', () => {
            bsModal.hide();
            callback();
        });
        
        // Clean up when modal is hidden
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
        
        bsModal.show();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.tableDropdownManager = new TableDropdownManager();
});

// Export for global access
window.TableDropdownManager = TableDropdownManager;