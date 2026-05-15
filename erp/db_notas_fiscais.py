"""
Grillato ERP - CRUD Notas Fiscais
Registro de compras que alimenta estoque e custo médio automaticamente via trigger.
"""

from erp.supabase_client import get_supabase


def listar_notas(limite=50):
    sb = get_supabase()
    return sb.table("notas_fiscais").select(
        "*, fornecedores(nome)"
    ).order("data_emissao", desc=True).limit(limite).execute().data


def buscar_nota(nota_id):
    sb = get_supabase()
    nota = sb.table("notas_fiscais").select(
        "*, fornecedores(nome)"
    ).eq("id", nota_id).single().execute().data
    itens = sb.table("itens_nota_fiscal").select(
        "*, insumos(nome, unidade_compra)"
    ).eq("nota_fiscal_id", nota_id).execute().data
    nota["itens"] = itens
    return nota


def registrar_nota_fiscal(dados_nf: dict, itens: list):
    """
    dados_nf: {numero_nf, fornecedor_id, data_emissao, valor_total, observacoes}
    itens: [{insumo_id, quantidade, valor_unitario, valor_total}, ...]

    Os triggers do banco cuidam de:
    - Atualizar estoque do insumo
    - Recalcular custo médio ponderado
    - Registrar no histórico de preços
    - Criar movimentação de estoque
    """
    sb = get_supabase()
    nota = sb.table("notas_fiscais").insert(dados_nf).execute().data[0]
    for item in itens:
        item["nota_fiscal_id"] = nota["id"]
    sb.table("itens_nota_fiscal").insert(itens).execute()
    return nota


def deletar_nota(nota_id):
    sb = get_supabase()
    return sb.table("notas_fiscais").delete().eq("id", nota_id).execute().data
