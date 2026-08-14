// ── CHAT ─────────────────────────────────────────────────────

import { API_BASE, chatForm, chatBox, userInput, sendBtn, USER_AVATAR } from './constants.js';
import { carregarTodosChats, salvarTodosChats, buscarChat, salvarMensagem, gerarId, gerarTitulo } from './storage.js';
import { renderizarMensagens, addBotMessage, createBotMessagePlaceholder, showTyping, hideTyping } from './ui.js';
import { authHeaders } from './auth.js';

// ── ESTADO ───────────────────────────────────────────────────

let currentChatId = null;

export function getCurrentChatId() {
    return currentChatId;
}

// ── SIDEBAR ──────────────────────────────────────────────────

export function renderizarSidebar() {
    const chats     = carregarTodosChats();
    const container = document.getElementById('chat-history');
    container.innerHTML = '';

    if (chats.length === 0) {
        container.innerHTML = `<div style="padding:12px 14px;font-size:12px;color:#ffffff30;">Nenhuma conversa ainda</div>`;
        return;
    }

    [...chats].reverse().forEach(chat => {
        const item = document.createElement('div');
        item.className = 'history-item' + (chat.id === currentChatId ? ' active' : '');
        item.innerHTML = `
            <i class="ti ti-message" aria-hidden="true"></i>
            <span class="history-item-text">${chat.title}</span>
            <button class="history-item-delete" title="Excluir conversa" data-id="${chat.id}">
                <i class="ti ti-x"></i>
            </button>
        `;
        item.addEventListener('click', () => abrirChat(chat.id));
        item.querySelector('.history-item-delete').addEventListener('click', (e) => {
            e.stopPropagation();
            excluirChat(chat.id);
        });
        container.appendChild(item);
    });
}

// ── AÇÕES ────────────────────────────────────────────────────

export function novaConversa() {
    const id    = gerarId();
    const chats = carregarTodosChats();
    chats.push({ id, title: 'Nova conversa', messages: [], created_at: new Date().toISOString() });
    salvarTodosChats(chats);
    abrirChat(id);
}

export function abrirChat(id) {
    currentChatId = id;
    const chat = buscarChat(id);
    renderizarMensagens(chat ? chat.messages : []);
    renderizarSidebar();
    userInput.focus();
}

export function excluirChat(id) {
    let chats = carregarTodosChats().filter(c => c.id !== id);
    salvarTodosChats(chats);

    if (currentChatId === id) {
        currentChatId = chats.length > 0 ? chats[chats.length - 1].id : null;
        if (currentChatId) {
            abrirChat(currentChatId);
        } else {
            chatBox.innerHTML = `
                <div class="empty-state">
                    <i class="ti ti-message-circle"></i>
                    <p>Crie uma nova conversa para começar</p>
                </div>`;
        }
    }

    renderizarSidebar();
}

// ── ENVIO ─────────────────────────────────────────────────────

async function enviarMensagem(textoDoUsuario, onChunk) {
    try {
        const chat = buscarChat(currentChatId);
        const history = chat ? chat.messages.slice(0, -1).map(msg => ({
            role: msg.role,
            content: msg.content,
            created_at: msg.created_at
        })) : [];

        console.log(textoDoUsuario, currentChatId, history);

        const resposta = await fetch(`${API_BASE}/chat/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                query: textoDoUsuario,
                session_id: currentChatId,
                history,
                title: chat.title
            })
        });

        if (!resposta.ok) {
            throw new Error(`Erro no servidor: ${resposta.status}`);
        }

        const reader = resposta.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let fullText = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            fullText += chunk;
            if (onChunk) {
                onChunk(chunk);
            }
        }

        return fullText;
    } catch (erro) {
        console.error('Erro ao conectar com o servidor:', erro);
        throw erro;
    }
}

// ── HANDLER DO FORMULÁRIO ─────────────────────────────────────

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const messageText = userInput.value.trim();
    if (!messageText) return;

    if (!currentChatId) novaConversa();

    const chats = carregarTodosChats();
    const chat  = chats.find(c => c.id === currentChatId);
    if (chat && chat.title === 'Nova conversa') {
        chat.title = gerarTitulo(messageText);
        salvarTodosChats(chats);
    }

    salvarMensagem(currentChatId, 'human', messageText);

    const empty = chatBox.querySelector('.empty-state');
    if (empty) empty.remove();

    const userRow = document.createElement('div');
    userRow.classList.add('message-row', 'user');
    userRow.innerHTML = `${USER_AVATAR}<div class="message user-msg">${messageText}</div>`;
    chatBox.appendChild(userRow);
    chatBox.scrollTop = chatBox.scrollHeight;

    userInput.value    = '';
    userInput.disabled = true;
    sendBtn.disabled   = true;

    renderizarSidebar();
    showTyping();

    let botPlaceholder = null;
    let fullResponse = '';

    try {
        fullResponse = await enviarMensagem(messageText, (chunk) => {
            if (!botPlaceholder) {
                hideTyping();
                botPlaceholder = createBotMessagePlaceholder();
            }
            botPlaceholder.appendChunk(chunk);
        });

        if (fullResponse) {
            salvarMensagem(currentChatId, 'ai', fullResponse);
        } else if (botPlaceholder) {
            salvarMensagem(currentChatId, 'ai', botPlaceholder.getText());
        }
    } catch (erro) {
        hideTyping();
        if (botPlaceholder) {
            botPlaceholder.remove();
        }
        addBotMessage('Não foi possível conectar com o servidor. Tente novamente.');
    } finally {
        hideTyping();
        userInput.disabled = false;
        sendBtn.disabled   = false;
        userInput.focus();
    }
});


export async function carregarChatsDoBackend() {
    console.log("tentando carregar chats do backend...")
    try {
        const res = await fetch(`${API_BASE}/chat`, {
            headers: authHeaders()
        });

        console.log(res)

        if (!res.ok) return;

        const chats = await res.json();
        salvarTodosChats(chats); // substitui o localStorage
        renderizarSidebar();
    } catch(e) {
        console.warn('Erro ao carregar chats do backend.');
        renderizarSidebar();
    }
}


