"""
Grillato ERP - Supabase Client
Conexão centralizada com o banco de dados.
"""

import os
from supabase import create_client, Client

_client: Client = None

def get_supabase() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise ValueError(
                "Configure SUPABASE_URL e SUPABASE_KEY nas variáveis de ambiente "
                "ou no arquivo .env"
            )
        _client = create_client(url, key)
    return _client
