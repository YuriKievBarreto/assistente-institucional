   // ── CONSTANTES ──────────────────────────────────────────────
    const STORAGE_KEY = 'ifpb_chats';
    const BOT_AVATAR  = `<div class="msg-avatar bot"><img src="https://www.ifpb.edu.br/static/media/logo.20d47050.png" alt="IFPB"></div>`;
    const USER_AVATAR = `<div class="msg-avatar user-av">U</div>`;

    const chatForm  = document.getElementById('chat-form');
    const chatBox   = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn   = document.getElementById('send-btn');

    // ── ESTADO ──────────────────────────────────────────────────
    let currentChatId = null;

    // ── LOCALSTORAGE ─────────────────────────────────────────────

    function carregarTodosChats() {
        return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    }

    function salvarTodosChats(chats) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
    }

    function buscarChat(id) {
        return carregarTodosChats().find(c => c.id === id) || null;
    }

    function salvarMensagem(chatId, role, content) {
        const chats = carregarTodosChats();
        const chat  = chats.find(c => c.id === chatId);
        if (!chat) return;
        chat.messages.push({ role, content });
        salvarTodosChats(chats);
    }

    function gerarId() {
        return crypto.randomUUID();
    }

    function gerarTitulo(texto) {
        return texto.length > 40 ? texto.slice(0, 40) + '…' : texto;
    }

    // ── SIDEBAR ──────────────────────────────────────────────────

    function renderizarSidebar() {
        const chats     = carregarTodosChats();
        const container = document.getElementById('chat-history');
        container.innerHTML = '';

        if (chats.length === 0) {
            container.innerHTML = `<div style="padding:12px 14px;font-size:12px;color:#ffffff30;">Nenhuma conversa ainda</div>`;
            return;
        }

        // mais recentes primeiro
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

    // ── RENDERIZAR MENSAGENS ──────────────────────────────────────

    function renderizarMensagens(messages) {
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

    // ── AÇÕES ────────────────────────────────────────────────────

    function novaConversa() {
        const id    = gerarId();
        const chats = carregarTodosChats();
        chats.push({ id, title: 'Nova conversa', messages: [] });
        salvarTodosChats(chats);
        abrirChat(id);
    }

    function abrirChat(id) {
        currentChatId = id;
        const chat = buscarChat(id);
        renderizarMensagens(chat ? chat.messages : []);
        renderizarSidebar();
        userInput.focus();
    }

    function excluirChat(id) {
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

    // ── UI HELPERS ───────────────────────────────────────────────

    function addBotMessage(text) {
        // remove empty state se existir
        const empty = chatBox.querySelector('.empty-state');
        if (empty) empty.remove();

        const row = document.createElement('div');
        row.classList.add('message-row');
        row.innerHTML = `${BOT_AVATAR}<div class="message bot-msg">${text}</div>`;
        chatBox.appendChild(row);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function showTyping() {
        const row = document.createElement('div');
        row.classList.add('message-row');
        row.id = 'typing';
        row.innerHTML = `${BOT_AVATAR}<div class="typing-indicator"><span></span><span></span><span></span></div>`;
        chatBox.appendChild(row);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function hideTyping() {
        const el = document.getElementById('typing');
        if (el) el.remove();
    }

    // ── ENVIO ────────────────────────────────────────────────────

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const messageText = userInput.value.trim();
        if (!messageText) return;

        // cria chat automaticamente se não houver nenhum ativo
        if (!currentChatId) {
            novaConversa();
        }

        // define título do chat pela primeira mensagem
        const chats = carregarTodosChats();
        const chat  = chats.find(c => c.id === currentChatId);
        if (chat && chat.title === 'Nova conversa') {
            chat.title = gerarTitulo(messageText);
            salvarTodosChats(chats);
        }

        // salva mensagem do usuário
        salvarMensagem(currentChatId, 'human', messageText);

        // renderiza mensagem do usuário
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

        const response = await enviarMensagem(messageText);

        hideTyping();
        userInput.disabled = false;
        sendBtn.disabled   = false;
        userInput.focus();

        if (response) {
            const resposta = response.answer || response.mensagem_recebida || '';
            salvarMensagem(currentChatId, 'ai', resposta);
            addBotMessage(resposta);
        }
    });

    async function enviarMensagem(textoDoUsuario) {
        try {
            const resposta = await fetch('http://127.0.0.1:8000/api/v1/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: textoDoUsuario, session_id: currentChatId })
            });
            return await resposta.json();
        } catch (erro) {
            console.error('Erro ao conectar com o servidor:', erro);
            addBotMessage('Não foi possível conectar com o servidor. Tente novamente.');
        }
    }

    // ── INICIALIZAÇÃO ────────────────────────────────────────────

    function init() {
        // sempre começa sem chat ativo — o histórico fica disponível na sidebar
        currentChatId = null;
        chatBox.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-message-circle"></i>
                <p>Digite uma mensagem para começar ou selecione uma conversa</p>
            </div>`;
        renderizarSidebar();
    }

    init();