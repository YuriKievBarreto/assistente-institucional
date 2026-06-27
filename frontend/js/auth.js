// ── AUTENTICAÇÃO ─────────────────────────────────────────────

import { API_BASE } from './constants.js';
import { carregarTodosChats } from './storage.js';
import { abrirModalAuth, fecharModalAuth } from './modal.js';
import { excluirChat, carregarChatsDoBackend, renderizarSidebar } from './chat.js';

// ── TOKEN ─────────────────────────────────────────────────────

export function getToken() {
    return localStorage.getItem('access_token');
}

export function setToken(token) {
    localStorage.setItem('access_token', token);
}

export function removeToken() {
    localStorage.removeItem('access_token');
}

export function isLoggedIn() {
    return !!getToken();
}

export function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
    };
}

// ── LOGIN ─────────────────────────────────────────────────────

export async function fazerLogin(e) {
    e.preventDefault();
    const email    = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const errorEl  = document.getElementById('auth-error');

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (!res.ok) {
            errorEl.textContent = 'Email ou senha incorretos.';
            return;
        }

        const data = await res.json();
        setToken(data.access_token);
        fecharModalAuth();
        atualizarPerfilUI(data.user);
    } catch {
        errorEl.textContent = 'Erro ao conectar com o servidor.';
    }

    location.reload()
}

// ── REGISTER ─────────────────────────────────────────────────

export async function fazerRegister(e) {
    e.preventDefault();
    const name     = document.getElementById('register-name').value.trim();
    const email    = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const errorEl  = document.getElementById('auth-error');

    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });

        if (!res.ok) {
            const err = await res.json();
            errorEl.textContent = err.detail || 'Erro ao criar conta.';
            return;
        }

        const data = await res.json();
        setToken(data.access_token);
        fecharModalAuth();
        atualizarPerfilUI(data.user);
        await migrarChats();
    } catch {
        errorEl.textContent = 'Erro ao conectar com o servidor.';
    }
}

// ── LOGOUT ────────────────────────────────────────────────────

export function fazerLogout() {
    removeToken();
    const todosChats = carregarTodosChats()
    console.log(todosChats)
    for (let chat of todosChats){
        excluirChat(chat.id)
    }
    

    atualizarPerfilUI(null);
}

// ── MIGRAÇÃO DE CHATS ─────────────────────────────────────────

export async function migrarChats() {
    const chats = carregarTodosChats();
    if (chats.length === 0) return;

    const chats_data = chats.map(chat => ({
        title: chat.title,
        created_at: chat.created_at || new Date().toISOString(),
        history: (chat.messages || []).map(msg => ({
            role: msg.role,
            content: msg.content,
            created_at: msg.created_at || new Date().toISOString()
        }))
    }));

    try {
        await fetch(`${API_BASE}/chat/migrate`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ chats_data })
        });
    } catch {
        console.error('Erro ao migrar chats.');
    }
}

// ── UI DE PERFIL ──────────────────────────────────────────────

export function atualizarPerfilUI(user) {
    const nameEl     = document.getElementById('profile-name');
    const roleEl     = document.getElementById('profile-role');
    const avatarEl   = document.getElementById('profile-avatar');
    const btnEl      = document.getElementById('profile-btn');
    const logoutIcon = document.getElementById('logout-icon');

    if (user) {
        nameEl.textContent       = user.name;
        roleEl.textContent       = user.email;
        avatarEl.textContent     = user.name.charAt(0).toUpperCase();
        logoutIcon.style.display = 'block';
        btnEl.onclick            = fazerLogout;
    } else {
        nameEl.textContent       = 'Usuário';
        roleEl.textContent       = 'Clique para entrar';
        avatarEl.textContent     = 'U';
        logoutIcon.style.display = 'none';
        btnEl.onclick            = () => abrirModalAuth('login');
    }
}

// ── SESSÃO ──────────────────────────────────────────────


export async function verificarSessao() {
    if (!isLoggedIn()) {
        renderizarSidebar(); // renderiza vazio se não logado
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            headers: authHeaders()
        });

        if (!res.ok) {
            removeToken();
            atualizarPerfilUI(null);
            renderizarSidebar();
            return;
        }

        const user = await res.json();
        atualizarPerfilUI(user);
        await carregarChatsDoBackend(); // substitui localStorage e renderiza sidebar
    } catch {
        console.warn('Não foi possível verificar a sessão.');
        renderizarSidebar();
    }
}