// ── ENTRY POINT ───────────────────────────────────────────────
// Lembre-se: no HTML, a tag <script> deve usar type="module":
//   <script type="module" src="script.js"></script>

import { chatBox, userInput } from './constants.js';
import { trocarAba, abrirModalAuth, fecharModalAuth } from './modal.js';
import { fazerLogin, fazerRegister, isLoggedIn, atualizarPerfilUI, verificarSessao } from './auth.js';
import { renderizarSidebar } from './chat.js';

async function init() {
    chatBox.innerHTML = `
        <div class="empty-state">
            <i class="ti ti-message-circle"></i>
            <p>Digite uma mensagem para começar ou selecione uma conversa</p>
        </div>`;

    renderizarSidebar();
    await verificarSessao()

    // ── Modal ──────────────────────────────────────────────────
    document.getElementById('tab-login').addEventListener('click', () => trocarAba('login'));
    document.getElementById('tab-register').addEventListener('click', () => trocarAba('register'));
    document.getElementById('form-login').addEventListener('submit', fazerLogin);
    document.getElementById('form-register').addEventListener('submit', fazerRegister);
    document.getElementById('modal-close').addEventListener('click', fecharModalAuth);
    document.getElementById('modal-auth').addEventListener('click', (e) => {
        if (e.target === document.getElementById('modal-auth')) fecharModalAuth();
    });

    // ── Perfil ─────────────────────────────────────────────────
    document.getElementById('profile-btn').addEventListener('click', () => {
        if (!isLoggedIn()) abrirModalAuth('login');
    });

    userInput.focus();
}

init();