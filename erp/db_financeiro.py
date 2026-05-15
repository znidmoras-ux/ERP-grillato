"""
Grillato ERP - Módulo Financeiro
Custos fixos, fechamento diário, runway e resumo.
"""

from datetime import date, timedelta
from erp.supabase_client import get_supabase


# --- CUSTOS FIXOS ---

def listar_custos_fixos(apenas_ativos=True):
    sb = get_supabase()
    q = sb.table("custos_fixos").select("*")
    if apenas_ativos:
        q = q.eq("ativo", True)
    return q.order("categoria").execute().data


def criar_custo_fixo(dados: dict):
    sb = get_supabase()
    return sb.table("custos_fixos").insert(dados).execute().data


def atualizar_custo_fixo(custo_id, dados: dict):
    sb = get_supabase()
    return sb.table("custos_fixos").update(dados).eq("id", custo_id).execute().data


def desativar_custo_fixo(custo_id):
    return atualizar_custo_fixo(custo_id, {"ativo": False})


def total_custos_fixos_mensal():
    custos = listar_custos_fixos()
    total = 0
    for c in custos:
        if c["recorrencia"] == "mensal":
            total += c["valor"]
        elif c["recorrencia"] == "semanal":
            total += c["valor"] * 4.33
        elif c["recorrencia"] == "diario":
            total += c["valor"] * 22
    return round(total, 2)


# --- FECHAMENTO DIÁRIO ---

def registrar_fechamento(dados: dict):
    sb = get_supabase()
    return sb.table("fechamentos_diarios").upsert(dados).execute().data


def buscar_fechamento(data_str: str):
    sb = get_supabase()
    res = sb.table("fechamentos_diarios").select("*").eq("data", data_str).execute().data
    return res[0] if res else None


def listar_fechamentos(limite=30):
    sb = get_supabase()
    return sb.table("fechamentos_diarios").select("*").order(
        "data", desc=True
    ).limit(limite).execute().data


def deletar_fechamento(fechamento_id):
    sb = get_supabase()
    return sb.table("fechamentos_diarios").delete().eq("id", fechamento_id).execute().data


# --- RESUMO FINANCEIRO ---

def resumo_financeiro(limite=30):
    sb = get_supabase()
    return sb.table("vw_resumo_financeiro").select("*").limit(limite).execute().data


def calcular_runway(caixa_atual: float, dias_operacao_mes: int = 22):
    custos_mensal = total_custos_fixos_mensal()
    custo_dia = custos_mensal / dias_operacao_mes if dias_operacao_mes > 0 else 0
    fechamentos = listar_fechamentos(7)
    if fechamentos:
        media_fat = sum(f["faturamento_bruto"] for f in fechamentos) / len(fechamentos)
        media_custo_insumos = sum(f.get("custo_insumos", 0) for f in fechamentos) / len(fechamentos)
    else:
        media_fat = 0
        media_custo_insumos = 0
    deficit_dia = custo_dia + media_custo_insumos - media_fat
    if deficit_dia > 0:
        runway_dias = int(caixa_atual / deficit_dia)
    else:
        runway_dias = 999
    return {
        "caixa_atual": caixa_atual,
        "custo_fixo_mensal": custos_mensal,
        "custo_fixo_dia": round(custo_dia, 2),
        "media_faturamento_7d": round(media_fat, 2),
        "media_custo_insumos_7d": round(media_custo_insumos, 2),
        "deficit_dia": round(max(0, deficit_dia), 2),
        "runway_dias": runway_dias,
        "risco": "CRITICO" if runway_dias < 15 else "ALERTA" if runway_dias < 30 else "SAUDAVEL",
    }


# --- HISTÓRICO DE PREÇOS ---

def historico_precos(insumo_id=None, limite=50):
    sb = get_supabase()
    q = sb.table("historico_precos").select("*, insumos(nome)")
    if insumo_id:
        q = q.eq("insumo_id", insumo_id)
    return q.order("data_registro", desc=True).limit(limite).execute().data
