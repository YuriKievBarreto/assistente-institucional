// ── MODAL DE AUTENTICAÇÃO ─────────────────────────────────────

export function abrirModalAuth(aba = 'login') {
    document.getElementById('modal-auth').style.display = 'flex';
    trocarAba(aba);
}

export function fecharModalAuth() {
    document.getElementById('modal-auth').style.display = 'none';
    document.getElementById('auth-error').textContent = '';
}

export function trocarAba(aba) {
    document.getElementById('form-login').style.display    = aba === 'login'    ? 'flex' : 'none';
    document.getElementById('form-register').style.display = aba === 'register' ? 'flex' : 'none';
    document.getElementById('tab-login').classList.toggle('active', aba === 'login');
    document.getElementById('tab-register').classList.toggle('active', aba === 'register');
    document.getElementById('auth-error').textContent = '';
}