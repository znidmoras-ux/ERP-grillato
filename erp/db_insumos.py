"""
Grillato ERP - CRUD Insumos
Cadastro completo de ingredientes com conversão automática de unidades.
"""

from erp.supabase_client import get_supabase


def listar_insumos(apenas_ativos=True):
    sb = get_supabase()
    q = sb.table("insumos").select(
        "*, categorias_insumo(nome), fornecedores(nome)"
    )
    if apenas_ativos:
        q = q.eq("ativo", True)
    return q.order("nome").execute().data


def buscar_insumo(insumo_id):
    sb = get_supabase()
    return sb.table("insumos").select(
        "*, categorias_insumo(nome), fornecedores(nome)"
    ).eq("id", insumo_id).single().execute().data


def criar_insumo(dados: dict):
    sb = get_supabase()
    return sb.table("insumos").insert(dados).execute().data


def atualizar_insumo(insumo_id, dados: dict):
    sb = get_supabase()
    return sb.table("insumos").update(dados).eq("id", insumo_id).execute().data


def desativar_insumo(insumo_id):
    return atualizar_insumo(insumo_id, {"ativo": False})


def listar_categorias_insumo():
    sb = get_supabase()
    return sb.table("categorias_insumo").select("*").order("nome").execute().data


def criar_categoria_insumo(nome, descricao=""):
    sb = get_supabase()
    return sb.table("categorias_insumo").insert(
        {"nome": nome, "descricao": descricao}
    ).execute().data


def estoque_alertas():
    sb = get_supabase()
    return sb.table("vw_estoque_alertas").select("*").execute().data


def ajustar_estoque(insumo_id, quantidade, observacao="Ajuste manual"):
    sb = get_supabase()
    insumo = buscar_insumo(insumo_id)
    novo_saldo = max(0, insumo["estoque_atual"] + quantidade)
    sb.table("insumos").update({"estoque_atual": novo_saldo}).eq("id", insumo_id).execute()
    sb.table("movimentacoes_estoque").insert({
        "insumo_id": insumo_id,
        "tipo": "ajuste",
        "quantidade": quantidade,
        "saldo_apos": novo_saldo,
        "referencia_tipo": "manual",
        "observacao": observacao,
    }).execute()
    return novo_saldo


def registrar_perda(insumo_id, quantidade, motivo=""):
    sb = get_supabase()
    insumo = buscar_insumo(insumo_id)
    novo_saldo = max(0, insumo["estoque_atual"] - abs(quantidade))
    sb.table("insumos").update({"estoque_atual": novo_saldo}).eq("id", insumo_id).execute()
    sb.table("movimentacoes_estoque").insert({
        "insumo_id": insumo_id,
        "tipo": "saida_perda",
        "quantidade": -abs(quantidade),
        "saldo_apos": novo_saldo,
        "referencia_tipo": "manual",
        "observacao": f"Perda: {motivo}",
    }).execute()
    return novo_saldo


def historico_movimentacoes(insumo_id=None, limite=50):
    sb = get_supabase()
    q = sb.table("movimentacoes_estoque").select("*, insumos(nome)")
    if insumo_id:
        q = q.eq("insumo_id", insumo_id)
    return q.order("created_at", desc=True).limit(limite).execute().data
