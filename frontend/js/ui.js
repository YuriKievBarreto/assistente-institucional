// ── INTERFACE DE MENSAGENS ────────────────────────────────────

import { BOT_AVATAR, USER_AVATAR, chatBox } from './constants.js';

function formatMessageHtml(html) {
    if (!html) return '';

    // Converter URLs soltas (http://, https://) que não estão dentro de tags <a> para links <a>
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;

    // Ajustar todas as tags <a> para abrir em nova aba e ter a relação de segurança adequada
    const links = tempDiv.querySelectorAll('a');
    links.forEach(a => {
        a.setAttribute('target', '_blank');
        a.setAttribute('rel', 'noopener noreferrer');
    });

    return tempDiv.innerHTML;
}

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
            row.classList.add('message-row', 'bot');
            row.innerHTML = `${BOT_AVATAR}<div class="message bot-msg">${formatMessageHtml(msg.content)}</div>`;
        }
        chatBox.appendChild(row);
    });

    chatBox.scrollTop = chatBox.scrollHeight;
}

export function addBotMessage(text) {
    const empty = chatBox.querySelector('.empty-state');
    if (empty) empty.remove();

    const row = document.createElement('div');
    row.classList.add('message-row', 'bot');
    row.innerHTML = `${BOT_AVATAR}<div class="message bot-msg">${formatMessageHtml(text)}</div>`;
    chatBox.appendChild(row);
    chatBox.scrollTop = chatBox.scrollHeight;
}

export function createBotMessagePlaceholder() {
    const empty = chatBox.querySelector('.empty-state');
    if (empty) empty.remove();

    const row = document.createElement('div');
    row.classList.add('message-row', 'bot');
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', 'bot-msg');
    row.innerHTML = BOT_AVATAR;
    row.appendChild(msgDiv);
    chatBox.appendChild(row);
    chatBox.scrollTop = chatBox.scrollHeight;

    let fullText = '';

    return {
        appendChunk: (chunk) => {
            fullText += chunk;
            msgDiv.innerHTML = formatMessageHtml(fullText);
            chatBox.scrollTop = chatBox.scrollHeight;
        },
        getText: () => fullText,
        remove: () => row.remove()
    };
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