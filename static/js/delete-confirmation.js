/**
 * Sistema Profissional de Confirmação de Exclusão
 * JT Sistemas - Professional Delete Confirmation System
 */

class DeleteConfirmationSystem {
    constructor() {
        this.init();
    }

    init() {
        this.createModalHTML();
        this.bindEvents();
    }

    createModalHTML() {
        const modalHTML = `
            <div class="modal fade" id="deleteConfirmationModal" tabindex="-1" aria-labelledby="deleteConfirmationModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="deleteConfirmationModalLabel">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                Confirmar Exclusão
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="delete-confirmation">
                                <div class="warning-icon">
                                    <i class="fas fa-exclamation-triangle"></i>
                                </div>
                                <h4 id="deleteTitle">Tem certeza?</h4>
                                <p id="deleteMessage">Esta ação não pode ser desfeita.</p>
                                <div class="entity-info" id="entityInfo" style="display: none;">
                                    <strong id="entityName"></strong>
                                    <div id="entityDetails"></div>
                                </div>
                                <div id="referenceWarning" style="display: none;" class="alert alert-danger mt-3">
                                    <i class="fas fa-link me-2"></i>
                                    <strong>Atenção:</strong> Este item está sendo usado por outros registros e não pode ser excluído.
                                    <div id="referenceDetails" class="mt-2"></div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times me-1"></i>Cancelar
                            </button>
                            <button type="button" class="btn btn-danger" id="confirmDeleteBtn">
                                <i class="fas fa-trash me-1"></i>Excluir
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Loading Overlay -->
            <div class="loading-overlay" id="loadingOverlay" style="display: none;">
                <div class="loading-spinner"></div>
            </div>
        `;

        // Adicionar o modal ao body se não existir
        if (!document.getElementById('deleteConfirmationModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
    }

    bindEvents() {
        // Bind para todos os botões de exclusão
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-delete-action]') || e.target.closest('[data-delete-action]')) {
                e.preventDefault();
                const button = e.target.matches('[data-delete-action]') ? e.target : e.target.closest('[data-delete-action]');
                this.showDeleteConfirmation(button);
            }
        });

        // Bind para o botão de confirmação
        document.addEventListener('click', (e) => {
            if (e.target.matches('#confirmDeleteBtn')) {
                this.executeDelete();
            }
        });
    }

    async showDeleteConfirmation(button) {
        const entityType = button.dataset.entityType || 'item';
        const entityName = button.dataset.entityName || '';
        const entityId = button.dataset.entityId;
        const deleteUrl = button.dataset.deleteAction;
        const checkUrl = button.dataset.checkReferences;

        // Armazenar informações para uso posterior
        this.currentDeleteData = {
            entityType,
            entityName,
            entityId,
            deleteUrl,
            checkUrl
        };

        // Atualizar conteúdo do modal
        document.getElementById('deleteTitle').textContent = `Excluir ${entityType}?`;
        document.getElementById('deleteMessage').textContent = `Você tem certeza que deseja excluir este ${entityType.toLowerCase()}? Esta ação não pode ser desfeita.`;

        // Mostrar informações da entidade
        if (entityName) {
            const entityInfo = document.getElementById('entityInfo');
            const entityNameEl = document.getElementById('entityName');
            entityNameEl.textContent = entityName;
            entityInfo.style.display = 'block';
        }

        // Verificar referências se uma URL foi fornecida
        if (checkUrl) {
            await this.checkReferences(checkUrl);
        }

        // Mostrar o modal
        const modal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'));
        modal.show();
    }

    async checkReferences(checkUrl) {
        try {
            this.showLoading(true);
            
            const response = await fetch(checkUrl);
            const data = await response.json();

            const referenceWarning = document.getElementById('referenceWarning');
            const confirmBtn = document.getElementById('confirmDeleteBtn');

            if (!data.can_delete) {
                // Mostrar aviso de referências
                referenceWarning.style.display = 'block';
                
                const referenceDetails = document.getElementById('referenceDetails');
                const references = data.references;
                const messages = [];

                if (references.funcionarios > 0) {
                    messages.push(`${references.funcionarios} funcionário(s)`);
                }
                if (references.agendamentos > 0) {
                    messages.push(`${references.agendamentos} agendamento(s)`);
                }

                referenceDetails.innerHTML = `Este ${this.currentDeleteData.entityType.toLowerCase()} está sendo usado por: ${messages.join(', ')}.`;
                
                // Desabilitar botão de confirmação
                confirmBtn.disabled = true;
                confirmBtn.innerHTML = '<i class="fas fa-ban me-1"></i>Não é possível excluir';
                confirmBtn.classList.remove('btn-danger');
                confirmBtn.classList.add('btn-secondary');
            } else {
                // Esconder aviso e habilitar botão
                referenceWarning.style.display = 'none';
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = '<i class="fas fa-trash me-1"></i>Excluir';
                confirmBtn.classList.remove('btn-secondary');
                confirmBtn.classList.add('btn-danger');
            }

        } catch (error) {
            console.error('Erro ao verificar referências:', error);
            // Em caso de erro, permitir exclusão (fallback)
            document.getElementById('referenceWarning').style.display = 'none';
        } finally {
            this.showLoading(false);
        }
    }

    async executeDelete() {
        if (!this.currentDeleteData) return;

        try {
            this.showLoading(true);

            // Criar formulário para envio POST
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = this.currentDeleteData.deleteUrl;
            
            // Adicionar token CSRF se existir
            const csrfToken = document.querySelector('meta[name=csrf-token]');
            if (csrfToken) {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrf_token';
                csrfInput.value = csrfToken.getAttribute('content');
                form.appendChild(csrfInput);
            }

            document.body.appendChild(form);
            form.submit();

        } catch (error) {
            console.error('Erro ao executar exclusão:', error);
            this.showToast('Erro ao executar exclusão', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }

    showToast(message, type = 'info') {
        // Criar container de toast se não existir
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        const toastId = 'toast-' + Date.now();
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        const toastHTML = `
            <div class="toast toast-${type}" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="${iconMap[type]} me-2"></i>
                    <strong class="me-auto">Sistema</strong>
                    <small>agora</small>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHTML);

        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();

        // Remover o toast após ser ocultado
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

// Inicializar o sistema quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new DeleteConfirmationSystem();
});