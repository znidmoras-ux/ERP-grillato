"""
Grillato ERP - Dashboard Principal (Streamlit)
Sistema completo de gestao para hamburgueria.
v3.0 - Design profissional com metricas e previsoes
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from erp import db_insumos, db_produtos, db_fornecedores, db_notas_fiscais, db_pedidos, db_financeiro
from erp import db_engenharia, db_metas, db_previsao_compras, db_produtividade, db_bi
from erp.auth import render_login, render_user_info, paginas_permitidas, get_perfil_atual, PERFIS

st.set_page_config(
    page_title="Grillato ERP",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS profissional
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        color: #e94560;
        margin-bottom: 0;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #6c7293;
        margin-top: -8px;
    }
    .kpi-box {
        background: linear-gradient(135deg, #16213e 0%, #1a1a3e 100%);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2a2a5a;
        margin-bottom: 12px;
    }
    .kpi-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        color: #6c7293;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-family: 'Inter', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: #eaeaea;
    }
    .kpi-delta-up { color: #27ae60; font-size: 0.8rem; font-weight: 600; }
    .kpi-delta-down { color: #e74c3c; font-size: 0.8rem; font-weight: 600; }
    .kpi-delta-neutral { color: #f39c12; font-size: 0.8rem; font-weight: 600; }

    .alert-card {
        background: linear-gradient(135deg, #2d1b1b 0%, #1a1a2e 100%);
        border-left: 4px solid #e74c3c;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .alert-card-warn {
        background: linear-gradient(135deg, #2d2a1b 0%, #1a1a2e 100%);
        border-left: 4px solid #f39c12;
    }
    .alert-card-ok {
        background: linear-gradient(135deg, #1b2d1e 0%, #1a1a2e 100%);
        border-left: 4px solid #27ae60;
    }

    .section-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #eaeaea;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid #e94560;
        display: inline-block;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        border-radius: 8px 8px 0 0;
    }
    div[data-testid="stMetricValue"] { font-size: 1.3rem; }
    .stRadio > label { font-weight: 600; }
</style>
""", unsafe_allow_html=True)


def _gauge_chart(valor, meta, titulo, sufixo="%", cor_bom="#27ae60", cor_ruim="#e74c3c"):
    """Cria um gauge chart elegante."""
    if valor <= meta:
        cor = cor_bom
    else:
        cor = cor_ruim
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        number={"suffix": sufixo, "font": {"size": 28, "color": "#eaeaea"}},
        title={"text": titulo, "font": {"size": 13, "color": "#6c7293"}},
        gauge={
            "axis": {"range": [0, max(100, meta * 2)], "tickcolor": "#3a3a5a"},
            "bar": {"color": cor, "thickness": 0.3},
            "bgcolor": "#16213e",
            "bordercolor": "#2a2a5a",
            "steps": [
                {"range": [0, meta], "color": "rgba(39,174,96,0.1)"},
                {"range": [meta, max(100, meta * 2)], "color": "rgba(231,76,60,0.1)"},
            ],
            "threshold": {
                "line": {"color": "#f39c12", "width": 3},
                "thickness": 0.8,
                "value": meta,
            },
        },
    ))
    fig.update_layout(
        height=200, margin=dict(t=40, b=10, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)", font={"color": "#eaeaea"},
    )
    return fig


def _kpi_html(label, value, delta=None, delta_type="neutral"):
    """Gera HTML para KPI card."""
    delta_class = f"kpi-delta-{delta_type}"
    delta_html = f'<div class="{delta_class}">{delta}</div>' if delta else ""
    return f"""
    <div class="kpi-box">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """


# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🍔 GRILLATO")
        st.caption("ERP v3.0")
        st.divider()
        render_user_info()
        st.divider()

        icones = {
            "Dashboard": "📊", "Insumos": "📦", "Produtos": "🍔",
            "Fornecedores": "🏭", "Notas Fiscais": "📄", "Pedidos": "🛒",
            "Financeiro": "💰", "CMV": "📈", "Custos Fixos": "⚙️",
            "Engenharia": "🧪", "BI": "📉", "Metas": "🎯",
            "Compras": "🛍️", "Produtividade": "⏰",
        }
        permitidas = paginas_permitidas()
        opcoes = [f"{icones.get(p, '📋')} {p}" for p in permitidas]

        menu = st.radio("Menu", opcoes, label_visibility="collapsed")
        st.divider()

        # Mini status na sidebar
        try:
            alertas = db_insumos.estoque_alertas()
            criticos = len([a for a in alertas if a["status_estoque"] in ("SEM_ESTOQUE", "ABAIXO_MINIMO")]) if alertas else 0
            if criticos > 0:
                st.error(f"⚠️ {criticos} insumo(s) em alerta")
            else:
                st.success("✅ Estoque OK")
        except:
            pass

        perfil = get_perfil_atual()
        st.caption(f"📅 {date.today().strftime('%d/%m/%Y')} | {perfil}")
        return menu


# ============================================================
# DASHBOARD PRINCIPAL - REDESENHADO
# ============================================================
def render_dashboard():
    st.markdown('<p class="main-header">PAINEL DE CONTROLE</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Visao geral em tempo real da operacao Grillato</p>', unsafe_allow_html=True)

    try:
        cmv_dados = db_produtos.cmv_todos_produtos()
        alertas_est = db_insumos.estoque_alertas()
        custos_mensal = db_financeiro.total_custos_fixos_mensal()
        custo_dia = custos_mensal / 22
        fechamentos = db_financeiro.listar_fechamentos(30)

        # ---- LINHA 1: KPIs PRINCIPAIS ----
        st.markdown("")
        c1, c2, c3, c4, c5 = st.columns(5)

        total_produtos = len(cmv_dados) if cmv_dados else 0
        alertas_crit = len([a for a in alertas_est if a["status_estoque"] in ("SEM_ESTOQUE", "ABAIXO_MINIMO")]) if alertas_est else 0

        # Calcular metricas de fechamentos
        if fechamentos:
            fat_total = sum(f["faturamento_bruto"] for f in fechamentos)
            ped_total = sum(f["total_pedidos"] for f in fechamentos)
            dias = len(fechamentos)
            media_fat_dia = fat_total / dias if dias > 0 else 0
            media_ped_dia = ped_total / dias if dias > 0 else 0
            ticket_medio = fat_total / ped_total if ped_total > 0 else 0
            ultimo_fat = fechamentos[0]["faturamento_bruto"] if fechamentos else 0
            lucro_total = sum(f.get("lucro_bruto", 0) for f in fechamentos)
            margem_op = (lucro_total / fat_total * 100) if fat_total > 0 else 0
        else:
            media_fat_dia = media_ped_dia = ticket_medio = ultimo_fat = lucro_total = margem_op = 0
            dias = 0

        with c1:
            st.markdown(_kpi_html("Faturamento Medio/Dia", f"R$ {media_fat_dia:,.0f}",
                                  f"Meta: R$ {custo_dia:,.0f}", "up" if media_fat_dia >= custo_dia else "down"),
                       unsafe_allow_html=True)
        with c2:
            st.markdown(_kpi_html("Pedidos Medio/Dia", f"{media_ped_dia:.1f}",
                                  f"Meta: 25/dia", "up" if media_ped_dia >= 25 else "down"),
                       unsafe_allow_html=True)
        with c3:
            st.markdown(_kpi_html("Ticket Medio", f"R$ {ticket_medio:,.2f}",
                                  f"{ped_total} pedidos em {dias}d", "neutral"),
                       unsafe_allow_html=True)
        with c4:
            delta_type = "up" if margem_op > 0 else "down"
            st.markdown(_kpi_html("Margem Operacional", f"{margem_op:.1f}%",
                                  f"Lucro: R$ {lucro_total:,.0f}", delta_type),
                       unsafe_allow_html=True)
        with c5:
            cor_alerta = "down" if alertas_crit > 0 else "up"
            st.markdown(_kpi_html("Alertas Estoque", str(alertas_crit),
                                  f"{total_produtos} produtos ativos", cor_alerta),
                       unsafe_allow_html=True)

        # ---- LINHA 2: GAUGES + PREVISOES ----
        st.markdown('<div class="section-title">INDICADORES DE SAUDE</div>', unsafe_allow_html=True)
        g1, g2, g3, g4 = st.columns(4)

        # CMV medio
        cmv_medio = 0
        if cmv_dados:
            cmv_valores = [c["cmv_pct"] for c in cmv_dados if c.get("cmv_pct")]
            cmv_medio = sum(cmv_valores) / len(cmv_valores) if cmv_valores else 0

        with g1:
            fig = _gauge_chart(cmv_medio, 35, "CMV MEDIO")
            st.plotly_chart(fig, use_container_width=True)

        with g2:
            # Ocupacao da capacidade (17 pedidos/dia = 100%)
            ocup = (media_ped_dia / 17 * 100) if media_ped_dia > 0 else 0
            fig = _gauge_chart(min(ocup, 100), 80, "CAPACIDADE", cor_bom="#3498db", cor_ruim="#27ae60")
            st.plotly_chart(fig, use_container_width=True)

        with g3:
            # Payroll ratio
            if fat_total > 0 and dias > 0:
                folha_mensal = sum(c["valor"] for c in db_financeiro.listar_custos_fixos() if c.get("categoria") == "funcionario")
                fat_mensal_proj = media_fat_dia * 22
                payroll_pct = (folha_mensal / fat_mensal_proj * 100) if fat_mensal_proj > 0 else 0
            else:
                payroll_pct = 0
            fig = _gauge_chart(payroll_pct, 30, "FOLHA / FAT")
            st.plotly_chart(fig, use_container_width=True)

        with g4:
            # Break-even progress
            if media_fat_dia > 0:
                be_pct = min(100, media_fat_dia / custo_dia * 100)
            else:
                be_pct = 0
            fig = _gauge_chart(be_pct, 100, "BREAK-EVEN", cor_bom="#27ae60", cor_ruim="#e74c3c")
            st.plotly_chart(fig, use_container_width=True)

        # ---- LINHA 3: GRAFICOS ----
        st.markdown('<div class="section-title">EVOLUCAO & PREVISOES</div>', unsafe_allow_html=True)

        if fechamentos and len(fechamentos) >= 2:
            col_chart1, col_chart2 = st.columns(2)

            df_fech = pd.DataFrame(fechamentos)
            df_fech = df_fech.sort_values("data")

            with col_chart1:
                # Grafico de faturamento com tendencia
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_fech["data"], y=df_fech["faturamento_bruto"],
                    name="Faturamento", line=dict(color="#3498db", width=2),
                    fill="tozeroy", fillcolor="rgba(52,152,219,0.1)",
                ))
                if "lucro_bruto" in df_fech.columns:
                    fig.add_trace(go.Scatter(
                        x=df_fech["data"], y=df_fech["lucro_bruto"],
                        name="Lucro", line=dict(color="#27ae60", width=2),
                        fill="tozeroy", fillcolor="rgba(39,174,96,0.1)",
                    ))
                # Linha de break-even
                fig.add_hline(y=custo_dia, line_dash="dash", line_color="#e74c3c",
                              annotation_text=f"Break-even R${custo_dia:.0f}")

                # Previsao 7 dias (media movel)
                if len(df_fech) >= 3:
                    media = df_fech["faturamento_bruto"].rolling(3, min_periods=1).mean().iloc[-1]
                    datas_futuras = [df_fech["data"].iloc[-1]]
                    for i in range(1, 8):
                        prox = (datetime.strptime(str(datas_futuras[0]), "%Y-%m-%d") + timedelta(days=i)).strftime("%Y-%m-%d")
                        datas_futuras.append(prox)
                    fig.add_trace(go.Scatter(
                        x=datas_futuras, y=[media] * len(datas_futuras),
                        name=f"Previsao (R${media:.0f}/dia)",
                        line=dict(color="#f39c12", width=2, dash="dot"),
                    ))

                fig.update_layout(
                    title="Faturamento vs Break-even",
                    height=320, margin=dict(t=40, b=40, l=40, r=20),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#8a8a9a"), legend=dict(orientation="h", y=-0.2),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_chart2:
                # Grafico de pedidos por dia
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=df_fech["data"], y=df_fech["total_pedidos"],
                    name="Pedidos", marker_color="#e94560",
                    marker=dict(cornerradius=4),
                ))
                fig2.add_hline(y=17, line_dash="dash", line_color="#f39c12",
                               annotation_text="Teto: 17/dia")
                fig2.add_hline(y=25, line_dash="dash", line_color="#27ae60",
                               annotation_text="Meta: 25/dia")
                fig2.update_layout(
                    title="Pedidos por Dia",
                    height=320, margin=dict(t=40, b=40, l=40, r=20),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#8a8a9a"),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("📊 Registre fechamentos diarios para ver graficos e previsoes.")

        # ---- LINHA 4: CMV + ESTOQUE ----
        st.markdown('<div class="section-title">PRODUTOS & ESTOQUE</div>', unsafe_allow_html=True)

        col_cmv, col_est = st.columns(2)

        with col_cmv:
            if cmv_dados:
                df_cmv = pd.DataFrame(cmv_dados).sort_values("lucro", ascending=True)
                fig3 = go.Figure()
                cores = ["#27ae60" if c < 30 else "#f39c12" if c < 40 else "#e74c3c" for c in df_cmv["cmv_pct"]]
                fig3.add_trace(go.Bar(
                    y=df_cmv["nome"], x=df_cmv["lucro"],
                    orientation="h", marker_color=cores,
                    text=[f"R${l:.2f} | CMV {c:.0f}%" for l, c in zip(df_cmv["lucro"], df_cmv["cmv_pct"])],
                    textposition="auto",
                ))
                fig3.update_layout(
                    title="Ranking de Lucratividade",
                    height=300, margin=dict(t=40, b=20, l=100, r=20),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#8a8a9a"),
                    xaxis=dict(title="Lucro R$", gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                )
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Cadastre produtos para ver o ranking.")

        with col_est:
            if alertas_est:
                st.markdown("**Status do Estoque**")
                for a in alertas_est:
                    status = a["status_estoque"]
                    icon = {"SEM_ESTOQUE": "🔴", "ABAIXO_MINIMO": "🟠", "ATENCAO": "🟡", "OK": "🟢"}.get(status, "⚪")
                    card_class = "alert-card" if status == "SEM_ESTOQUE" else "alert-card-warn" if status in ("ABAIXO_MINIMO", "ATENCAO") else "alert-card-ok"
                    pct = (a["estoque_atual"] / a["estoque_minimo"] * 100) if a["estoque_minimo"] > 0 else 100
                    st.markdown(f"""
                    <div class="{card_class}">
                        <strong>{icon} {a['nome']}</strong> — {a['estoque_atual']:.1f} {a['unidade_compra']}
                        <span style="float:right; color:#6c7293">{pct:.0f}% do minimo</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Cadastre insumos para monitorar estoque.")

        # ---- LINHA 5: PREVISOES INTELIGENTES ----
        st.markdown('<div class="section-title">PREVISOES & ALERTAS</div>', unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)

        with p1:
            # Previsao de faturamento mensal
            if media_fat_dia > 0:
                fat_proj_mes = media_fat_dia * 22
                meta_min = 35000
                meta_max = 45000
                pct_meta = fat_proj_mes / meta_min * 100
                cor_proj = "#27ae60" if fat_proj_mes >= meta_min else "#e74c3c"
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-label">PROJECAO MENSAL</div>
                    <div class="kpi-value" style="color:{cor_proj}">R$ {fat_proj_mes:,.0f}</div>
                    <div style="color:#6c7293; font-size:0.8rem; margin-top:4px">
                        Meta: R$ {meta_min:,.0f} - R$ {meta_max:,.0f}<br>
                        {pct_meta:.0f}% da meta minima
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(_kpi_html("PROJECAO MENSAL", "Sem dados", "Registre vendas"), unsafe_allow_html=True)

        with p2:
            # Runway
            try:
                caixa = 9502.88  # Valor base - deve vir do ultimo fechamento
                if fechamentos and fechamentos[0].get("caixa_apos"):
                    caixa = fechamentos[0]["caixa_apos"]
                runway = db_financeiro.calcular_runway(caixa)
                cor_run = "#e74c3c" if runway["runway_dias"] < 15 else "#f39c12" if runway["runway_dias"] < 30 else "#27ae60"
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-label">RUNWAY (SOBREVIVENCIA)</div>
                    <div class="kpi-value" style="color:{cor_run}">{runway['runway_dias']} dias</div>
                    <div style="color:#6c7293; font-size:0.8rem; margin-top:4px">
                        Caixa: R$ {caixa:,.2f}<br>
                        Deficit/dia: R$ {runway['deficit_dia']:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(_kpi_html("RUNWAY", "—", str(e)[:40]), unsafe_allow_html=True)

        with p3:
            # Previsao de necessidade de compra
            if alertas_est:
                criticos = [a for a in alertas_est if a["status_estoque"] in ("SEM_ESTOQUE", "ABAIXO_MINIMO")]
                atencao = [a for a in alertas_est if a["status_estoque"] == "ATENCAO"]
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-label">NECESSIDADE DE COMPRA</div>
                    <div class="kpi-value">{"🔴 URGENTE" if criticos else "🟡 ATENÇÃO" if atencao else "🟢 OK"}</div>
                    <div style="color:#6c7293; font-size:0.8rem; margin-top:4px">
                        {len(criticos)} critico(s) | {len(atencao)} atencao<br>
                        {len(alertas_est)} insumos monitorados
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(_kpi_html("COMPRAS", "Sem dados", "Cadastre insumos"), unsafe_allow_html=True)

    except Exception as e:
        st.info("📋 Configure a conexao com o Supabase para ver os dados.")
        st.caption(f"Detalhes: {e}")


# ============================================================
# INSUMOS
# ============================================================
def render_insumos():
    st.markdown('<p class="main-header">INSUMOS</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Cadastro de ingredientes, embalagens e materiais</p>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Lista", "➕ Cadastrar", "📦 Estoque", "📊 Movimentacoes"])

    with tab1:
        try:
            insumos = db_insumos.listar_insumos()
            if insumos:
                df = pd.DataFrame(insumos)
                colunas = ["nome", "unidade_compra", "unidade_uso", "custo_unitario",
                          "estoque_atual", "estoque_minimo"]
                colunas_existentes = [c for c in colunas if c in df.columns]
                st.dataframe(
                    df[colunas_existentes],
                    use_container_width=True, hide_index=True,
                    column_config={
                        "nome": "Insumo",
                        "unidade_compra": "Un. Compra",
                        "unidade_uso": "Un. Uso",
                        "custo_unitario": st.column_config.NumberColumn("Custo Unit.", format="R$ %.4f"),
                        "estoque_atual": st.column_config.NumberColumn("Estoque", format="%.3f"),
                        "estoque_minimo": st.column_config.NumberColumn("Minimo", format="%.3f"),
                    }
                )

                st.markdown('<div class="section-title">EDITAR INSUMO</div>', unsafe_allow_html=True)
                nomes = {i["nome"]: i["id"] for i in insumos}
                sel = st.selectbox("Selecione o insumo", list(nomes.keys()), key="edit_insumo")
                if sel:
                    insumo = db_insumos.buscar_insumo(nomes[sel])
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        novo_custo = st.number_input("Custo unitario", value=float(insumo.get("custo_unitario", 0)), format="%.4f", key="ed_custo")
                    with col2:
                        novo_estoque = st.number_input("Estoque atual", value=float(insumo.get("estoque_atual", 0)), format="%.3f", key="ed_est")
                    with col3:
                        novo_minimo = st.number_input("Estoque minimo", value=float(insumo.get("estoque_minimo", 0)), format="%.3f", key="ed_min")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("💾 Salvar", type="primary", key="btn_salvar_insumo"):
                            db_insumos.atualizar_insumo(nomes[sel], {
                                "custo_unitario": novo_custo, "estoque_atual": novo_estoque, "estoque_minimo": novo_minimo,
                            })
                            st.success("Insumo atualizado!")
                            st.rerun()
                    with col_b:
                        if st.button("🗑️ Desativar", key="btn_desativar_insumo"):
                            db_insumos.desativar_insumo(nomes[sel])
                            st.success("Desativado!")
                            st.rerun()
            else:
                st.info("Nenhum insumo cadastrado.")
        except Exception as e:
            st.info("Configure o Supabase para gerenciar insumos.")
            st.caption(str(e))

    with tab2:
        st.markdown('<div class="section-title">NOVO INSUMO</div>', unsafe_allow_html=True)
        try:
            categorias = db_insumos.listar_categorias_insumo()
            cat_map = {c["nome"]: c["id"] for c in categorias} if categorias else {}
            fornecedores = db_fornecedores.listar_fornecedores()
            forn_map = {f["nome"]: f["id"] for f in fornecedores} if fornecedores else {}
        except:
            cat_map = {}
            forn_map = {}

        with st.form("form_novo_insumo"):
            nome = st.text_input("Nome do insumo *")
            col1, col2 = st.columns(2)
            with col1:
                categoria = st.selectbox("Categoria", [""] + list(cat_map.keys()))
                unidade_compra = st.selectbox("Unidade de compra", ["kg", "unid", "litro", "pacote", "caixa"])
                custo_un = st.number_input("Custo unitario (por un. uso)", min_value=0.0, format="%.4f")
            with col2:
                fornecedor = st.selectbox("Fornecedor principal", [""] + list(forn_map.keys()))
                unidade_uso = st.selectbox("Unidade de uso", ["g", "ml", "unid"])
                fator = st.number_input("Fator de conversao", value=1000.0, help="Ex: 1kg = 1000g")
            col3, col4 = st.columns(2)
            with col3:
                estoque = st.number_input("Estoque inicial", min_value=0.0, format="%.3f")
            with col4:
                est_min = st.number_input("Estoque minimo", min_value=0.0, format="%.3f")

            if st.form_submit_button("Cadastrar Insumo", type="primary"):
                if nome:
                    dados = {
                        "nome": nome, "unidade_compra": unidade_compra, "unidade_uso": unidade_uso,
                        "fator_conversao": fator, "custo_unitario": custo_un,
                        "estoque_atual": estoque, "estoque_minimo": est_min,
                    }
                    if categoria and categoria in cat_map:
                        dados["categoria_id"] = cat_map[categoria]
                    if fornecedor and fornecedor in forn_map:
                        dados["fornecedor_principal_id"] = forn_map[fornecedor]
                    try:
                        db_insumos.criar_insumo(dados)
                        st.success(f"✅ {nome} cadastrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.warning("Preencha o nome.")

    with tab3:
        st.markdown('<div class="section-title">ALERTAS DE ESTOQUE</div>', unsafe_allow_html=True)
        try:
            alertas = db_insumos.estoque_alertas()
            if alertas:
                for a in alertas:
                    status = a["status_estoque"]
                    icon = {"SEM_ESTOQUE": "🔴", "ABAIXO_MINIMO": "🟠", "ATENCAO": "🟡", "OK": "🟢"}.get(status, "⚪")
                    card_class = "alert-card" if status in ("SEM_ESTOQUE", "ABAIXO_MINIMO") else "alert-card-warn" if status == "ATENCAO" else "alert-card-ok"
                    st.markdown(f'<div class="{card_class}"><strong>{icon} {a["nome"]}</strong> — {a["estoque_atual"]:.1f} {a["unidade_compra"]} (min: {a["estoque_minimo"]})</div>', unsafe_allow_html=True)

                st.markdown('<div class="section-title">AJUSTE RAPIDO</div>', unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    insumo_sel = st.selectbox("Insumo", [a["nome"] for a in alertas], key="ajuste_sel")
                with col2:
                    qtd_ajuste = st.number_input("Quantidade (+/-)", format="%.3f", key="ajuste_qtd")
                with col3:
                    obs_ajuste = st.text_input("Observacao", key="ajuste_obs")
                if st.button("Aplicar Ajuste", key="btn_ajuste"):
                    insumo_id = next(a["id"] for a in alertas if a["nome"] == insumo_sel)
                    db_insumos.ajustar_estoque(insumo_id, qtd_ajuste, obs_ajuste)
                    st.success("Estoque ajustado!")
                    st.rerun()

                st.markdown('<div class="section-title">REGISTRAR PERDA</div>', unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    insumo_perda = st.selectbox("Insumo", [a["nome"] for a in alertas], key="perda_sel")
                with col2:
                    qtd_perda = st.number_input("Quantidade perdida", min_value=0.0, format="%.3f", key="perda_qtd")
                with col3:
                    motivo = st.text_input("Motivo", key="perda_motivo")
                if st.button("Registrar Perda", key="btn_perda"):
                    insumo_id = next(a["id"] for a in alertas if a["nome"] == insumo_perda)
                    db_insumos.registrar_perda(insumo_id, qtd_perda, motivo)
                    st.success("Perda registrada.")
                    st.rerun()
            else:
                st.info("Cadastre insumos para ver alertas.")
        except Exception as e:
            st.caption(str(e))

    with tab4:
        try:
            movs = db_insumos.historico_movimentacoes()
            if movs:
                st.dataframe(pd.DataFrame(movs), use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma movimentacao registrada.")
        except Exception as e:
            st.caption(str(e))


# ============================================================
# PRODUTOS & FICHAS TECNICAS
# ============================================================
def render_produtos():
    st.markdown('<p class="main-header">PRODUTOS & FICHAS TECNICAS</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Cardapio", "➕ Novo Produto", "📑 Ficha Tecnica"])

    with tab1:
        try:
            produtos = db_produtos.listar_produtos()
            cmv = db_produtos.cmv_todos_produtos()
            cmv_map = {c["produto_id"]: c for c in cmv} if cmv else {}

            if produtos:
                for p in produtos:
                    c = cmv_map.get(p["id"], {})
                    cmv_pct = c.get("cmv_pct", 0)
                    cor = "🟢" if cmv_pct < 30 else "🟡" if cmv_pct < 40 else "🔴"
                    with st.expander(f"{cor} {p['nome']} — R$ {p['preco_venda']:.2f} | Lucro R$ {c.get('lucro', 0):.2f} | CMV {cmv_pct:.0f}%"):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Venda", f"R$ {p['preco_venda']:.2f}")
                        with col2:
                            st.metric("Custo", f"R$ {c.get('custo_total', 0):.2f}")
                        with col3:
                            st.metric("Lucro", f"R$ {c.get('lucro', 0):.2f}")
                        with col4:
                            st.metric("CMV", f"{cmv_pct:.1f}%")

                        novo_preco = st.number_input("Novo preco", value=float(p["preco_venda"]), format="%.2f", key=f"preco_{p['id']}")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("Salvar Preco", key=f"btn_preco_{p['id']}"):
                                db_produtos.atualizar_produto(p["id"], {"preco_venda": novo_preco})
                                st.success("Atualizado!")
                                st.rerun()
                        with col_b:
                            if st.button("Desativar", key=f"btn_desat_{p['id']}"):
                                db_produtos.desativar_produto(p["id"])
                                st.rerun()

                        ficha = db_produtos.listar_ficha_tecnica(p["id"])
                        if ficha:
                            st.caption("**Ficha Tecnica:**")
                            for ing in ficha:
                                ins = ing.get("insumos", {})
                                custo_ing = float(ing["quantidade"]) * float(ins.get("custo_unitario", 0))
                                st.text(f"  • {ins.get('nome', '?')} — {ing['quantidade']}{ins.get('unidade_uso', 'g')} (R$ {custo_ing:.3f})")
            else:
                st.info("Nenhum produto cadastrado.")
        except Exception as e:
            st.caption(str(e))

    with tab2:
        st.markdown('<div class="section-title">CADASTRAR PRODUTO</div>', unsafe_allow_html=True)
        try:
            categorias = db_produtos.listar_categorias_produto()
            cat_map = {c["nome"]: c["id"] for c in categorias} if categorias else {}
        except:
            cat_map = {}

        with st.form("form_novo_produto"):
            nome = st.text_input("Nome do produto *")
            col1, col2 = st.columns(2)
            with col1:
                preco = st.number_input("Preco de venda (R$) *", min_value=0.0, format="%.2f")
                categoria = st.selectbox("Categoria", [""] + list(cat_map.keys()))
            with col2:
                descricao = st.text_area("Descricao")
            if st.form_submit_button("Cadastrar Produto", type="primary"):
                if nome and preco > 0:
                    dados = {"nome": nome, "preco_venda": preco, "descricao": descricao}
                    if categoria and categoria in cat_map:
                        dados["categoria_id"] = cat_map[categoria]
                    try:
                        db_produtos.criar_produto(dados)
                        st.success(f"✅ {nome} cadastrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Preencha nome e preco.")

    with tab3:
        st.markdown('<div class="section-title">MONTAR FICHA TECNICA</div>', unsafe_allow_html=True)
        try:
            produtos = db_produtos.listar_produtos()
            insumos = db_insumos.listar_insumos()
            if produtos and insumos:
                prod_map = {p["nome"]: p["id"] for p in produtos}
                ins_map = {i["nome"]: i for i in insumos}
                produto_sel = st.selectbox("Produto", list(prod_map.keys()))
                if produto_sel:
                    produto_id = prod_map[produto_sel]
                    ficha_atual = db_produtos.listar_ficha_tecnica(produto_id)

                    if ficha_atual:
                        st.caption("**Ingredientes atuais:**")
                        for ing in ficha_atual:
                            ins = ing.get("insumos", {})
                            col1, col2, col3 = st.columns([3, 2, 1])
                            with col1:
                                st.text(f"{ins.get('nome', '?')}")
                            with col2:
                                nova_qtd = st.number_input(f"Qtd ({ins.get('unidade_uso', 'g')})", value=float(ing["quantidade"]), format="%.2f", key=f"ficha_{ing['id']}")
                                if nova_qtd != ing["quantidade"]:
                                    if st.button("Salvar", key=f"btn_ficha_{ing['id']}"):
                                        db_produtos.atualizar_gramatura(produto_id, ing["insumo_id"], nova_qtd)
                                        st.rerun()
                            with col3:
                                if st.button("❌", key=f"rm_ficha_{ing['id']}"):
                                    db_produtos.remover_ingrediente_ficha(produto_id, ing["insumo_id"])
                                    st.rerun()

                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        novo_ins = st.selectbox("Insumo", list(ins_map.keys()), key="add_ins")
                    with col2:
                        ins_info = ins_map.get(novo_ins, {})
                        nova_qtd = st.number_input(f"Quantidade ({ins_info.get('unidade_uso', 'g')})", min_value=0.0, format="%.2f", key="add_qtd")
                    with col3:
                        modo = st.text_input("Modo preparo", key="add_modo")
                    if st.button("➕ Adicionar", type="primary"):
                        if nova_qtd > 0:
                            db_produtos.adicionar_ingrediente_ficha(produto_id, ins_info["id"], nova_qtd, modo)
                            st.success("Adicionado!")
                            st.rerun()
            else:
                st.info("Cadastre produtos e insumos primeiro.")
        except Exception as e:
            st.caption(str(e))


# ============================================================
# FORNECEDORES
# ============================================================
def render_fornecedores():
    st.markdown('<p class="main-header">FORNECEDORES</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Lista", "➕ Cadastrar"])

    with tab1:
        try:
            fornecedores = db_fornecedores.listar_fornecedores()
            if fornecedores:
                for f in fornecedores:
                    with st.expander(f"🏭 {f['nome']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nome = st.text_input("Nome", value=f["nome"], key=f"fn_{f['id']}")
                            contato = st.text_input("Contato", value=f.get("contato", "") or "", key=f"fc_{f['id']}")
                            telefone = st.text_input("Telefone", value=f.get("telefone", "") or "", key=f"ft_{f['id']}")
                        with col2:
                            email = st.text_input("Email", value=f.get("email", "") or "", key=f"fe_{f['id']}")
                            endereco = st.text_input("Endereco", value=f.get("endereco", "") or "", key=f"fend_{f['id']}")
                            obs = st.text_area("Observacoes", value=f.get("observacoes", "") or "", key=f"fo_{f['id']}")

                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("💾 Salvar", key=f"btn_forn_{f['id']}"):
                                db_fornecedores.atualizar_fornecedor(f["id"], {
                                    "nome": nome, "contato": contato, "telefone": telefone,
                                    "email": email, "endereco": endereco, "observacoes": obs,
                                })
                                st.success("Atualizado!")
                                st.rerun()
                        with col_b:
                            if st.button("🗑️ Desativar", key=f"btn_desat_forn_{f['id']}"):
                                db_fornecedores.desativar_fornecedor(f["id"])
                                st.rerun()
            else:
                st.info("Nenhum fornecedor cadastrado.")
        except Exception as e:
            st.caption(str(e))

    with tab2:
        with st.form("form_novo_fornecedor"):
            nome = st.text_input("Nome *")
            col1, col2 = st.columns(2)
            with col1:
                contato = st.text_input("Contato")
                telefone = st.text_input("Telefone")
            with col2:
                email = st.text_input("Email")
                endereco = st.text_input("Endereco")
            obs = st.text_area("Observacoes")
            if st.form_submit_button("Cadastrar", type="primary"):
                if nome:
                    try:
                        db_fornecedores.criar_fornecedor({
                            "nome": nome, "contato": contato, "telefone": telefone,
                            "email": email, "endereco": endereco, "observacoes": obs,
                        })
                        st.success(f"✅ {nome} cadastrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))


# ============================================================
# NOTAS FISCAIS
# ============================================================
def render_notas_fiscais():
    st.markdown('<p class="main-header">NOTAS FISCAIS</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Historico", "➕ Registrar NF"])

    with tab1:
        try:
            notas = db_notas_fiscais.listar_notas()
            if notas:
                for nf in notas:
                    forn_nome = nf.get("fornecedores", {}).get("nome", "—") if nf.get("fornecedores") else "—"
                    with st.expander(f"📄 NF {nf.get('numero_nf', '—')} — {forn_nome} — R$ {nf['valor_total']:.2f} — {nf['data_emissao']}"):
                        detalhes = db_notas_fiscais.buscar_nota(nf["id"])
                        if detalhes.get("itens"):
                            st.dataframe(pd.DataFrame(detalhes["itens"]), use_container_width=True, hide_index=True)
                        if st.button("🗑️ Excluir NF", key=f"del_nf_{nf['id']}"):
                            db_notas_fiscais.deletar_nota(nf["id"])
                            st.success("NF excluida.")
                            st.rerun()
            else:
                st.info("Nenhuma nota fiscal registrada.")
        except Exception as e:
            st.caption(str(e))

    with tab2:
        st.markdown('<div class="section-title">REGISTRAR NOTA FISCAL</div>', unsafe_allow_html=True)
        try:
            fornecedores = db_fornecedores.listar_fornecedores()
            forn_map = {f["nome"]: f["id"] for f in fornecedores} if fornecedores else {}
            insumos = db_insumos.listar_insumos()
            ins_map = {i["nome"]: i for i in insumos} if insumos else {}
        except:
            forn_map = {}
            ins_map = {}

        with st.form("form_nf"):
            col1, col2, col3 = st.columns(3)
            with col1:
                numero_nf = st.text_input("Numero NF")
            with col2:
                fornecedor = st.selectbox("Fornecedor", [""] + list(forn_map.keys()))
            with col3:
                data_nf = st.date_input("Data", value=date.today())

            num_itens = st.number_input("Quantidade de itens", min_value=1, max_value=20, value=1)
            itens_nf = []
            valor_total_calc = 0
            for idx in range(int(num_itens)):
                st.caption(f"**Item {idx + 1}**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    insumo = st.selectbox("Insumo", [""] + list(ins_map.keys()), key=f"nf_ins_{idx}")
                with col2:
                    qtd = st.number_input("Quantidade", min_value=0.0, format="%.3f", key=f"nf_qtd_{idx}")
                with col3:
                    valor_un = st.number_input("Valor unitario (R$)", min_value=0.0, format="%.2f", key=f"nf_val_{idx}")
                if insumo and qtd > 0 and valor_un > 0:
                    vt = round(qtd * valor_un, 2)
                    valor_total_calc += vt
                    itens_nf.append({"insumo_id": ins_map[insumo]["id"], "quantidade": qtd, "valor_unitario": valor_un, "valor_total": vt})

            st.metric("Total calculado", f"R$ {valor_total_calc:.2f}")
            if st.form_submit_button("Registrar NF", type="primary"):
                if itens_nf and fornecedor:
                    try:
                        dados_nf = {"numero_nf": numero_nf, "fornecedor_id": forn_map.get(fornecedor), "data_emissao": data_nf.isoformat(), "valor_total": valor_total_calc}
                        db_notas_fiscais.registrar_nota_fiscal(dados_nf, itens_nf)
                        st.success("✅ NF registrada! Estoque e custos atualizados.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Preencha fornecedor e itens.")


# ============================================================
# PEDIDOS
# ============================================================
def render_pedidos():
    st.markdown('<p class="main-header">PEDIDOS</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Historico", "➕ Novo Pedido", "📊 Por Canal"])

    with tab1:
        try:
            pedidos = db_pedidos.listar_pedidos()
            if pedidos:
                df = pd.DataFrame(pedidos)
                colunas = ["data_pedido", "numero_pedido", "canal", "total", "status"]
                colunas_existentes = [c for c in colunas if c in df.columns]
                st.dataframe(df[colunas_existentes], use_container_width=True, hide_index=True,
                            column_config={"total": st.column_config.NumberColumn("Total", format="R$ %.2f")})
                st.markdown('<div class="section-title">EXCLUIR PEDIDO</div>', unsafe_allow_html=True)
                pedido_ids = {f"{p.get('numero_pedido', '—')} ({str(p['data_pedido'])[:10]}) R${p['total']:.2f}": p["id"] for p in pedidos}
                sel = st.selectbox("Selecione", list(pedido_ids.keys()), key="del_pedido")
                if st.button("🗑️ Excluir", key="btn_del_pedido"):
                    db_pedidos.deletar_pedido(pedido_ids[sel])
                    st.success("Excluido.")
                    st.rerun()
            else:
                st.info("Nenhum pedido registrado.")
        except Exception as e:
            st.caption(str(e))

    with tab2:
        st.markdown('<div class="section-title">REGISTRAR PEDIDO</div>', unsafe_allow_html=True)
        try:
            produtos = db_produtos.listar_produtos()
            prod_map = {p["nome"]: p for p in produtos} if produtos else {}
        except:
            prod_map = {}

        with st.form("form_pedido"):
            col1, col2, col3 = st.columns(3)
            with col1:
                numero = st.text_input("No Pedido")
            with col2:
                canal = st.selectbox("Canal", ["balcao", "ifood", "anota_ai", "whatsapp", "direto"])
            with col3:
                taxa_ent = st.number_input("Taxa entrega", min_value=0.0, format="%.2f")

            num_itens = st.number_input("Qtd itens", min_value=1, max_value=15, value=1, key="ped_num")
            itens_ped = []
            subtotal = 0
            for idx in range(int(num_itens)):
                col1, col2 = st.columns(2)
                with col1:
                    prod = st.selectbox("Produto", [""] + list(prod_map.keys()), key=f"ped_prod_{idx}")
                with col2:
                    qtd = st.number_input("Qtd", min_value=1, value=1, key=f"ped_qtd_{idx}")
                if prod and prod in prod_map:
                    preco = prod_map[prod]["preco_venda"]
                    total_item = preco * qtd
                    subtotal += total_item
                    itens_ped.append({"produto_id": prod_map[prod]["id"], "quantidade": qtd, "preco_unitario": preco, "preco_total": total_item})

            taxa_plat = st.number_input("Taxa plataforma (R$)", min_value=0.0, format="%.2f")
            desconto = st.number_input("Desconto (R$)", min_value=0.0, format="%.2f")
            total_pedido = subtotal + taxa_ent - desconto
            st.metric("Total", f"R$ {total_pedido:.2f}")
            if st.form_submit_button("Registrar Pedido", type="primary"):
                if itens_ped:
                    try:
                        dados = {"numero_pedido": numero, "canal": canal, "subtotal": subtotal,
                                "taxa_entrega": taxa_ent, "taxa_plataforma": taxa_plat, "desconto": desconto, "total": total_pedido}
                        db_pedidos.registrar_pedido(dados, itens_ped)
                        st.success("✅ Pedido registrado! Estoque atualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tab3:
        try:
            col1, col2 = st.columns(2)
            with col1:
                di = st.date_input("De", value=date.today() - timedelta(days=30), key="canal_di")
            with col2:
                df_data = st.date_input("Ate", value=date.today(), key="canal_df")
            resumo = db_pedidos.vendas_por_canal(di.isoformat(), df_data.isoformat())
            if resumo:
                dados_chart = [{"Canal": k, "Total": v["total"], "Pedidos": v["qtd"]} for k, v in resumo.items()]
                df = pd.DataFrame(dados_chart)
                fig = px.pie(df, values="Total", names="Canal", title="Faturamento por Canal",
                            color_discrete_sequence=["#e94560", "#3498db", "#27ae60", "#f39c12", "#9b59b6"])
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#8a8a9a"))
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.caption(str(e))


# ============================================================
# FINANCEIRO
# ============================================================
def render_financeiro():
    st.markdown('<p class="main-header">FINANCEIRO</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Runway", "📅 Fechamento Diario", "📈 Historico"])

    with tab1:
        st.markdown('<div class="section-title">ANALISE DE RUNWAY</div>', unsafe_allow_html=True)
        caixa = st.number_input("Caixa atual (R$)", value=9502.88, format="%.2f")
        if st.button("Calcular Runway", type="primary"):
            try:
                r = db_financeiro.calcular_runway(caixa)
                cor = "#e74c3c" if r["risco"] == "CRITICO" else "#f39c12" if r["risco"] == "ALERTA" else "#27ae60"
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(_kpi_html("RUNWAY", f"{r['runway_dias']} dias", r["risco"], "down" if r["risco"] == "CRITICO" else "up"), unsafe_allow_html=True)
                with c2:
                    st.markdown(_kpi_html("CUSTO FIXO/DIA", f"R$ {r['custo_fixo_dia']:.2f}", f"Mensal: R$ {r['custo_fixo_mensal']:,.2f}"), unsafe_allow_html=True)
                with c3:
                    st.markdown(_kpi_html("MEDIA FAT. 7D", f"R$ {r['media_faturamento_7d']:.2f}", f"Deficit: R$ {r['deficit_dia']:.2f}/dia", "down" if r["deficit_dia"] > 0 else "up"), unsafe_allow_html=True)

                fig = _gauge_chart(min(r["runway_dias"], 90), 30, "DIAS DE SOBREVIVENCIA", " dias")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.caption(str(e))

    with tab2:
        st.markdown('<div class="section-title">FECHAMENTO DO DIA</div>', unsafe_allow_html=True)
        with st.form("form_fechamento"):
            data_fech = st.date_input("Data", value=date.today())
            col1, col2, col3 = st.columns(3)
            with col1:
                fat = st.number_input("Faturamento bruto (R$)", min_value=0.0, format="%.2f")
                ped_total = st.number_input("Total de pedidos", min_value=0, value=0)
            with col2:
                ped_direto = st.number_input("Pedidos diretos", min_value=0, value=0)
                ped_ifood = st.number_input("Pedidos iFood", min_value=0, value=0)
            with col3:
                custo_ins = st.number_input("Custo insumos do dia (R$)", min_value=0.0, format="%.2f")
                taxas = st.number_input("Taxas plataforma (R$)", min_value=0.0, format="%.2f")
            caixa_pos = st.number_input("Caixa apos fechamento (R$)", format="%.2f")
            obs = st.text_input("Observacoes")

            if st.form_submit_button("Registrar Fechamento", type="primary"):
                try:
                    custos_dia = db_financeiro.total_custos_fixos_mensal() / 22
                    lucro = fat - custo_ins - custos_dia - taxas
                    db_financeiro.registrar_fechamento({
                        "data": data_fech.isoformat(), "faturamento_bruto": fat,
                        "total_pedidos": ped_total, "pedidos_direto": ped_direto,
                        "pedidos_ifood": ped_ifood, "pedidos_outros": ped_total - ped_direto - ped_ifood,
                        "custo_insumos": custo_ins, "custo_fixo_dia": round(custos_dia, 2),
                        "taxas_plataforma": taxas, "lucro_bruto": round(lucro, 2),
                        "caixa_apos": caixa_pos, "observacoes": obs,
                    })
                    st.success("✅ Fechamento registrado!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tab3:
        try:
            fechamentos = db_financeiro.listar_fechamentos()
            if fechamentos:
                df = pd.DataFrame(fechamentos).sort_values("data")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["data"], y=df["faturamento_bruto"], name="Faturamento",
                                        line=dict(color="#3498db", width=2), fill="tozeroy", fillcolor="rgba(52,152,219,0.1)"))
                fig.add_trace(go.Scatter(x=df["data"], y=df["lucro_bruto"], name="Lucro",
                                        line=dict(color="#27ae60", width=2), fill="tozeroy", fillcolor="rgba(39,174,96,0.1)"))
                fig.update_layout(title="Evolucao Financeira", height=350,
                                 paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                 font=dict(color="#8a8a9a"), legend=dict(orientation="h", y=-0.2),
                                 xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                                 yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.markdown('<div class="section-title">REMOVER FECHAMENTO</div>', unsafe_allow_html=True)
                fech_map = {f"{f['data']} — R$ {f['faturamento_bruto']:.2f}": f["id"] for f in fechamentos}
                sel = st.selectbox("Selecione", list(fech_map.keys()))
                if st.button("🗑️ Excluir"):
                    db_financeiro.deletar_fechamento(fech_map[sel])
                    st.success("Removido!")
                    st.rerun()
            else:
                st.info("Nenhum fechamento registrado.")
        except Exception as e:
            st.caption(str(e))


# ============================================================
# CMV & MARGEM
# ============================================================
def render_cmv():
    st.markdown('<p class="main-header">CMV & ENGENHARIA DE CARDAPIO</p>', unsafe_allow_html=True)
    try:
        cmv = db_produtos.cmv_todos_produtos()
        if cmv:
            df = pd.DataFrame(cmv)

            # KPIs de CMV
            cmv_medio = df["cmv_pct"].mean() if len(df) > 0 else 0
            melhor = df.loc[df["lucro"].idxmax()] if len(df) > 0 else None
            pior = df.loc[df["cmv_pct"].idxmax()] if len(df) > 0 else None

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(_kpi_html("CMV MEDIO", f"{cmv_medio:.1f}%", "Meta: < 35%", "up" if cmv_medio < 35 else "down"), unsafe_allow_html=True)
            with c2:
                if melhor is not None:
                    st.markdown(_kpi_html("MAIS LUCRATIVO", melhor["nome"], f"R$ {melhor['lucro']:.2f} de lucro", "up"), unsafe_allow_html=True)
            with c3:
                if pior is not None:
                    st.markdown(_kpi_html("MAIOR CMV", pior["nome"], f"{pior['cmv_pct']:.1f}% - revisar ficha", "down"), unsafe_allow_html=True)

            st.dataframe(df, use_container_width=True, hide_index=True,
                        column_config={
                            "nome": "Produto",
                            "preco_venda": st.column_config.NumberColumn("Venda", format="R$ %.2f"),
                            "custo_total": st.column_config.NumberColumn("Custo", format="R$ %.2f"),
                            "lucro": st.column_config.NumberColumn("Lucro", format="R$ %.2f"),
                            "cmv_pct": st.column_config.NumberColumn("CMV %", format="%.1f%%"),
                        })

            fig = px.scatter(df, x="preco_venda", y="lucro", size="cmv_pct", color="cmv_pct", text="nome",
                           color_continuous_scale=["#27ae60", "#f39c12", "#e74c3c"],
                           labels={"preco_venda": "Preco Venda", "lucro": "Lucro R$", "cmv_pct": "CMV %"},
                           title="Mapa de Rentabilidade")
            fig.update_traces(textposition="top center")
            fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             font=dict(color="#8a8a9a"),
                             xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                             yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Cadastre produtos com fichas tecnicas para ver o CMV.")
    except Exception as e:
        st.caption(str(e))


# ============================================================
# CUSTOS FIXOS
# ============================================================
def render_custos_fixos():
    st.markdown('<p class="main-header">CUSTOS FIXOS</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Lista", "➕ Novo Custo"])

    with tab1:
        try:
            custos = db_financeiro.listar_custos_fixos()
            total = db_financeiro.total_custos_fixos_mensal()

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(_kpi_html("TOTAL MENSAL", f"R$ {total:,.2f}"), unsafe_allow_html=True)
            with c2:
                st.markdown(_kpi_html("CUSTO/DIA", f"R$ {total/22:,.2f}", "22 dias operacao"), unsafe_allow_html=True)
            with c3:
                # Distribuicao por categoria
                if custos:
                    cats = {}
                    for c in custos:
                        cat = c.get("categoria", "outros")
                        cats[cat] = cats.get(cat, 0) + c["valor"]
                    maior = max(cats.items(), key=lambda x: x[1])
                    st.markdown(_kpi_html("MAIOR CUSTO", maior[0].upper(), f"R$ {maior[1]:,.2f}/mes"), unsafe_allow_html=True)

            st.divider()
            if custos:
                # Grafico pizza de custos
                cats_data = []
                for c in custos:
                    cats_data.append({"Nome": c["nome"], "Valor": c["valor"], "Categoria": c.get("categoria", "outros")})
                df_custos = pd.DataFrame(cats_data)
                fig = px.pie(df_custos, values="Valor", names="Nome",
                            color_discrete_sequence=["#e94560", "#3498db", "#27ae60", "#f39c12", "#9b59b6", "#e67e22", "#1abc9c", "#34495e", "#e74c3c", "#2ecc71"])
                fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#8a8a9a"))
                st.plotly_chart(fig, use_container_width=True)

                for c in custos:
                    with st.expander(f"💰 {c['nome']} — R$ {c['valor']:.2f}/{c.get('recorrencia', 'mensal')}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            nome = st.text_input("Nome", value=c["nome"], key=f"cf_n_{c['id']}")
                        with col2:
                            valor = st.number_input("Valor", value=float(c["valor"]), format="%.2f", key=f"cf_v_{c['id']}")
                        with col3:
                            cat = st.text_input("Categoria", value=c.get("categoria", "") or "", key=f"cf_c_{c['id']}")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("💾 Salvar", key=f"btn_cf_{c['id']}"):
                                db_financeiro.atualizar_custo_fixo(c["id"], {"nome": nome, "valor": valor, "categoria": cat})
                                st.success("Atualizado!")
                                st.rerun()
                        with col_b:
                            if st.button("🗑️ Desativar", key=f"btn_desat_cf_{c['id']}"):
                                db_financeiro.desativar_custo_fixo(c["id"])
                                st.rerun()
        except Exception as e:
            st.caption(str(e))

    with tab2:
        with st.form("form_custo_fixo"):
            nome = st.text_input("Nome *")
            col1, col2, col3 = st.columns(3)
            with col1:
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            with col2:
                categoria = st.selectbox("Categoria", ["aluguel", "funcionario", "plataforma",
                                                       "energia", "internet", "financeiro", "administrativo", "outros"])
            with col3:
                recorrencia = st.selectbox("Recorrencia", ["mensal", "semanal", "diario"])
            if st.form_submit_button("Cadastrar", type="primary"):
                if nome and valor > 0:
                    try:
                        db_financeiro.criar_custo_fixo({"nome": nome, "valor": valor, "categoria": categoria, "recorrencia": recorrencia})
                        st.success(f"✅ {nome} cadastrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))



# ============================================================
# ENGENHARIA DE CARDAPIO
# ============================================================
def render_engenharia():
    st.markdown('<p class="main-header">ENGENHARIA DE CARDAPIO</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Matriz BCG: descubra quais produtos promover, ajustar ou remover</p>', unsafe_allow_html=True)
    try:
        col1, col2 = st.columns(2)
        with col1:
            di = st.date_input("De", value=date.today() - timedelta(days=30), key="eng_di")
        with col2:
            df_data = st.date_input("Ate", value=date.today(), key="eng_df")
        dados = db_engenharia.analise_engenharia(di.isoformat(), df_data.isoformat())
        if dados:
            classes = {}
            for d in dados:
                c = d["classe"]
                if c not in classes:
                    classes[c] = {"qtd": 0, "lucro": 0}
                classes[c]["qtd"] += 1
                classes[c]["lucro"] += d["lucro_total"]
            cols = st.columns(4)
            labels_list = [("Estrelas", "Estrela"), ("Cavalos", "Cavalo de Batalha"), ("Enigmas", "Enigma"), ("Caes", "Cao")]
            for i, (label, key) in enumerate(labels_list):
                with cols[i]:
                    info = classes.get(key, {"qtd": 0, "lucro": 0})
                    st.metric(label, f"{info['qtd']} prod.", f"R$ {info['lucro']:.2f}")
            st.divider()
            df = pd.DataFrame(dados)
            cores_map = {"Estrela": "#27ae60", "Cavalo de Batalha": "#f39c12", "Enigma": "#3498db", "Cao": "#e74c3c"}
            fig = px.scatter(df, x="qtd_vendida", y="lucro_unitario", size="receita_total", color="classe", text="nome",
                            color_discrete_map=cores_map, labels={"qtd_vendida": "Popularidade", "lucro_unitario": "Lucro Unit. R$"})
            fig.update_traces(textposition="top center", textfont_size=9)
            fig.update_layout(height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8a8a9a"))
            st.plotly_chart(fig, use_container_width=True)
            for d in dados:
                with st.expander(f"{d['emoji']} {d['nome']} — {d['classe']}"):
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("Vendidos", d["qtd_vendida"])
                    with c2:
                        st.metric("Lucro Unit.", f"R$ {d['lucro_unitario']:.2f}")
                    with c3:
                        st.metric("CMV", f"{d['cmv_pct']:.1f}%")
                    with c4:
                        st.metric("Lucro Total", f"R$ {d['lucro_total']:.2f}")
                    st.info(f"**Acao:** {d['acao']}")
        else:
            st.info("Registre pedidos para ver a analise.")
    except Exception as e:
        st.caption(str(e))


# ============================================================
# DASHBOARD BI
# ============================================================
def render_bi():
    st.markdown('<p class="main-header">BUSINESS INTELLIGENCE</p>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["Resumo", "Por Hora", "Por Dia", "Previsao"])
    with tab1:
        try:
            dias_bi = st.slider("Periodo (dias)", 7, 90, 30, key="bi_dias")
            resumo = db_bi.resumo_bi(dias_bi)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Faturamento", f"R$ {resumo['total_faturamento']:,.2f}")
            with c2:
                st.metric("Pedidos", resumo["total_pedidos"])
            with c3:
                st.metric("Ticket Medio", f"R$ {resumo['ticket_medio']:.2f}")
            with c4:
                st.metric("Melhor Canal", resumo["melhor_canal"])
        except Exception as e:
            st.caption(str(e))
    with tab2:
        try:
            dados_hora = db_bi.vendas_por_hora()
            if dados_hora:
                df_h = pd.DataFrame(dados_hora)
                fig = px.bar(df_h, x="hora", y="pedidos", color="faturamento",
                            color_continuous_scale=["#16213e", "#e94560"], title="Pedidos por Hora")
                fig.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8a8a9a"))
                st.plotly_chart(fig, use_container_width=True)
                pico = max(dados_hora, key=lambda x: x["pedidos"])
                st.success(f"Horario pico: **{pico['hora']}** com {pico['pedidos']} pedidos")
            else:
                st.info("Registre pedidos para ver analise por hora.")
        except Exception as e:
            st.caption(str(e))
    with tab3:
        try:
            dados_dia = db_bi.vendas_por_dia_semana()
            if dados_dia:
                df_d = pd.DataFrame(dados_dia)
                fig = px.bar(df_d, x="dia", y="media_faturamento_dia", color="media_pedidos_dia",
                            color_continuous_scale=["#f39c12", "#27ae60"], title="Media por Dia da Semana")
                fig.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8a8a9a"))
                st.plotly_chart(fig, use_container_width=True)
                melhor_d = max(dados_dia, key=lambda x: x["media_faturamento_dia"])
                pior_d = min(dados_dia, key=lambda x: x["media_faturamento_dia"])
                c1, c2 = st.columns(2)
                with c1:
                    st.success(f"Melhor: **{melhor_d['dia']}** R$ {melhor_d['media_faturamento_dia']:.2f}")
                with c2:
                    st.warning(f"Pior: **{pior_d['dia']}** R$ {pior_d['media_faturamento_dia']:.2f}")
        except Exception as e:
            st.caption(str(e))
    with tab4:
        try:
            previsao = db_bi.previsao_demanda()
            if previsao:
                df_p = pd.DataFrame(previsao)
                fig = px.bar(df_p, x="data", y="faturamento_previsto", text="dia_semana",
                            color="faturamento_previsto", color_continuous_scale=["#e94560", "#27ae60"],
                            title="Previsao 7 Dias")
                fig.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8a8a9a"))
                st.plotly_chart(fig, use_container_width=True)
                total_prev = sum(p["faturamento_previsto"] for p in previsao)
                st.metric("Faturamento Previsto (7 dias)", f"R$ {total_prev:,.2f}")
            else:
                st.info("Registre fechamentos para gerar previsoes.")
        except Exception as e:
            st.caption(str(e))


# ============================================================
# METAS INTELIGENTES
# ============================================================
def render_metas():
    st.markdown('<p class="main-header">METAS INTELIGENTES</p>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Hoje", "Historico"])
    with tab1:
        try:
            meta_calc = db_metas.calcular_meta_diaria()
            meta_dia = db_metas.buscar_meta_dia()
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Meta Faturamento", f"R$ {meta_calc['meta_faturamento']:.2f}")
            with c2:
                st.metric("Meta Pedidos", meta_calc["meta_pedidos"])
            with c3:
                st.metric("Custo/Dia", f"R$ {meta_calc['custo_dia']:.2f}")
            if not meta_dia:
                if st.button("Iniciar Meta de Hoje", type="primary"):
                    db_metas.registrar_meta_dia()
                    st.rerun()
            else:
                st.divider()
                fat_atual = meta_dia.get("faturamento_atual", 0) or 0
                ped_atual = meta_dia.get("pedidos_atual", 0) or 0
                pct_fat = min(100, (fat_atual / meta_calc["meta_faturamento"] * 100)) if meta_calc["meta_faturamento"] > 0 else 0
                pct_ped = min(100, (ped_atual / meta_calc["meta_pedidos"] * 100)) if meta_calc["meta_pedidos"] > 0 else 0
                c1, c2 = st.columns(2)
                with c1:
                    st.progress(pct_fat / 100)
                    st.markdown(f"**Faturamento:** R$ {fat_atual:.2f} / R$ {meta_calc['meta_faturamento']:.2f} ({pct_fat:.0f}%)")
                with c2:
                    st.progress(pct_ped / 100)
                    faltam = max(0, meta_calc["meta_pedidos"] - ped_atual)
                    st.markdown(f"**Pedidos:** {ped_atual} / {meta_calc['meta_pedidos']} (faltam {faltam})")
                st.divider()
                c1, c2, c3 = st.columns(3)
                with c1:
                    novo_fat = st.number_input("Faturamento atual", value=float(fat_atual), format="%.2f", key="meta_fat")
                with c2:
                    novo_ped = st.number_input("Pedidos atuais", value=int(ped_atual), key="meta_ped")
                with c3:
                    novo_dir = st.number_input("Pedidos diretos", value=int(meta_dia.get("pedidos_direto_atual", 0) or 0), key="meta_dir")
                if st.button("Atualizar", type="primary"):
                    db_metas.atualizar_progresso(faturamento=novo_fat, pedidos=novo_ped, pedidos_direto=novo_dir)
                    st.rerun()
        except Exception as e:
            st.caption(str(e))
    with tab2:
        try:
            taxa = db_metas.taxa_batimento()
            st.metric("Taxa de Batimento (30d)", f"{taxa}%")
            historico = db_metas.historico_metas()
            if historico:
                df_m = pd.DataFrame(historico)
                fig = go.Figure()
                fat_vals = [h.get("faturamento_atual", 0) or 0 for h in historico]
                fig.add_trace(go.Bar(x=df_m["data"], y=fat_vals, name="Realizado", marker_color="#27ae60"))
                fig.add_trace(go.Scatter(x=df_m["data"], y=df_m["meta_faturamento"], name="Meta", line=dict(color="#e94560", dash="dash")))
                fig.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8a8a9a"))
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.caption(str(e))


# ============================================================
# PREVISAO DE COMPRAS
# ============================================================
def render_compras():
    st.markdown('<p class="main-header">PREVISAO DE COMPRAS</p>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Gerar Lista", "Listas Anteriores"])
    with tab1:
        try:
            dias_cob = st.slider("Cobrir quantos dias?", 3, 14, 7, key="compras_dias")
            if st.button("Gerar Lista de Compras", type="primary"):
                resultado = db_previsao_compras.gerar_lista_compras(dias_cob)
                if resultado["itens"]:
                    st.success(f"Total estimado: **R$ {resultado['total_estimado']:.2f}**")
                    for item in resultado["itens"]:
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.text(item["nome"])
                        with c2:
                            st.text(f"Comprar: {item['quantidade_sugerida']:.2f} {item['unidade']}")
                        with c3:
                            st.text(f"Estoque: {item['estoque_atual']:.2f}")
                        with c4:
                            st.text(f"~R$ {item['custo_estimado']:.2f}")
                else:
                    st.info("Estoque suficiente!")
            st.divider()
            st.subheader("Consumo Medio (7 dias)")
            consumo = db_previsao_compras.calcular_consumo_medio()
            if consumo:
                dados_c = [{"Insumo": v["nome"], "Consumo/dia": f"{v['media_dia']:.3f} {v['unidade']}",
                           "Estoque": f"{v['estoque_atual']:.2f}", "Minimo": f"{v['estoque_minimo']:.2f}"}
                          for v in consumo.values()]
                st.dataframe(pd.DataFrame(dados_c), use_container_width=True, hide_index=True)
        except Exception as e:
            st.caption(str(e))
    with tab2:
        try:
            listas = db_previsao_compras.listar_listas_compras()
            if listas:
                for lista in listas:
                    with st.expander(f"Lista {lista['data_geracao']} — {lista['periodo_dias']} dias"):
                        itens_l = lista.get("itens_lista_compras", [])
                        for item in itens_l:
                            nome_i = item.get("insumos", {}).get("nome", "?")
                            check = "ok" if item.get("comprado") else "pendente"
                            st.text(f"[{check}] {nome_i}: {item['quantidade_sugerida']:.2f} {item.get('unidade', '')} ~R$ {item.get('custo_estimado', 0):.2f}")
            else:
                st.info("Nenhuma lista gerada.")
        except Exception as e:
            st.caption(str(e))


# ============================================================
# PRODUTIVIDADE
# ============================================================
def render_produtividade():
    st.markdown('<p class="main-header">PRODUTIVIDADE</p>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Metricas", "Registrar", "Historico"])
    with tab1:
        try:
            m = db_produtividade.metricas_produtividade()
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Tempo Medio Preparo", f"{m['media_tempo_preparo']:.1f} min")
            with c2:
                st.metric("Media Pedidos/Dia", f"{m['media_pedidos_dia']:.1f}")
            with c3:
                st.metric("Pedidos/Hora", f"{m['pedidos_hora']:.1f}")
            if m.get("melhor_dia", {}).get("data"):
                c1, c2 = st.columns(2)
                with c1:
                    st.success(f"Melhor: {m['melhor_dia']['data']} ({m['melhor_dia']['pedidos']} ped)")
                with c2:
                    st.warning(f"Pior: {m['pior_dia']['data']} ({m['pior_dia']['pedidos']} ped)")
            st.divider()
            turnos = db_produtividade.analise_por_turno()
            if turnos:
                dados_t = [{"Turno": t, "Media Pedidos": v["media_pedidos"], "Tempo Medio": f"{v['media_tempo']:.1f} min"} for t, v in turnos.items()]
                st.dataframe(pd.DataFrame(dados_t), use_container_width=True, hide_index=True)
        except Exception as e:
            st.caption(str(e))
    with tab2:
        with st.form("form_producao"):
            data_prod = st.date_input("Data", value=date.today())
            c1, c2 = st.columns(2)
            with c1:
                hora_ini = st.time_input("Hora inicio")
                pedidos_prod = st.number_input("Pedidos realizados", min_value=0, value=0)
                turno = st.selectbox("Turno", ["almoco", "janta", "integral"])
            with c2:
                hora_fim = st.time_input("Hora fim")
                tempo_med = st.number_input("Tempo medio preparo (min)", min_value=0.0, format="%.1f")
                funcs = st.number_input("Funcionarios presentes", min_value=1, value=1)
            obs_prod = st.text_input("Observacoes")
            if st.form_submit_button("Registrar", type="primary"):
                try:
                    db_produtividade.registrar_producao({
                        "data": data_prod.isoformat(), "hora_inicio": hora_ini.strftime("%H:%M"),
                        "hora_fim": hora_fim.strftime("%H:%M"), "turno": turno,
                        "pedidos_realizados": pedidos_prod, "tempo_medio_preparo_min": tempo_med,
                        "funcionarios_presentes": funcs, "observacoes": obs_prod,
                    })
                    st.success("Registrado!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
    with tab3:
        try:
            registros = db_produtividade.listar_producao()
            if registros:
                df_r = pd.DataFrame(registros)
                cols_show = ["data", "turno", "pedidos_realizados", "tempo_medio_preparo_min", "funcionarios_presentes"]
                cols_ok = [c for c in cols_show if c in df_r.columns]
                st.dataframe(df_r[cols_ok], use_container_width=True, hide_index=True)
                reg_map = {f"{r['data']} {r.get('turno', '?')} {r.get('pedidos_realizados', 0)}ped": r["id"] for r in registros}
                sel_r = st.selectbox("Selecione para excluir", list(reg_map.keys()))
                if st.button("Excluir"):
                    db_produtividade.deletar_registro(reg_map[sel_r])
                    st.rerun()
        except Exception as e:
            st.caption(str(e))


# ============================================================
# ROTEADOR PRINCIPAL
# ============================================================
def main():
    if not render_login():
        return

    menu = render_sidebar()

    if "Dashboard" in menu:
        render_dashboard()
    elif "Insumos" in menu:
        render_insumos()
    elif "Produtos" in menu:
        render_produtos()
    elif "Fornecedores" in menu:
        render_fornecedores()
    elif "Notas Fiscais" in menu:
        render_notas_fiscais()
    elif "Pedidos" in menu:
        render_pedidos()
    elif "Financeiro" in menu:
        render_financeiro()
    elif "CMV" in menu:
        render_cmv()
    elif "Custos Fixos" in menu:
        render_custos_fixos()
    elif "Engenharia" in menu:
        render_engenharia()
    elif "BI" in menu:
        render_bi()
    elif "Metas" in menu:
        render_metas()
    elif "Compras" in menu:
        render_compras()
    elif "Produtividade" in menu:
        render_produtividade()


if __name__ == "__main__":
    main()
