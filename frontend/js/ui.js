// ── INTERFACE DE MENSAGENS ────────────────────────────────────

import { BOT_AVATAR, USER_AVATAR, chatBox } from './constants.js';

export function renderizarMensagens(messages) {
    chatBox.innerHTML = '';

    if (!messages || messages.length === 0) {
        chatBox.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-message-circle"></i>
                <p>Envie uma mensagem para começar</p>
            </div>`;
        return;
    }

    messages.forEach(msg => {
        const row = document.createElement('div');
        if (msg.role === 'human') {
            row.classList.add('message-row', 'user');
            row.innerHTML = `${USER_AVATAR}<div class="message user-msg">${msg.content}</div>`;
        } else {
            row.classList.add('message-row');
            row.innerHTML = `${BOT_AVATAR}<div class="message bot-msg">${msg.content}</div>`;
        }
        chatBox.appendChild(row);
    });

    chatBox.scrollTop = chatBox.scrollHeight;
}

export function addBotMessage(text) {
    const empty = chatBox.querySelector('.empty-state');
    if (empty) empty.remove();

    const row = document.createElement('div');
    row.classList.add('message-row');
    row.innerHTML = `${BOT_AVATAR}<div class="message bot-msg">${text}</div>`;
    chatBox.appendChild(row);
    chatBox.scrollTop = chatBox.scrollHeight;
}

export function showTyping() {
    const row = document.createElement('div');
    row.classList.add('message-row');
    row.id = 'typing';
    row.innerHTML = `${BOT_AVATAR}<div class="typing-indicator"><span></span><span></span><span></span></div>`;
    chatBox.appendChild(row);
    chatBox.scrollTop = chatBox.scrollHeight;
}

export function hideTyping() {
    const el = document.getElementById('typing');
    if (el) el.remove();
}