"""
Grillato System - Dashboard Streamlit
Uso: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
import io
import tempfile
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from modulos.motor_financeiro import MotorFinanceiro
from modulos.radar_inflacao import RadarInflacao, ITENS_CURVA_A
from modulos.gestao_estoque import GestaoEstoque

# ======================================================================
# Page Config
# ======================================================================
st.set_page_config(
    page_title="Grillato System",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ======================================================================
# Config & Modulos
# ======================================================================
def carregar_config():
    config_path = os.path.join(ROOT_DIR, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    for chave, caminho in config["caminhos"].items():
        if not os.path.isabs(caminho):
            config["caminhos"][chave] = os.path.join(ROOT_DIR, caminho)
    return config


def salvar_config(config):
    """Salva alteracoes no config.json."""
    config_path = os.path.join(ROOT_DIR, "config.json")
    config_salvar = json.loads(json.dumps(config))
    # Reverte paths para relativos
    for chave, caminho in config_salvar["caminhos"].items():
        if caminho.startswith(ROOT_DIR):
            config_salvar["caminhos"][chave] = os.path.relpath(caminho, ROOT_DIR).replace("\\", "/")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_salvar, f, indent=4, ensure_ascii=False)


# ======================================================================
# CSS
# ======================================================================
def injetar_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .main-header h1 { color: #e94560; margin: 0; font-size: 1.6rem; }
    .main-header p { color: #8a8a9a; margin: 0.2rem 0 0; font-size: 0.85rem; }
    [data-testid="stMetric"] {
        background: #f8f9fa; border: 1px solid #e9ecef;
        border-radius: 8px; padding: 0.8rem;
    }
    .alerta-runway {
        padding: 0.7rem 1rem; border-radius: 8px;
        font-weight: 600; font-size: 0.9rem; margin-bottom: 0.8rem;
    }
    .alerta-critico { background: #fde8e8; color: #dc3545; border-left: 4px solid #dc3545; }
    .alerta-atencao { background: #fff3cd; color: #856404; border-left: 4px solid #f39c12; }
    .alerta-ok { background: #d4edda; color: #155724; border-left: 4px solid #27ae60; }
    .secao-titulo {
        font-size: 1.1rem; font-weight: 700; color: #1a1a2e;
        border-bottom: 2px solid #e94560;
        padding-bottom: 0.3rem; margin: 1rem 0 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)


# ======================================================================
# Header e KPIs
# ======================================================================
def render_header():
    st.markdown("""
    <div class="main-header">
        <h1>GRILLATO SYSTEM</h1>
        <p>Painel de Controle &mdash; Arapongas, PR &mdash; {data}</p>
    </div>
    """.format(data=datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)


def render_alerta_runway(runway_dias, caixa_atual):
    if runway_dias == -1:
        css, msg = "alerta-ok", "Operacao SUSTENTAVEL - faturamento acima do break-even."
    elif runway_dias <= 7:
        css, msg = "alerta-critico", f"CRITICO: {runway_dias} dias de caixa. R$ {caixa_atual:,.2f} restantes."
    elif runway_dias <= 15:
        css, msg = "alerta-atencao", f"ATENCAO: {runway_dias} dias de caixa. R$ {caixa_atual:,.2f} restantes."
    else:
        css, msg = "alerta-ok", f"Runway: {runway_dias} dias. Caixa: R$ {caixa_atual:,.2f}."
    st.markdown(f'<div class="alerta-runway {css}">{msg}</div>', unsafe_allow_html=True)


def render_kpis(config, motor):
    status = motor.get_status_caixa()
    fin = config["financeiro"]
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("Caixa Liquido", f"R$ {status['caixa_atual']:,.2f}",
                  delta=f"-{status['pct_consumido']:.1f}% usado" if status['pct_consumido'] > 0 else "Intacto",
                  delta_color="inverse")
    with c2:
        r = status["runway_dias"]
        st.metric("Runway", f"{r} dias" if r >= 0 else "Sustentavel",
                  delta="Critico" if 0 <= r <= 7 else ("Atencao" if 0 <= r <= 15 else "OK"),
                  delta_color="inverse" if 0 <= r <= 15 else "normal")
    with c3:
        st.metric("Meta Diaria", f"R$ {fin['meta_breakeven_diaria']:,.2f}",
                  delta=f"{fin['dias_operacao_mes']} dias/mes", delta_color="off")
    with c4:
        mm = status["media_movel_3d"]
        meta = fin["meta_breakeven_diaria"]
        pct = (mm / meta * 100) if meta > 0 else 0
        st.metric("Media Movel 3d", f"R$ {mm:,.2f}",
                  delta=f"{pct:.0f}% da meta", delta_color="normal" if mm >= meta else "inverse")
    with c5:
        st.metric("Dias Registrados", str(status["dias_registrados"]),
                  delta=status["ultima_atualizacao"] or "Nenhum dado", delta_color="off")


# ======================================================================
# Secao 1: Vendas (Upload + Manual + Editar)
# ======================================================================
def render_vendas(config, motor):
    st.markdown('<div class="secao-titulo">Fechamento de Caixa</div>', unsafe_allow_html=True)

    tab_csv, tab_manual, tab_editar = st.tabs([
        "Arrastar CSV", "Lancamento Manual", "Editar / Corrigir Dados"
    ])

    with tab_csv:
        uploaded = st.file_uploader(
            "Arraste o CSV de Vendas do iFood/PDV Aqui",
            type=["csv", "txt"],
            help="Aceita CSVs do iFood Analytics ou PDV",
        )
        if uploaded is not None:
            processar_csv(uploaded, config, motor)

    with tab_manual:
        with st.form("form_venda", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                fat = st.number_input("Faturamento Bruto (R$)", min_value=0.0, value=0.0, step=10.0, format="%.2f")
            with c2:
                ped = st.number_input("Pedidos", min_value=0, value=0, step=1)
            with c3:
                pct = st.slider("% Vendas Diretas", 0, 100, 30, help="Fora do iFood")
            ok = st.form_submit_button("Registrar Vendas", use_container_width=True, type="primary")
            if ok and fat > 0 and ped > 0:
                rel = motor.registrar_dia_manual(fat, ped, pct / 100)
                exibir_resultado_vendas(rel, config)
                st.rerun()

    with tab_editar:
        render_editar_historico(config, motor)


def processar_csv(uploaded, config, motor):
    try:
        temp = os.path.join(tempfile.gettempdir(), f"grillato_{datetime.now().strftime('%H%M%S')}.csv")
        with open(temp, "wb") as f:
            f.write(uploaded.getvalue())

        try:
            conteudo = uploaded.getvalue().decode("utf-8-sig")
            delim = ";" if conteudo.count(";") > conteudo.count(",") else ","
            df = pd.read_csv(io.StringIO(conteudo), delimiter=delim)
            with st.expander("Pre-visualizacao do CSV", expanded=False):
                st.dataframe(df.head(20), use_container_width=True)
                st.caption(f"{len(df)} linhas | Colunas: {', '.join(df.columns)}")
        except Exception:
            st.warning("Nao foi possivel pre-visualizar, mas o processamento continua.")

        metricas = motor.processar_csv_vendas(temp)
        rel = motor.atualizar_runway(metricas)
        exibir_resultado_vendas(rel, config)

        try:
            os.remove(temp)
        except OSError:
            pass
    except Exception as e:
        st.error(f"Erro: {e}")
        st.info("Verifique se o CSV tem colunas de valor (Valor Total, Total, Valor).")


def exibir_resultado_vendas(rel, config):
    st.markdown("---")
    meta = config["financeiro"]["meta_breakeven_diaria"]
    fat = rel["faturamento_bruto"]

    if fat >= meta:
        st.success(f"META BATIDA! R$ {fat:,.2f} ({rel['pct_meta']:.0f}% da meta)")
    else:
        st.error(f"META NAO ATINGIDA. R$ {fat:,.2f} ({rel['pct_meta']:.0f}%). Deficit: R$ {rel['deficit_hoje']:,.2f}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Faturamento", f"R$ {fat:,.2f}")
    with c2:
        st.metric("Pedidos", str(rel["total_pedidos"]))
    with c3:
        st.metric("Ticket Medio", f"R$ {rel['ticket_medio']:,.2f}")
    with c4:
        r = rel["runway_dias"]
        st.metric("Runway", f"{r} dias" if r >= 0 else "Sustentavel")


def render_editar_historico(config, motor):
    """Permite editar, remover e ajustar dados registrados."""
    historico = motor.estado.get("historico_diario", [])

    st.markdown("**Ajustar Saldo do Caixa**")
    st.caption("Use para corrigir o saldo quando houver pagamento de conta, entrada extra, ou erro.")
    c1, c2 = st.columns([2, 1])
    with c1:
        novo_saldo = st.number_input(
            "Novo saldo do caixa (R$)",
            value=float(motor.estado.get("caixa_atual", config["financeiro"]["caixa_sobrevivencia"])),
            step=100.0, format="%.2f",
            key="ajuste_caixa"
        )
    with c2:
        st.markdown("")
        st.markdown("")
        if st.button("Atualizar Saldo", key="btn_saldo", use_container_width=True):
            motor.atualizar_caixa_manual(novo_saldo)
            st.success(f"Caixa atualizado para R$ {novo_saldo:,.2f}")
            st.rerun()

    st.markdown("---")
    st.markdown("**Historico de Dias Registrados**")

    if not historico:
        st.info("Nenhum dia registrado ainda.")
        return

    # Tabela editável
    df = pd.DataFrame(historico)
    colunas_exibir = ["data", "faturamento", "deficit", "superavit", "caixa_pos", "pedidos", "ticket_medio"]
    colunas_existentes = [c for c in colunas_exibir if c in df.columns]
    df_exibir = df[colunas_existentes].copy()
    df_exibir.columns = [c.replace("_", " ").title() for c in colunas_existentes]

    st.dataframe(df_exibir, use_container_width=True, hide_index=False)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Remover Ultimo Dia Registrado", type="secondary", use_container_width=True):
            if motor.remover_ultimo_dia():
                st.success("Ultimo dia removido. Caixa e runway recalculados.")
                st.rerun()
            else:
                st.warning("Nao ha dias para remover.")
    with c2:
        if st.button("RESETAR TUDO (Voltar ao Inicio)", type="secondary", use_container_width=True):
            st.session_state["confirmar_reset"] = True

    if st.session_state.get("confirmar_reset"):
        st.warning("Tem certeza? Isso apaga todo o historico e restaura o caixa para o valor inicial.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("SIM, RESETAR", type="primary"):
                motor.limpar_historico()
                st.session_state["confirmar_reset"] = False
                st.success("Historico limpo. Caixa restaurado.")
                st.rerun()
        with c2:
            if st.button("Cancelar"):
                st.session_state["confirmar_reset"] = False
                st.rerun()


# ======================================================================
# Secao 2: Radar de Inflacao
# ======================================================================
def render_radar(config, radar):
    st.markdown('<div class="secao-titulo">Radar de Inflacao - Nota Fiscal</div>', unsafe_allow_html=True)

    tab_inserir, tab_historico = st.tabs(["Lancar Precos", "Historico de Precos"])

    with tab_inserir:
        ultimo = radar.get_ultimo_registro()
        if ultimo:
            st.caption(f"Ultima auditoria: {ultimo['data']} | CMV/lanche: R$ {ultimo.get('cmv_lanche', '?')}")

        with st.form("form_radar", clear_on_submit=False):
            st.markdown("**Precos atualizados da nota fiscal:**")
            cols = st.columns(5)
            precos = {}
            nomes = {
                "carne_kg": "Carne (R$/kg)", "cheddar_kg": "Cheddar (R$/kg)",
                "bacon_kg": "Bacon (R$/kg)", "batata_kg": "Batata (R$/kg)",
                "pao_brioche_unid": "Pao (R$/un)",
            }
            for i, (key, label) in enumerate(nomes.items()):
                ref = radar.get_preco_referencia(key)
                with cols[i]:
                    precos[key] = st.number_input(
                        label, min_value=0.01, value=ref,
                        step=0.50, format="%.2f",
                        help=f"Anterior: R$ {ref:.2f}"
                    )
            if st.form_submit_button("Auditar Nota Fiscal", use_container_width=True, type="primary"):
                resultado = radar.registrar_precos(precos)
                exibir_radar(resultado)

    with tab_historico:
        render_historico_precos(radar)


def exibir_radar(resultado):
    var = resultado["variacao_cmv"]
    if var > 0:
        st.error(f"CMV SUBIU R$ {var:.2f}/lanche. +R$ {var * 17:.2f}/dia em 17 lanches.")
    elif var < 0:
        st.success(f"CMV DESCEU R$ {abs(var):.2f}/lanche. Economia R$ {abs(var) * 17:.2f}/dia.")
    else:
        st.info("Precos estaveis.")

    linhas = []
    for dados in resultado["itens"].values():
        seta = {"vermelho": "🔴 SUBIU", "verde": "🟢 DESCEU"}.get(dados["cor"], "🟡 ESTAVEL")
        linhas.append({
            "Insumo": dados["nome"],
            "Anterior": f"R$ {dados['preco_anterior']:.2f}",
            "Novo": f"R$ {dados['preco_novo']:.2f}",
            "Variacao": f"{dados['variacao_pct']:+.1f}%",
            "Status": seta,
            "Impacto/Lanche": f"R$ {dados['impacto_lanche']:+.3f}",
        })
    st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("CMV Anterior", f"R$ {resultado['cmv_lanche_anterior']:.2f}")
    with c2:
        st.metric("CMV Novo", f"R$ {resultado['cmv_lanche_novo']:.2f}",
                  delta=f"R$ {var:+.2f}", delta_color="inverse")
    with c3:
        imp = var * 17 * 22
        st.metric("Impacto Mensal", f"R$ {imp:+,.2f}",
                  delta="custo extra" if imp > 0 else "economia",
                  delta_color="inverse" if imp > 0 else "normal")


def render_historico_precos(radar):
    """Exibe e permite limpar historico de precos."""
    hist = radar.historico
    if not hist:
        st.info("Nenhum preco registrado ainda.")
        return

    linhas = []
    for reg in hist:
        linha = {"Data": reg["data"], "CMV/Lanche": f"R$ {reg.get('cmv_lanche', 0):.2f}"}
        for key, val in reg.get("precos", {}).items():
            nome = key.replace("_kg", "").replace("_unid", "").replace("pao_brioche", "pao").title()
            linha[nome] = f"R$ {val:.2f}"
        linhas.append(linha)

    st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)

    if st.button("Limpar Historico de Precos", key="limpar_precos"):
        radar.historico = []
        radar._salvar_historico()
        st.success("Historico limpo.")
        st.rerun()


# ======================================================================
# Secao 3: Estoque
# ======================================================================
def render_estoque(config, estoque):
    st.markdown('<div class="secao-titulo">Controle de Estoque</div>', unsafe_allow_html=True)

    tab_s, tab_e, tab_b, tab_p = st.tabs([
        "Status Atual", "Entrada de Mercadoria", "Baixa por Vendas", "Projecao"
    ])

    nomes_insumos = {
        "carne_kg": "Carne (kg)", "bacon_kg": "Bacon (kg)", "cheddar_kg": "Cheddar (kg)",
        "batata_kg": "Batata (kg)", "pao_brioche_unid": "Pao Brioche (un)",
    }

    with tab_s:
        status = estoque.get_status()
        saldo = status["saldo"]
        limites = config["producao"]["estoque_seguranca"]

        if status["alertas"]:
            for a in status["alertas"]:
                st.error(f"RISCO DE RUTURA: {a['msg']}")

        cols = st.columns(5)
        for i, (key, nome) in enumerate(nomes_insumos.items()):
            with cols[i]:
                val = saldo.get(key, 0)
                lim = limites.get(key)
                if lim and val < lim:
                    st.metric(nome, f"{val:.2f}", delta="BAIXO", delta_color="inverse")
                elif val == 0:
                    st.metric(nome, "0.00", delta="VAZIO", delta_color="inverse")
                else:
                    st.metric(nome, f"{val:.2f}", delta="OK", delta_color="normal")

        if status["ultima_atualizacao"]:
            st.caption(f"Ultima atualizacao: {status['ultima_atualizacao']}")

        # Ajuste manual de estoque
        st.markdown("---")
        st.markdown("**Ajuste manual de estoque** (correcao de contagem)")
        with st.form("form_ajuste_estoque", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                ins_ajuste = st.selectbox("Insumo", list(nomes_insumos.keys()),
                                          format_func=lambda x: nomes_insumos[x], key="ajuste_ins")
            with c2:
                qtd_ajuste = st.number_input("Quantidade a DEFINIR (saldo real)", min_value=0.0,
                                              value=0.0, step=0.5, format="%.2f", key="ajuste_qtd")
            with c3:
                st.markdown("")
                st.markdown("")
            if st.form_submit_button("Definir Saldo Real", use_container_width=True):
                saldo_atual = estoque.inventario.get(ins_ajuste, 0)
                diferenca = qtd_ajuste - saldo_atual
                if diferenca > 0:
                    estoque.registrar_entrada(ins_ajuste, diferenca, "Ajuste manual")
                elif diferenca < 0:
                    estoque.inventario[ins_ajuste] = round(qtd_ajuste, 3)
                    estoque.inventario["historico_movimentos"].append({
                        "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "tipo": "ajuste_manual",
                        "insumo": ins_ajuste,
                        "saldo_anterior": saldo_atual,
                        "saldo_novo": qtd_ajuste,
                    })
                    estoque.inventario["ultima_atualizacao"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    estoque._salvar_inventario()
                st.success(f"{nomes_insumos[ins_ajuste]} ajustado para {qtd_ajuste:.2f}")
                st.rerun()

    with tab_e:
        with st.form("form_entrada", clear_on_submit=True):
            st.markdown("**Registrar entrada (nota fiscal)**")
            c1, c2, c3 = st.columns(3)
            with c1:
                ins = st.selectbox("Insumo", list(nomes_insumos.keys()),
                                   format_func=lambda x: nomes_insumos[x])
            with c2:
                qtd = st.number_input("Quantidade", min_value=0.0, step=0.5, format="%.2f")
            with c3:
                forn = st.text_input("Fornecedor", placeholder="Delly's, Frigorifico...")
            if st.form_submit_button("Registrar Entrada", use_container_width=True, type="primary"):
                if qtd > 0:
                    estoque.registrar_entrada(ins, qtd, forn)
                    st.success(f"+{qtd:.2f} {nomes_insumos[ins]} registrado.")
                    st.rerun()

    with tab_b:
        with st.form("form_baixa", clear_on_submit=True):
            st.markdown("**Baixar pelas vendas do dia**")
            c1, c2 = st.columns(2)
            with c1:
                qs = st.number_input("Smashs (70g)", min_value=0, value=0, step=1)
            with c2:
                qa = st.number_input("Altos (100g)", min_value=0, value=0, step=1)
            if st.form_submit_button("Processar Baixa", use_container_width=True, type="primary"):
                if qs > 0 or qa > 0:
                    res = estoque.processar_vendas_dia(qs, qa)
                    st.markdown(f"**{res['vendas']['total']} lanches processados**")
                    consumo = []
                    for insumo, q in res["consumo"].items():
                        consumo.append({
                            "Insumo": nomes_insumos.get(insumo, insumo),
                            "Consumido": f"{q:.3f}",
                            "Saldo": f"{res['saldo_atual'].get(insumo, 0):.3f}",
                        })
                    st.table(pd.DataFrame(consumo))
                    if res["alertas"]:
                        for a in res["alertas"]:
                            st.error(f"RUTURA: {a['msg']}")
                    else:
                        st.success("Estoque OK.")

    with tab_p:
        st.markdown("**Projecao: quantos dias o estoque aguenta?**")
        c1, c2 = st.columns(2)
        with c1:
            ms = st.number_input("Media smashs/dia", min_value=1, value=10, step=1, key="proj_s")
        with c2:
            ma = st.number_input("Media altos/dia", min_value=0, value=5, step=1, key="proj_a")
        if st.button("Calcular", use_container_width=True, type="primary"):
            proj = estoque.projetar_dias_estoque(ms, ma)
            dados = []
            for key, d in proj.items():
                if key == "gargalo":
                    continue
                dados.append({
                    "Insumo": nomes_insumos.get(key, key),
                    "Saldo": f"{d['saldo']:.2f}",
                    "Consumo/dia": f"{d['consumo_dia']:.3f}",
                    "Dias": f"{d['dias_restantes']:.1f}",
                })
            st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
            g = proj["gargalo"]
            if g["dias"] < 3:
                st.error(f"GARGALO: {g['insumo']} acaba em {g['dias']:.1f} dias!")
            elif g["dias"] < 7:
                st.warning(f"Atencao: {g['insumo']} ({g['dias']:.1f} dias)")
            else:
                st.success(f"Estoque confortavel. Gargalo: {g['insumo']} ({g['dias']:.1f} dias)")


# ======================================================================
# Secao 4: Historico + Grafico
# ======================================================================
def render_historico(motor):
    st.markdown('<div class="secao-titulo">Historico de Operacoes</div>', unsafe_allow_html=True)
    historico = motor.estado.get("historico_diario", [])
    if not historico:
        st.info("Nenhum dia registrado. Use as abas acima para comecar.")
        return

    df = pd.DataFrame(historico)
    if len(df) > 1 and "faturamento" in df.columns:
        chart = df[["data", "faturamento"]].copy()
        chart["meta"] = motor.meta_diaria
        chart = chart.set_index("data")
        st.line_chart(chart, color=["#e94560", "#27ae60"])
        st.caption("Vermelho = Faturamento | Verde = Meta diaria")

    colunas_mostrar = [c for c in ["data", "faturamento", "deficit", "superavit", "caixa_pos", "pedidos", "ticket_medio"] if c in df.columns]
    st.dataframe(df[colunas_mostrar], use_container_width=True, hide_index=True)


# ======================================================================
# Sidebar: Configuracoes Editaveis
# ======================================================================
def render_sidebar(config):
    with st.sidebar:
        st.markdown("### Grillato System")
        st.markdown(f"**{config['empresa']}**")
        st.markdown(f"*{config['cidade']}*")
        st.markdown("---")

        # Parametros editaveis
        st.markdown("**Parametros Financeiros**")
        with st.expander("Editar Parametros", expanded=False):
            fin = config["financeiro"]
            novo_custo = st.number_input("Custo Fixo Mensal", value=fin["custo_fixo_mensal"],
                                          step=100.0, format="%.2f", key="sb_custo")
            novos_dias = st.number_input("Dias Operacao/Mes", value=fin["dias_operacao_mes"],
                                          min_value=1, max_value=31, step=1, key="sb_dias")
            novo_caixa = st.number_input("Caixa Inicial", value=fin["caixa_sobrevivencia"],
                                          step=100.0, format="%.2f", key="sb_caixa")
            novo_payroll = st.number_input("Payroll Teto (%)", value=int(fin["payroll_teto_pct"] * 100),
                                            min_value=1, max_value=100, step=1, key="sb_payroll")

            if st.button("Salvar Parametros", key="sb_salvar", use_container_width=True):
                config["financeiro"]["custo_fixo_mensal"] = novo_custo
                config["financeiro"]["dias_operacao_mes"] = novos_dias
                config["financeiro"]["meta_breakeven_diaria"] = round(novo_custo / novos_dias, 2)
                config["financeiro"]["caixa_sobrevivencia"] = novo_caixa
                config["financeiro"]["payroll_teto_pct"] = novo_payroll / 100
                salvar_config(config)
                st.success(f"Salvo! Nova meta: R$ {novo_custo / novos_dias:,.2f}/dia")
                st.rerun()

        st.markdown("---")
        fin = config["financeiro"]
        st.markdown(f"""
        - Custo Fixo: **R$ {fin['custo_fixo_mensal']:,.2f}**/mes
        - Meta: **R$ {fin['meta_breakeven_diaria']:,.2f}**/dia
        - Dias: **{fin['dias_operacao_mes']}**/mes
        - Payroll: **{fin['payroll_teto_pct']*100:.0f}%**
        """)

        prod = config["producao"]
        st.markdown(f"""
        **Producao**
        - Smash: **{prod['gramatura_smash_g']}g** | Alto: **{prod['gramatura_alto_g']}g**
        - Teto: **{prod['teto_pedidos_dia']} ped/dia**
        """)
        st.markdown("---")
        st.caption(f"v2.0 | {datetime.now().strftime('%d/%m/%Y')}")


# ======================================================================
# Main
# ======================================================================
def main():
    injetar_css()
    config = carregar_config()
    motor = MotorFinanceiro(config)
    radar = RadarInflacao(config)
    estoque = GestaoEstoque(config)

    render_sidebar(config)
    render_header()

    status = motor.get_status_caixa()
    render_alerta_runway(status["runway_dias"], status["caixa_atual"])
    render_kpis(config, motor)

    st.markdown("---")
    tab_vendas, tab_compras, tab_estoque, t