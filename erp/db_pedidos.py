"""
Grillato ERP - CRUD Pedidos/Vendas
Registro de vendas que dá baixa automática no estoque via trigger.
"""

from erp.supabase_client import get_supabase


def listar_pedidos(limite=50, data_inicio=None, data_fim=None):
    sb = get_supabase()
    q = sb.table("pedidos").select("*")
    if data_inicio:
        q = q.gte("data_pedido", data_inicio)
    if data_fim:
        q = q.lte("data_pedido", data_fim)
    return q.order("data_pedido", desc=True).limit(limite).execute().data


def buscar_pedido(pedido_id):
    sb = get_supabase()
    pedido = sb.table("pedidos").select("*").eq(
        "id", pedido_id
    ).single().execute().data
    itens = sb.table("itens_pedido").select(
        "*, produtos(nome, preco_venda)"
    ).eq("pedido_id", pedido_id).execute().data
    pedido["itens"] = itens
    return pedido


def registrar_pedido(dados_pedido: dict, itens: list):
    """
    dados_pedido: {numero_pedido, canal, subtotal, taxa_entrega, taxa_plataforma, desconto, total}
    itens: [{produto_id, quantidade, preco_unitario, preco_total}, ...]

    O trigger trg_baixar_estoque cuida da baixa automática.
    """
    sb = get_supabase()
    pedido = sb.table("pedidos").insert(dados_pedido).execute().data[0]
    for item in itens:
        item["pedido_id"] = pedido["id"]
    sb.table("itens_pedido").insert(itens).execute()
    return pedido


def deletar_pedido(pedido_id):
    sb = get_supabase()
    return sb.table("pedidos").delete().eq("id", pedido_id).execute().data


def vendas_por_periodo(data_inicio, data_fim):
    sb = get_supabase()
    return sb.table("pedidos").select(
        "data_pedido, canal, total, status"
    ).gte("data_pedido", data_inicio).lte(
        "data_pedido", data_fim
    ).order("data_pedido").execute().data


def vendas_por_canal(data_inicio=None, data_fim=None):
    sb = get_supabase()
    q = sb.table("pedidos").select("canal, total")
    if data_inicio:
        q = q.gte("data_pedido", data_inicio)
    if data_fim:
        q = q.lte("data_pedido", data_fim)
    dados = q.execute().data
    resumo = {}
    for p in dados:
        canal = p["canal"]
        if canal not in resumo:
            resumo[canal] = {"total": 0, "qtd": 0}
        resumo[canal]["total"] += p["total"]
        resumo[canal]["qtd"] += 1
    return resumo
