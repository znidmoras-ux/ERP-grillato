"""
Grillato ERP - Previsao de Compras
Gera lista de compras automatica baseada em consumo historico.
"""

from datetime import date, timedelta
from erp.supabase_client import get_supabase


def calcular_consumo_medio(dias=7):
    """Calcula consumo medio diario de cada insumo nos ultimos N dias."""
    sb = get_supabase()
    data_inicio = (date.today() - timedelta(days=dias)).isoformat()

    # Buscar movimentacoes de saida
    movs = sb.table("movimentacoes_estoque").select(
        "insumo_id, quantidade, insumos(nome, unidade_compra, estoque_atual, estoque_minimo, custo_unitario, fator_conversao)"
    ).in_("tipo", ["saida_venda", "saida_perda"]).gte(
        "created_at", data_inicio
    ).execute().data

    consumo = {}
    for m in movs:
        pid = m["insumo_id"]
        if pid not in consumo:
            ins = m.get("insumos", {})
            consumo[pid] = {
                "nome": ins.get("nome", "?"),
                "unidade": ins.get("unidade_compra", "kg"),
                "estoque_atual": ins.get("estoque_atual", 0),
                "estoque_minimo": ins.get("estoque_minimo", 0),
                "custo_unitario_uso": ins.get("custo_unitario", 0),
                "fator_conversao": ins.get("fator_conversao", 1000),
                "total_consumido": 0,
            }
        consumo[pid]["total_consumido"] += abs(m["quantidade"])

    for pid in consumo:
        consumo[pid]["media_dia"] = round(consumo[pid]["total_consumido"] / dias, 3)

    return consumo


def gerar_lista_compras(dias_cobertura=7):
    """Gera lista de compras para cobrir N dias."""
    sb = get_supabase()
    consumo = calcular_consumo_medio(7)

    itens = []
    for pid, dados in consumo.items():
        necessidade = dados["media_dia"] * dias_cobertura
        disponivel = dados["estoque_atual"]
        comprar = max(0, necessidade - disponivel + dados["estoque_minimo"])

        if comprar > 0:
            custo_est = round(comprar * dados["custo_unitario_uso"] * dados["fator_conversao"], 2)
            itens.append({
                "insumo_id": pid,
                "nome": dados["nome"],
                "unidade": dados["unidade"],
                "estoque_atual": dados["estoque_atual"],
                "consumo_dia": dados["media_dia"],
                "necessidade_periodo": round(necessidade, 3),
                "quantidade_sugerida": round(comprar, 3),
                "custo_estimado": custo_est,
            })

    itens.sort(key=lambda x: x["custo_estimado"], reverse=True)

    # Salvar lista no banco
    lista = sb.table("listas_compras").insert({
        "periodo_dias": dias_cobertura,
    }).execute().data[0]

    for item in itens:
        sb.table("itens_lista_compras").insert({
            "lista_id": lista["id"],
            "insumo_id": item["insumo_id"],
            "quantidade_sugerida": item["quantidade_sugerida"],
            "unidade": item["unidade"],
            "custo_estimado": item["custo_estimado"],
        }).execute()

    return {"lista_id": lista["id"], "itens": itens, "total_estimado": sum(i["custo_estimado"] for i in itens)}


def listar_listas_compras(limite=10):
    sb = get_supabase()
    return sb.table("listas_compras").select(
        "*, itens_lista_compras(*, insumos(nome))"
    ).order("created_at", desc=True).limit(limite).execute().data


def marcar_item_comprado(item_id, comprado=True):
    sb = get_supabase()
    return sb.table("itens_lista_compras").update(
        {"comprado": comprado}
    ).eq("id", item_id).execute().data
