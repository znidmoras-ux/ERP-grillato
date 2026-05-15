"""
Grillato ERP - CRUD Produtos e Fichas Técnicas
Cardápio completo com CMV automático.
"""

from erp.supabase_client import get_supabase


# --- PRODUTOS ---

def listar_produtos(apenas_ativos=True):
    sb = get_supabase()
    q = sb.table("produtos").select("*, categorias_produto(nome)")
    if apenas_ativos:
        q = q.eq("ativo", True)
    return q.order("nome").execute().data


def buscar_produto(produto_id):
    sb = get_supabase()
    return sb.table("produtos").select(
        "*, categorias_produto(nome)"
    ).eq("id", produto_id).single().execute().data


def criar_produto(dados: dict):
    sb = get_supabase()
    return sb.table("produtos").insert(dados).execute().data


def atualizar_produto(produto_id, dados: dict):
    sb = get_supabase()
    return sb.table("produtos").update(dados).eq("id", produto_id).execute().data


def desativar_produto(produto_id):
    return atualizar_produto(produto_id, {"ativo": False})


def listar_categorias_produto():
    sb = get_supabase()
    return sb.table("categorias_produto").select("*").order("nome").execute().data


# --- FICHAS TÉCNICAS ---

def listar_ficha_tecnica(produto_id):
    sb = get_supabase()
    return sb.table("fichas_tecnicas").select(
        "*, insumos(nome, unidade_uso, custo_unitario)"
    ).eq("produto_id", produto_id).order("ordem").execute().data


def adicionar_ingrediente_ficha(produto_id, insumo_id, quantidade, modo_preparo="", ordem=0):
    sb = get_supabase()
    return sb.table("fichas_tecnicas").upsert({
        "produto_id": produto_id,
        "insumo_id": insumo_id,
        "quantidade": quantidade,
        "modo_preparo": modo_preparo,
        "ordem": ordem,
    }).execute().data


def remover_ingrediente_ficha(produto_id, insumo_id):
    sb = get_supabase()
    return sb.table("fichas_tecnicas").delete().eq(
        "produto_id", produto_id
    ).eq("insumo_id", insumo_id).execute().data


def atualizar_gramatura(produto_id, insumo_id, nova_quantidade):
    sb = get_supabase()
    return sb.table("fichas_tecnicas").update(
        {"quantidade": nova_quantidade}
    ).eq("produto_id", produto_id).eq("insumo_id", insumo_id).execute().data


# --- CMV ---

def cmv_todos_produtos():
    sb = get_supabase()
    return sb.table("vw_cmv_produtos").select("*").execute().data


def cmv_produto(produto_id):
    sb = get_supabase()
    return sb.table("vw_cmv_produtos").select("*").eq(
        "produto_id", produto_id
    ).single().execute().data
