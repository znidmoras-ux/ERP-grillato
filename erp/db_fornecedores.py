"""
Grillato ERP - CRUD Fornecedores
"""

from erp.supabase_client import get_supabase


def listar_fornecedores(apenas_ativos=True):
    sb = get_supabase()
    q = sb.table("fornecedores").select("*")
    if apenas_ativos:
        q = q.eq("ativo", True)
    return q.order("nome").execute().data


def buscar_fornecedor(fornecedor_id):
    sb = get_supabase()
    return sb.table("fornecedores").select("*").eq(
        "id", fornecedor_id
    ).single().execute().data


def criar_fornecedor(dados: dict):
    sb = get_supabase()
    return sb.table("fornecedores").insert(dados).execute().data


def atualizar_fornecedor(fornecedor_id, dados: dict):
    sb = get_supabase()
    return sb.table("fornecedores").update(dados).eq(
        "id", fornecedor_id
    ).execute().data


def desativar_fornecedor(fornecedor_id):
    return atualizar_fornecedor(fornecedor_id, {"ativo": False})


def historico_compras_fornecedor(fornecedor_id, limite=20):
    sb = get_supabase()
    return sb.table("notas_fiscais").select(
        "*, itens_nota_fiscal(*, insumos(nome))"
    ).eq("fornecedor_id", fornecedor_id).order(
        "data_emissao", desc=True
    ).limit(limite).execute().data
