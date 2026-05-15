"""
Grillato ERP - Dashboard BI
Analise de horario pico, dia da semana, previsao de demanda.
"""

from datetime import date, timedelta
from collections import defaultdict
from erp.supabase_client import get_supabase


def vendas_por_hora(dias=30):
    """Agrupa pedidos por hora do dia."""
    sb = get_supabase()
    data_inicio = (date.today() - timedelta(days=dias)).isoformat()
    pedidos = sb.table("pedidos").select(
        "data_pedido, total"
    ).gte("data_pedido", data_inicio).execute().data

    por_hora = defaultdict(lambda: {"total": 0, "qtd": 0})
    for p in pedidos:
        hora = p["data_pedido"][11:13] if len(p["data_pedido"]) > 13 else "00"
        por_hora[hora]["total"] += p["total"]
        por_hora[hora]["qtd"] += 1

    resultado = []
    for h in sorted(por_hora.keys()):
        resultado.append({
            "hora": f"{h}:00",
            "pedidos": por_hora[h]["qtd"],
            "faturamento": round(por_hora[h]["total"], 2),
            "ticket_medio": round(por_hora[h]["total"] / por_hora[h]["qtd"], 2) if por_hora[h]["qtd"] > 0 else 0,
        })
    return resultado


def vendas_por_dia_semana(dias=30):
    """Agrupa pedidos por dia da semana."""
    sb = get_supabase()
    data_inicio = (date.today() - timedelta(days=dias)).isoformat()
    pedidos = sb.table("pedidos").select(
        "data_pedido, total"
    ).gte("data_pedido", data_inicio).execute().data

    dias_nome = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo"]
    por_dia = defaultdict(lambda: {"total": 0, "qtd": 0, "dias_contados": set()})

    for p in pedidos:
        data_str = p["data_pedido"][:10]
        try:
            dt = date.fromisoformat(data_str)
            dia_idx = dt.weekday()
            por_dia[dia_idx]["total"] += p["total"]
            por_dia[dia_idx]["qtd"] += 1
            por_dia[dia_idx]["dias_contados"].add(data_str)
        except:
            pass

    resultado = []
    for i in range(7):
        d = por_dia.get(i, {"total": 0, "qtd": 0, "dias_contados": set()})
        n_dias = len(d["dias_contados"]) or 1
        resultado.append({
            "dia": dias_nome[i],
            "dia_idx": i,
            "pedidos_total": d["qtd"],
            "faturamento_total": round(d["total"], 2),
            "media_pedidos_dia": round(d["qtd"] / n_dias, 1),
            "media_faturamento_dia": round(d["total"] / n_dias, 2),
        })
    return resultado


def previsao_demanda(dias_historico=14, dias_previsao=7):
    """Previsao simples baseada em media movel."""
    sb = get_supabase()
    data_inicio = (date.today() - timedelta(days=dias_historico)).isoformat()
    fechamentos = sb.table("fechamentos_diarios").select(
        "data, faturamento_bruto, total_pedidos"
    ).gte("data", data_inicio).order("data").execute().data

    if not fechamentos:
        return []

    media_fat = sum(f["faturamento_bruto"] for f in fechamentos) / len(fechamentos)
    media_ped = sum(f["total_pedidos"] for f in fechamentos) / len(fechamentos)

    # Fator por dia da semana
    dias_semana = defaultdict(list)
    for f in fechamentos:
        try:
            dt = date.fromisoformat(f["data"])
            dias_semana[dt.weekday()].append(f["faturamento_bruto"])
        except:
            pass

    fatores = {}
    for dia_idx, vals in dias_semana.items():
        media_dia = sum(vals) / len(vals) if vals else media_fat
        fatores[dia_idx] = media_dia / media_fat if media_fat > 0 else 1

    previsoes = []
    for i in range(dias_previsao):
        dt = date.today() + timedelta(days=i + 1)
        fator = fatores.get(dt.weekday(), 1.0)
        previsoes.append({
            "data": dt.isoformat(),
            "dia_semana": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"][dt.weekday()],
            "faturamento_previsto": round(media_fat * fator, 2),
            "pedidos_previstos": max(1, round(media_ped * fator)),
        })

    return previsoes


def resumo_bi(dias=30):
    """Resumo geral do BI."""
    sb = get_supabase()
    data_inicio = (date.today() - timedelta(days=dias)).isoformat()
    pedidos = sb.table("pedidos").select("total, canal, data_pedido").gte(
        "data_pedido", data_inicio
    ).execute().data

    if not pedidos:
        return {"total_faturamento": 0, "total_pedidos": 0, "ticket_medio": 0, "melhor_canal": "—"}

    total = sum(p["total"] for p in pedidos)
    canais = defaultdict(float)
    for p in pedidos:
        canais[p.get("canal", "?")] += p["total"]

    melhor = max(canais.items(), key=lambda x: x[1]) if canais else ("—", 0)

    return {
        "total_faturamento": round(total, 2),
        "total_pedidos": len(pedidos),
        "ticket_medio": round(total / len(pedidos), 2),
        "melhor_canal": melhor[0],
        "faturamento_dia": round(total / dias, 2),
    }
