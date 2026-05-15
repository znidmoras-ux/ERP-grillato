"""
Grillato ERP - Metas Inteligentes
Meta diaria calculada pelo break-even, acompanhamento em tempo real.
"""

from datetime import date
from erp.supabase_client import get_supabase
from erp import db_financeiro


def calcular_meta_diaria(dias_operacao=22):
    """Calcula meta diaria baseada nos custos fixos."""
    custo_mensal = db_financeiro.total_custos_fixos_mensal()
    meta_fat = round(custo_mensal / dias_operacao * 1.3, 2)  # 30% margem seguranca
    meta_pedidos = max(1, int(meta_fat / 35))  # ticket medio estimado R$35
    return {
        "meta_faturamento": meta_fat,
        "meta_pedidos": meta_pedidos,
        "custo_dia": round(custo_mensal / dias_operacao, 2),
    }


def registrar_meta_dia(data_str=None):
    """Cria ou atualiza meta do dia."""
    sb = get_supabase()
    if not data_str:
        data_str = date.today().isoformat()
    meta = calcular_meta_diaria()
    return sb.table("metas_diarias").upsert({
        "data": data_str,
        "meta_faturamento": meta["meta_faturamento"],
        "meta_pedidos": meta["meta_pedidos"],
    }).execute().data


def atualizar_progresso(data_str=None, faturamento=0, pedidos=0, pedidos_direto=0):
    """Atualiza progresso do dia."""
    sb = get_supabase()
    if not data_str:
        data_str = date.today().isoformat()
    return sb.table("metas_diarias").upsert({
        "data": data_str,
        "faturamento_atual": faturamento,
        "pedidos_atual": pedidos,
        "pedidos_direto_atual": pedidos_direto,
        "status": "batida" if pedidos >= calcular_meta_diaria()["meta_pedidos"] else "em_andamento",
    }).execute().data


def buscar_meta_dia(data_str=None):
    sb = get_supabase()
    if not data_str:
        data_str = date.today().isoformat()
    res = sb.table("metas_diarias").select("*").eq("data", data_str).execute().data
    return res[0] if res else None


def historico_metas(limite=30):
    sb = get_supabase()
    return sb.table("metas_diarias").select("*").order("data", desc=True).limit(limite).execute().data


def taxa_batimento(limite=30):
    """Calcula % de dias que bateu a meta."""
    metas = historico_metas(limite)
    if not metas:
        return 0
    batidas = len([m for m in metas if m.get("status") == "batida"])
    return round((batidas / len(metas)) * 100, 1)
