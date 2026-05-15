"""
Grillato ERP - Sistema de Autenticacao
Dois perfis: admin (acesso total) e caixa (acesso limitado).
"""

import streamlit as st
import hashlib
import hmac

PERFIS = {
    "admin": {
        "nome_display": "Administrador",
        "paginas": [
            "Dashboard", "Insumos", "Produtos", "Fornecedores",
            "Notas Fiscais", "Pedidos", "Financeiro", "CMV", "Custos Fixos",
            "Engenharia", "BI", "Metas", "Compras", "Produtividade",
        ],
    },
    "caixa": {
        "nome_display": "Caixa",
        "paginas": [
            "Dashboard", "Pedidos", "Financeiro", "Metas"
        ],
    },
}


def _hash_senha(senha: str) -> str:
    salt = "grillato_erp_2026"
    return hashlib.sha256(f"{salt}{senha}".encode()).hexdigest()


def _get_usuarios() -> dict:
    try:
        users = st.secrets.get("usuarios", {})
        if users:
            return dict(users)
    except Exception:
        pass
    return {
        "admin": _hash_senha("grillato10"),
        "caixa": _hash_senha("1234"),
    }


def _verificar_credenciais(usuario: str, senha: str) -> bool:
    usuarios = _get_usuarios()
    if usuario not in usuarios:
        return False
    senha_hash = _hash_senha(senha)
    return hmac.compare_digest(senha_hash, usuarios[usuario])


def get_perfil_atual() -> str:
    return st.session_state.get("perfil", "")


def tem_permissao(pagina: str) -> bool:
    perfil = get_perfil_atual()
    if perfil not in PERFIS:
        return False
    return pagina in PERFIS[perfil]["paginas"]


def paginas_permitidas() -> list:
    perfil = get_perfil_atual()
    if perfil not in PERFIS:
        return []
    return PERFIS[perfil]["paginas"]


def render_login():
    if st.session_state.get("autenticado", False):
        return True

    st.markdown("""
    <style>
        .login-title {text-align:center;font-size:2rem;font-weight:700;color:#e94560;margin-bottom:8px;}
        .login-sub {text-align:center;color:#8a8a9a;font-size:0.9rem;margin-bottom:24px;}
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="login-title">GRILLATO ERP</p>', unsafe_allow_html=True)
        st.markdown('<p class="login-sub">Sistema de Gestao</p>', unsafe_allow_html=True)
        with st.form("login_form"):
            usuario = st.text_input("Usuario", placeholder="admin ou caixa")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            if submit:
                if not usuario or not senha:
                    st.error("Preencha usuario e senha.")
                elif _verificar_credenciais(usuario, senha):
                    st.session_state["autenticado"] = True
                    st.session_state["usuario"] = usuario
                    st.session_state["perfil"] = usuario
                    st.session_state["tentativas_falhas"] = 0
                    st.rerun()
                else:
                    tentativas = st.session_state.get("tentativas_falhas", 0) + 1
                    st.session_state["tentativas_falhas"] = tentativas
                    if tentativas >= 5:
                        st.error("Muitas tentativas incorretas.")
                    else:
                        st.error(f"Usuario ou senha incorretos. Tentativa {tentativas}/5")
    return False


def render_user_info():
    perfil = get_perfil_atual()
    info = PERFIS.get(perfil, {})
    st.markdown(f"**Logado como:** {info.get('nome_display', perfil)}")
    if st.button("Sair", key="btn_logout"):
        for key in ["autenticado", "usuario", "perfil"]:
            st.session_state.pop(key, None)
        st.rerun()
