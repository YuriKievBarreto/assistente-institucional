// ── CONSTANTES ──────────────────────────────────────────────
const rodandoLocal = true
export const STORAGE_KEY = 'ifpb_chats';

export const API_BASE = rodandoLocal
  ? 'http://127.0.0.1:8000/api/v1'
  : 'https://sua-api-producao.com/api/v1';

export const BOT_AVATAR  = `<div class="msg-avatar bot"><img src="https://www.ifpb.edu.br/static/media/logo.20d47050.png" alt="IFPB"></div>`;
export const USER_AVATAR = `<div class="msg-avatar user-av">U</div>`;

// ── REFERÊNCIAS DO DOM ───────────────────────────────────────

export const chatForm  = document.getElementById('chat-form');
export const chatBox   = document.getElementById('chat-box');
export const userInput = document.getElementById('user-input');
export const sendBtn   = document.getElementById('send-btn');