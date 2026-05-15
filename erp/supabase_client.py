"""
Grillato ERP - Supabase Client
Conexao centralizada. Funciona com .env local ou st.secrets no Streamlit Cloud.
"""

import os
from supabase import create_client, Client

_client: Client = None

def get_supabase() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")

        # Fallback: Streamlit secrets (para deploy no Streamlit Cloud)
        if not url or not key:
            try:
                import streamlit as st
                url = st.secrets.get("SUPABASE_URL", url)
                key = st.secrets.get("SUPABASE_KEY", key)
            except Exception:
                pass

        if not url or not key:
            raise ValueError(
                "Configure SUPABASE_URL e SUPABASE_KEY nas variaveis de ambiente, "
                "no arquivo .env, ou em .streamlit/secrets.toml"
            )
        _client = create_client(url, key)
    return _client
