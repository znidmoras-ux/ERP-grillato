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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        .login-container {
            text-align: center;
            padding: 40px 0 20px 0;
        }
        .login-brand {
            font-family: 'Inter', sans-serif;
            font-size: 2.4rem;
            font-weight: 900;
            letter-spacing: -1px;
            background: linear-gradient(135deg, #e94560, #f59e0b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 4px;
        }
        .login-sub {
            font-family: 'Inter', sans-serif;
            text-align: center;
            color: #6b7280;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 2.5px;
            margin-bottom: 32px;
        }
        .login-line {
            width: 48px;
            height: 3px;
            background: linear-gradient(90deg, #e94560, #f59e0b);
            margin: 12px auto 24px auto;
            border-radius: 2px;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div class="login-container">
            <div class="login-brand">GRILLATO</div>
            <div class="login-line"></div>
            <div class="login-sub">Sistema Operacional de Delivery</div>
        </div>
        """, unsafe_allow_html=True)
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
