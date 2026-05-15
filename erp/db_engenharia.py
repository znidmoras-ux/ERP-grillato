"""
Grillato ERP - Engenharia de Cardapio (Matriz BCG)
Classifica produtos em: Estrela, Cavalo de Batalha, Enigma, Cao.
"""

from erp.supabase_client import get_supabase


def analise_engenharia(data_inicio=None, data_fim=None):
    """
    Cruza popularidade (qtd vendida) com margem (lucro unitario).
    Retorna classificacao BCG de cada produto.
    """
    sb = get_supabase()

    # 1. CMV de todos os produtos
    cmv = sb.table("vw_cmv_produtos").select("*").execute().data
    cmv_map = {c["produto_id"]: c for c in cmv} if cmv else {}

    # 2. Vendas por produto
    q = sb.table("itens_pedido").select("produto_id, quantidade, produtos(nome)")
    if data_inicio:
        q = q.gte("created_at", data_inicio)
    if data_fim:
        q = q.lte("created_at", data_fim)
    vendas_raw = q.execute().data

    # Agregar vendas
    vendas = {}
    for v in vendas_raw:
        pid = v["produto_id"]
        if pid not in vendas:
            vendas[pid] = {"qtd": 0, "nome": v.get("produtos", {}).get("nome", "?")}
        vendas[pid]["qtd"] += v["quantidade"]

    if not vendas:
        return []

    # 3. Calcular medianas
    qtds = [v["qtd"] for v in vendas.values()]
    margens = []
    for pid in vendas:
        c = cmv_map.get(pid, {})
        margens.append(c.get("cmv_pct", 50))

    mediana_qtd = sorted(qtds)[len(qtds) // 2]
    mediana_cmv = sorted(margens)[len(margens) // 2]

    # 4. Classificar
    resultado = []
    for pid, v in vendas.items():
        c = cmv_map.get(pid, {})
        cmv_pct = c.get("cmv_pct", 50)
        lucro = c.get("lucro", 0)
        preco = c.get("preco_venda", 0)
        qtd = v["qtd"]

        alta_pop = qtd >= mediana_qtd
        alta_margem = cmv_pct <= mediana_cmv  # CMV baixo = margem alta

        if alta_pop and alta_margem:
            classe = "Estrela"
            emoji = "⭐"
            acao = "Manter e destacar no cardapio"
        elif alta_pop and not alta_margem:
            classe = "Cavalo de Batalha"
            emoji = "🐴"
            acao = "Popular mas margem baixa. Reduzir gramatura ou subir preco"
        elif not alta_pop and alta_margem:
            classe = "Enigma"
            emoji = "❓"
            acao = "Boa margem mas vende pouco. Promover mais"
        else:
            classe = "Cao"
            emoji = "🐕"
            acao = "Margem ruim e vende pouco. Considerar remover"

        resultado.append({
            "produto_id": pid,
            "nome": v["nome"],
            "qtd_vendida": qtd,
            "preco_venda": preco,
            "custo": c.get("custo_total", 0),
            "lucro_unitario": lucro,
            "cmv_pct": cmv_pct,
            "receita_total": round(preco * qtd, 2),
            "lucro_total": round(lucro * qtd, 2),
            "classe": classe,
            "emoji": emoji,
            "acao": acao,
        })

    resultado.sort(key=lambda x: x["lucro_total"], reverse=True)
    return resultado
