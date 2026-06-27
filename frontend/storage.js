// ── LOCALSTORAGE ─────────────────────────────────────────────

import { STORAGE_KEY } from './constants.js';

export function carregarTodosChats() {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
}

export function salvarTodosChats(chats) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
}

export function buscarChat(id) {
    return carregarTodosChats().find(c => c.id === id) || null;
}

export function salvarMensagem(chatId, role, content) {
    const chats = carregarTodosChats();
    const chat  = chats.find(c => c.id === chatId);
    if (!chat) return;
    chat.messages.push({ role, content, created_at: new Date().toISOString() });
    salvarTodosChats(chats);
}

export function gerarId() {
    return crypto.randomUUID();
}

export function gerarTitulo(texto) {
    return texto.length > 40 ? texto.slice(0, 40) + '…' : texto;
}