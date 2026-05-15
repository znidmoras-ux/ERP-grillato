"""
Grillato ERP - Produtividade
Tempo de preparo, pedidos/hora, eficiencia por turno.
"""

from datetime import date, timedelta
from erp.supabase_client import get_supabase


def registrar_producao(dados: dict):
    sb = get_supabase()
    return sb.table("registros_producao").insert(dados).execute().data


def listar_producao(limite=30):
    sb = get_supabase()
    return sb.table("registros_producao").select("*").order(
        "data", desc=True
    ).limit(limite).execute().data


def deletar_registro(registro_id):
    sb = get_supabase()
    return sb.table("registros_producao").delete().eq("id", registro_id).execute().data


def metricas_produtividade(dias=7):
    """Calcula metricas de produtividade dos ultimos N dias."""
    sb = get_supabase()
    data_inicio = (date.today() - timedelta(days=dias)).isoformat()
    registros = sb.table("registros_producao").select("*").gte(
        "data", data_inicio
    ).execute().data

    if not registros:
        return {
            "media_tempo_preparo": 0,
            "media_pedidos_dia": 0,
            "pedidos_hora": 0,
            "melhor_dia": None,
            "pior_dia": None,
            "total_registros": 0,
        }

    tempos = [r["tempo_medio_preparo_min"] for r in registros if r.get("tempo_medio_preparo_min")]
    pedidos = [r["pedidos_realizados"] for r in registros if r.get("pedidos_realizados")]

    # Calcular pedidos/hora
    horas_trabalhadas = 0
    for r in registros:
        if r.get("hora_inicio") and r.get("hora_fim"):
            h_ini = int(r["hora_inicio"].split(":")[0])
            h_fim = int(r["hora_fim"].split(":")[0])
            horas_trabalhadas += max(1, h_fim - h_ini)

    pedidos_hora = round(sum(pedidos) / horas_trabalhadas, 1) if horas_trabalhadas > 0 else 0

    # Melhor e pior dia
    por_dia = {}
    for r in registros:
        d = r["data"]
        if d not in por_dia:
            por_dia[d] = 0
        por_dia[d] += r.get("pedidos_realizados", 0)

    melhor = max(por_dia.items(), key=lambda x: x[1]) if por_dia else (None, 0)
    pior = min(por_dia.items(), key=lambda x: x[1]) if por_dia else (None, 0)

    return {
        "media_tempo_preparo": round(sum(tempos) / len(tempos), 1) if tempos else 0,
        "media_pedidos_dia": round(sum(pedidos) / len(set(r["data"] for r in registros)), 1) if pedidos else 0,
        "pedidos_hora": pedidos_hora,
        "melhor_dia": {"data": melhor[0], "pedidos": melhor[1]},
        "pior_dia": {"data": pior[0], "pedidos": pior[1]},
        "total_registros": len(registros),
    }


def analise_por_turno(dias=30):
    """Analise de performance por turno."""
    sb = get_supabase()
    data_inicio = (date.today() - timedelta(days=dias)).isoformat()
    registros = sb.table("registros_producao").select("*").gte(
        "data", data_inicio
    ).execute().data

    turnos = {}
    for r in registros:
        t = r.get("turno", "integral")
        if t not in turnos:
            turnos[t] = {"pedidos": 0, "tempo_total": 0, "registros": 0}
        turnos[t]["pedidos"] += r.get("pedidos_realizados", 0)
        turnos[t]["tempo_total"] += r.get("tempo_medio_preparo_min", 0)
        turnos[t]["registros"] += 1

    for t in turnos:
        n = turnos[t]["registros"]
        turnos[t]["media_pedidos"] = round(turnos[t]["pedidos"] / n, 1) if n > 0 else 0
        turnos[t]["media_tempo"] = round(turnos[t]["tempo_total"] / n, 1) if n > 0 else 0

    return turnos
