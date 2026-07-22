import { chatBox } from './constants.js';

function criarBotaoCopiar(botMsgEl) {
    if (botMsgEl.querySelector('.message-actions')) return; // já tem

    const actions = document.createElement('div');
    actions.className = 'message-actions';
    actions.innerHTML = `
        <button class="message-action-btn" type="button" title="Copiar resposta" data-action="copy">
            <i class="ti ti-copy" aria-hidden="true"></i>
        </button>
    `;
    botMsgEl.appendChild(actions);
}

function copiarTexto(botao) {
    const msgEl = botao.closest('.bot-msg');
    if (!msgEl) return;

    // clona pra remover o próprio botão do texto copiado
    const clone = msgEl.cloneNode(true);
    clone.querySelector('.message-actions')?.remove();
    const texto = clone.innerText.trim();

    navigator.clipboard.writeText(texto).then(() => {
        const icon = botao.querySelector('i');
        const original = icon.className;
        icon.className = 'ti ti-check';
        botao.disabled = true;
        setTimeout(() => {
            icon.className = original;
            botao.disabled = false;
        }, 1500);
    });
}

export function initCopyButtons() {
    if (!chatBox) return;

    // mensagens que já estiverem no DOM ao iniciar
    chatBox.querySelectorAll('.bot-msg').forEach(criarBotaoCopiar);

    // novas mensagens que o chat.js/ui.js inserir depois
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType !== 1) return;
                if (node.classList?.contains('bot-msg')) {
                    criarBotaoCopiar(node);
                }
                node.querySelectorAll?.('.bot-msg').forEach(criarBotaoCopiar);
            });
        }
    });
    observer.observe(chatBox, { childList: true, subtree: true });

    // um listener só, delegado, em vez de um por botão
    chatBox.addEventListener('click', (event) => {
        const botao = event.target.closest('[data-action="copy"]');
        if (botao) copiarTexto(botao);
    });
}