// ── ENTRY POINT ───────────────────────────────────────────────
// Lembre-se: no HTML, a tag <script> deve usar type="module":
//   <script type="module" src="script.js"></script>

import { chatBox, userInput } from './js/constants.js';
import { trocarAba, abrirModalAuth, fecharModalAuth } from './js/modal.js';
import { fazerLogin, fazerRegister, isLoggedIn, atualizarPerfilUI, verificarSessao } from './js/auth.js';
import { renderizarSidebar, novaConversa } from './js/chat.js';
import { initTheme } from './js/theme.js';
import { initCopyButtons } from './js/copyMessage.js';

async function init() {
    chatBox.innerHTML = `
        <div class="empty-state">
            <i class="ti ti-message-circle"></i>
            <p>Digite uma mensagem para começar ou selecione uma conversa</p>
        </div>`;

    await verificarSessao(); // já carrega chats e renderiza sidebar internamente
    initTheme()
    initCopyButtons()

    // ── Modal ──────────────────────────────────────────────────
    document.getElementById('tab-login').addEventListener('click', () => trocarAba('login'));
    document.getElementById('new-chat-btn').addEventListener('click', novaConversa);
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