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

# CSS premium — food tech design system
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    :root {
        --bg-primary: #0f1117;
        --bg-card: rgba(255,255,255,0.03);
        --bg-card-hover: rgba(255,255,255,0.06);
        --border-subtle: rgba(255,255,255,0.08);
        --border-active: rgba(233,69,96,0.4);
        --text-primary: #e5e7eb;
        --text-secondary: #6b7280;
        --text-muted: #4b5563;
        --accent-red: #e94560;
        --accent-orange: #f59e0b;
        --accent-gold: #d4a574;
        --accent-green: #10b981;
        --accent-blue: #3b82f6;
        --accent-red-glow: rgba(233,69,96,0.15);
        --radius-lg: 16px;
        --radius-md: 12px;
        --radius-sm: 8px;
    }

    /* ---- GLOBAL ---- */
    .main .block-container { padding-top: 1.5rem; }
    section[data-testid="stSidebar"] {
        background: #0a0c10 !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 2px !important;
    }
    section[data-testid="stSidebar"] .stRadio > div > label {
        padding: 10px 16px !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        transition: all 0.2s ease !important;
        border: 1px solid transparent !important;
    }
    section[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: var(--bg-card-hover) !important;
        color: var(--text-primary) !important;
    }
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio > div > label[aria-checked="true"] {
        background: var(--accent-red-glow) !important;
        color: var(--accent-red) !important;
        font-weight: 600 !important;
        border: 1px solid var(--border-active) !important;
    }

    /* ---- HEADERS ---- */
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.6rem;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 0;
        letter-spacing: -0.5px;
    }
    .main-header span.accent { color: var(--accent-red); }
    .sub-header {
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
        color: var(--text-secondary);
        margin-top: -6px;
        margin-bottom: 20px;
    }

    /* ---- KPI CARDS PREMIUM ---- */
    .kpi-box {
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        padding: 22px 24px;
        border: 1px solid var(--border-subtle);
        margin-bottom: 12px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 4px 24px rgba(0,0,0,0.2);
        transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
        position: relative;
        overflow: hidden;
    }
    .kpi-box::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-red), var(--accent-orange));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    .kpi-box:hover {
        background: var(--bg-card-hover);
        border-color: var(--border-active);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(233,69,96,0.1);
    }
    .kpi-box:hover::before { opacity: 1; }

    .kpi-icon {
        width: 36px; height: 36px;
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 14px;
        font-size: 1.1rem;
    }
    .kpi-icon-red { background: rgba(233,69,96,0.12); color: var(--accent-red); }
    .kpi-icon-green { background: rgba(16,185,129,0.12); color: var(--accent-green); }
    .kpi-icon-blue { background: rgba(59,130,246,0.12); color: var(--accent-blue); }
    .kpi-icon-orange { background: rgba(245,158,11,0.12); color: var(--accent-orange); }
    .kpi-icon-gold { background: rgba(212,165,116,0.12); color: var(--accent-gold); }

    .kpi-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-family: 'Inter', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1.1;
        letter-spacing: -0.5px;
    }
    .kpi-delta {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 8px;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .kpi-delta-up {
        color: var(--accent-green);
        background: rgba(16,185,129,0.1);
    }
    .kpi-delta-down {
        color: #ef4444;
        background: rgba(239,68,68,0.1);
    }
    .kpi-delta-neutral {
        color: var(--accent-orange);
        background: rgba(245,158,11,0.1);
    }

    /* ---- ALERT CARDS ---- */
    .alert-card {
        background: var(--bg-card);
        border-left: 3px solid #ef4444;
        border-radius: var(--radius-sm);
        padding: 12px 16px;
        margin-bottom: 6px;
        backdrop-filter: blur(8px);
        transition: background 0.2s ease;
    }
    .alert-card:hover { background: var(--bg-card-hover); }
    .alert-card-warn { border-left-color: var(--accent-orange); }
    .alert-card-ok { border-left-color: var(--accent-green); }

    /* ---- SECTION TITLES ---- */
    .section-title {
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem;
        font-weight: 700;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border-subtle);
        display: block;
    }

    /* ---- TABS PREMIUM ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--bg-card);
        border-radius: var(--radius-md);
        padding: 4px;
        border: 1px solid var(--border-subtle);
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        border-radius: var(--radius-sm) !important;
        font-size: 0.85rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.3rem;
        font-weight: 700;
    }

    /* ---- SIDEBAR BRAND ---- */
    .sidebar-brand {
        padding: 8px 0 16px 0;
        text-align: left;
    }
    .sidebar-brand-name {
        font-family: 'Inter', sans-serif;
        font-size: 1.3rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, var(--accent-red), var(--accent-orange));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .sidebar-brand-sub {
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: -2px;
    }
    .sidebar-divider {
        height: 1px;
        background: var(--border-subtle);
        margin: 12px 0;
    }
    .sidebar-status {
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        color: var(--text-muted);
        padding: 8px 0;
    }

    /* ---- BUTTONS / FORMS ---- */
    .stButton > button {
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(233,69,96,0.2) !important;
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        border-radius: var(--radius-sm) !important;
        border-color: var(--border-subtle) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ---- LOADING ANIMATION ---- */
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    .loading-card {
        background: linear-gradient(90deg, var(--bg-card) 25%, var(--bg-card-hover) 50%, var(--bg-card) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: var(--radius-lg);
        height: 120px;
        border: 1px solid var(--border-subtle);
    }

    /* ---- PLOTLY OVERRIDES ---- */
    .js-plotly-plot .plotly .main-svg { border-radius: var(--radius-md); }
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


def _kpi_html(label, value, delta=None, delta_type="neutral", icon_color="red"):
    """Gera HTML para KPI card premium."""
    delta_class = f"kpi-delta-{delta_type}"
    arrow = "&#8593;" if delta_type == "up" else "&#8595;" if delta_type == "down" else "&#8594;"
    delta_html = f'<div class="kpi-delta {delta_class}">{arrow} {delta}</div>' if delta else ""
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
        # Brand premium
        st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-name">GRILLATO</div>
            <div class="sidebar-brand-sub">Sistema Operacional</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        render_user_info()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Menu com labels limpos (sem emojis)
        permitidas = paginas_permitidas()
        opcoes = list(permitidas)

        menu = st.radio("Navegacao", opcoes, label_visibility="collapsed")
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Status compacto
        try:
            alertas = db_insumos.estoque_alertas()
            criticos = len([a for a in alertas if a["status_estoque"] in ("SEM_ESTOQUE", "ABAIXO_MINIMO")]) if alertas else 0
            if criticos > 0:
                st.markdown(f"""
                <div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.2);
                     border-radius:8px; padding:8px 12px; font-size:0.78rem; color:#ef4444;">
                    {criticos} insumo(s) em alerta
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.2);
                     border-radius:8px; padding:8px 12px; font-size:0.78rem; color:#10b981;">
                    Estoque OK
                </div>""", unsafe_allow_html=True)
        except:
            pass

        perfil = get_perfil_atual()
        st.markdown(f"""
        <div class="sidebar-status">
            {date.today().strftime('%d/%m/%Y')} &middot; {perfil}
        </div>""", unsafe_allow_html=True)

        return menu


# ============================================================
# DASHBOARD PRINCIPAL - REDESENHADO
# ============================================================
def render_dashboard():
    st.markdown('<p class="main-header"><span class="accent">GRILLATO</span> &middot; Painel de Controle</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sistema operacional de delivery premium — visao em tempo real</p>', unsafe_allow_html=True)

    try:
        fechamentos = db_financeiro.listar_fechamentos(30)
        cmv_dados = db_produtos.cmv_todos_produtos()
        alertas_est = db_insumos.estoque_alertas()
        custos_mensal = db_financeiro.total_custos_fixos_mensal()
        custo_dia = custos_mensal / 22

        # Dados de hoje
        hoje_str = str(date.today())
        fech_hoje = [f for f in fechamentos if f.get("data") == hoje_str] if fechamentos else []
        fat_hoje = sum(f["faturamento_bruto"] for f in fech_hoje) if fech_hoje else 0
        ped_hoje = sum(f["total_pedidos"] for f in fech_hoje) if fech_hoje else 0
        lucro_hoje = sum(f.get("lucro_bruto", 0) for f in fech_hoje) if fech_hoje else 0
        ticket_hoje = (fat_hoje / ped_hoje) if ped_hoje > 0 else 0

        # CMV medio
        cmv_medio = 0
        if cmv_dados:
            cmv_valores = [c["cmv_pct"] for c in cmv_dados if c.get("cmv_pct")]
            cmv_medio = sum(cmv_valores) / len(cmv_valores) if cmv_valores else 0

        # Produto top (maior lucro)
        produto_top = "—"
        if cmv_dados:
            top = max(cmv_dados, key=lambda x: x.get("lucro", 0))
            produto_top = top.get("nome", "—")

        # Estoque critico
        alertas_crit = len([a for a in alertas_est if a["status_estoque"] in ("SEM_ESTOQUE", "ABAIXO_MINIMO")]) if alertas_est else 0

        # Lucro liquido hoje
        lucro_liq_hoje = lucro_hoje - custo_dia if fech_hoje else 0

        # Metricas agregadas para graficos
        if fechamentos:
            fat_total = sum(f["faturamento_bruto"] for f in fechamentos)
            ped_total = sum(f["total_pedidos"] for f in fechamentos)
            dias = len(fechamentos)
            media_fat_dia = fat_total / dias if dias > 0 else 0
            media_ped_dia = ped_total / dias if dias > 0 else 0
            lucro_total = sum(f.get("lucro_bruto", 0) for f in fechamentos)
        else:
            fat_total = ped_total = media_fat_dia = media_ped_dia = lucro_total = 0
            dias = 0

        # ---- ROW 1: KPIs PRINCIPAIS (7 cards) ----
        st.markdown("")
        r1a, r1b, r1c, r1d = st.columns(4)

        with r1a:
            delta_fat = "up" if fat_hoje >= custo_dia else "down"
            st.markdown(_kpi_html("Faturamento Hoje", f"R$ {fat_hoje:,.2f}",
                                  f"Meta: R$ {custo_dia:,.0f}", delta_fat),
                       unsafe_allow_html=True)
        with r1b:
            delta_ped = "up" if ped_hoje >= 17 else "down"
            st.markdown(_kpi_html("Pedidos Hoje", str(ped_hoje),
                                  "Meta: 17/dia", delta_ped),
                       unsafe_allow_html=True)
        with r1c:
            st.markdown(_kpi_html("Ticket Medio", f"R$ {ticket_hoje:,.2f}",
                                  f"{ped_hoje} pedidos hoje", "neutral"),
                       unsafe_allow_html=True)
        with r1d:
            delta_cmv = "up" if cmv_medio <= 35 else "down"
            st.markdown(_kpi_html("CMV Medio", f"{cmv_medio:.1f}%",
                                  "Meta: < 35%", delta_cmv),
                       unsafe_allow_html=True)

        r2a, r2b, r2c = st.columns(3)

        with r2a:
            delta_lucro = "up" if lucro_liq_hoje > 0 else "down"
            st.markdown(_kpi_html("Lucro Liquido", f"R$ {lucro_liq_hoje:,.2f}",
                                  f"Bruto: R$ {lucro_hoje:,.2f}", delta_lucro),
                       unsafe_allow_html=True)
        with r2b:
            st.markdown(_kpi_html("Produto Top", produto_top,
                                  "Maior lucro unitario", "neutral"),
                       unsafe_allow_html=True)
        with r2c:
            cor_est = "down" if alertas_crit > 0 else "up"
            st.markdown(_kpi_html("Estoque Critico", str(alertas_crit),
                                  f"{len(alertas_est) if alertas_est else 0} monitorados", cor_est),
                       unsafe_allow_html=True)

        # ---- ROW 2: INDICADORES DE SAUDE ----
        st.markdown('<div class="section-title">INDICADORES DE SAUDE</div>', unsafe_allow_html=True)
        g1, g2, g3, g4 = st.columns(4)

        with g1:
            fig = _gauge_chart(cmv_medio, 35, "CMV MEDIO")
            st.plotly_chart(fig, use_container_width=True)

        with g2:
            ocup = (media_ped_dia / 17 * 100) if media_ped_dia > 0 else 0
            fig = _gauge_chart(min(ocup, 100), 80, "CAPACIDADE", cor_bom="#3498db", cor_ruim="#27ae60")
            st.plotly_chart(fig, use_container_width=True)

        with g3:
            payroll_pct = 0
            if fat_total > 0 and dias > 0:
                folha_mensal = sum(c["valor"] for c in db_financeiro.listar_custos_fixos() if c.get("categoria") == "funcionario")
                fat_mensal_proj = media_fat_dia * 22
                payroll_pct = (folha_mensal / fat_mensal_proj * 100) if fat_mensal_proj > 0 else 0
            fig = _gauge_chart(payroll_pct, 30, "FOLHA / FAT")
            st.plotly_chart(fig, use_container_width=True)

        with g4:
            be_pct = min(100, media_fat_dia / custo_dia * 100) if media_fat_dia > 0 else 0
            fig = _gauge_chart(be_pct, 100, "BREAK-EVEN", cor_bom="#27ae60", cor_ruim="#e74c3c")
            st.plotly_chart(fig, use_container_width=True)

        # ---- ROW 3: EVOLUCAO & PREVISOES ----
        st.markdown('<div class="section-title">EVOLUCAO & PREVISOES</div>', unsafe_allow_html=True)

        if fechamentos and len(fechamentos) >= 2:
            col_chart1, col_chart2 = st.columns(2)

            df_fech = pd.DataFrame(fechamentos).sort_values("data")

            with col_chart1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_fech["data"], y=df_fech["faturamento_bruto"],
                    name="Faturamento", line=dict(color="#3b82f6", width=2),
                    fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
                ))
                if "lucro_bruto" in df_fech.columns:
                    fig.add_trace(go.Scatter(
                        x=df_fech["data"], y=df_fech["lucro_bruto"],
                        name="Lucro", line=dict(color="#10b981", width=2),
                        fill="tozeroy", fillcolor="rgba(16,185,129,0.08)",
                    ))
                fig.add_hline(y=custo_dia, line_dash="dash", line_color="#ef4444",
                              annotation_text=f"Break-even R${custo_dia:.0f}")

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
                    font=dict(color="#6b7280", family="Inter"),
                    legend=dict(orientation="h", y=-0.2),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_chart2:
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
                    font=dict(color="#6b7280", family="Inter"),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Registre fechamentos diarios para ver graficos e previsoes.")

        # ---- ROW 4: VENDAS POR HORA ----
        st.markdown('<div class="section-title">VENDAS POR HORA</div>', unsafe_allow_html=True)
        try:
            vendas_hora = db_bi.vendas_por_hora(30)
            if vendas_hora and len(vendas_hora) > 0:
                df_hora = pd.DataFrame(vendas_hora)
                n_bars = len(df_hora)
                gradient_colors = [f"rgba(233,69,96,{0.4 + 0.6 * (v / max(df_hora['count']))})" if max(df_hora['count']) > 0 else "rgba(233,69,96,0.6)" for v in df_hora["count"]]
                fig_hora = go.Figure()
                fig_hora.add_trace(go.Bar(
                    x=df_hora["hour"], y=df_hora["count"],
                    marker_color=gradient_colors,
                    marker=dict(cornerradius=4),
                    name="Vendas",
                ))
                fig_hora.update_layout(
                    title="Distribuicao de Vendas por Hora",
                    height=320, margin=dict(t=40, b=40, l=40, r=20),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#6b7280", family="Inter"),
                    xaxis=dict(title="Hora", gridcolor="rgba(255,255,255,0.04)", dtick=1),
                    yaxis=dict(title="Quantidade", gridcolor="rgba(255,255,255,0.04)"),
                )
                st.plotly_chart(fig_hora, use_container_width=True)
            else:
                st.info("Sem dados de vendas por hora disponveis.")
        except Exception:
            st.info("Dados de vendas por hora indisponiveis.")

        # ---- ROW 5: PRODUTOS & ESTOQUE ----
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
                    font=dict(color="#6b7280", family="Inter"),
                    xaxis=dict(title="Lucro R$", gridcolor="rgba(255,255,255,0.04)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                )
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Cadastre produtos para ver o ranking.")

        with col_est:
            if alertas_est:
                st.markdown("**Status do Estoque**")
                for a in alertas_est:
                    status = a["status_estoque"]
                    card_class = "alert-card" if status == "SEM_ESTOQUE" else "alert-card-warn" if status in ("ABAIXO_MINIMO", "ATENCAO") else "alert-card-ok"
                    pct = (a["estoque_atual"] / a["estoque_minimo"] * 100) if a["estoque_minimo"] > 0 else 100
                    status_label = {"SEM_ESTOQUE": "SEM ESTOQUE", "ABAIXO_MINIMO": "ABAIXO", "ATENCAO": "ATENCAO", "OK": "OK"}.get(status, status)
                    st.markdown(f"""
                    <div class="{card_class}">
                        <strong>{a['nome']}</strong> — {a['estoque_atual']:.1f} {a['unidade_compra']}
                        <span style="float:right; color:#6b7280">{pct:.0f}% do minimo | {status_label}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Cadastre insumos para monitorar estoque.")

        # ---- ROW 6: PREVISOES & ALERTAS ----
        st.markdown('<div class="section-title">PREVISOES & ALERTAS</div>', unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)

        with p1:
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
                    <div style="color:#6b7280; font-size:0.8rem; margin-top:4px">
                        Meta: R$ {meta_min:,.0f} - R$ {meta_max:,.0f}<br>
                        {pct_meta:.0f}% da meta minima
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(_kpi_html("PROJECAO MENSAL", "Sem dados", "Registre vendas"), unsafe_allow_html=True)

        with p2:
            try:
                caixa = 9502.88
                if fechamentos and fechamentos[0].get("caixa_apos"):
                    caixa = fechamentos[0]["caixa_apos"]
                runway = db_financeiro.calcular_runway(caixa)
                cor_run = "#e74c3c" if runway["runway_dias"] < 15 else "#f39c12" if runway["runway_dias"] < 30 else "#27ae60"
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-label">RUNWAY (SOBREVIVENCIA)</div>
                    <div class="kpi-value" style="color:{cor_run}">{runway['runway_dias']} dias</div>
                    <div style="color:#6b7280; font-size:0.8rem; margin-top:4px">
                        Caixa: R$ {caixa:,.2f}<br>
                        Deficit/dia: R$ {runway['deficit_dia']:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(_kpi_html("RUNWAY", "—", str(e)[:40]), unsafe_allow_html=True)

        with p3:
            if alertas_est:
                criticos = [a for a in alertas_est if a["status_estoque"] in ("SEM_ESTOQUE", "ABAIXO_MINIMO")]
                atencao = [a for a in alertas_est if a["status_estoque"] == "ATENCAO"]
                if criticos:
                    urgencia = "URGENTE"
                elif atencao:
                    urgencia = "ATENCAO"
                else:
                    urgencia = "OK"
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-label">NECESSIDADE DE COMPRA</div>
                    <div class="kpi-value">{urgencia}</div>
                    <div style="color:#6b7280; font-size:0.8rem; margin-top:4px">
                        {len(criticos)} critico(s) | {len(atencao)} atencao<br>
                        {len(alertas_est)} insumos monitorados
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(_kpi_html("COMPRAS", "Sem dados", "Cadastre insumos"), unsafe_allow_html=True)

    except Exception as e:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px;">
            <div style="font-size:2.5rem; margin-bottom:12px; opacity:0.3;">&#9881;</div>
            <div style="font-size:1rem; color:#6b7280; margin-bottom:8px;">Conecte o Supabase para visualizar os dados</div>
            <div style="font-size:0.78rem; color:#4b5563;">Configure SUPABASE_URL e SUPABASE_KEY nos secrets</div>
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"Debug: {e}")


# ============================================================
# INSUMOS
# ============================================================
def render_insumos():
    st.markdown('<p class="main-header">INSUMOS</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Cadastro de ingredientes, embalagens e materiais</p>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Lista", "Cadastrar", "Estoque", "Movimentacoes"])

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

    tab1, tab2, tab3 = st.tabs(["Cardapio", "Novo Produto", "Ficha Tecnica"])

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

    tab1, tab2 = st.tabs(["Lista", "Cadastrar"])

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

    tab1, tab2 = st.tabs(["Historico", "Registrar NF"])

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

    tab1, tab2, tab3 = st.tabs(["Historico", "Novo Pedido", "Por Canal"])

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

    tab1, tab2, tab3 = st.tabs(["Runway", "Fechamento Diario", "Historico"])

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

    tab1, tab2 = st.tabs(["Lista", "Novo Custo"])

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
    with tab4:
        try:
            previsao = db_bi.previsao_demanda()
            if previsao:
                df_p = pd.DataFrame(previsao)
                fig = px.bar(
                    df_p, x="data", y="faturamento_previsto", text="dia_semana",
                    color="faturamento_previsto",
                    color_continuous_scale=["#e94560", "#10b981"],
                    title="Previsao 7 Dias"
                )
                fig.update_layout(
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#6b7280", family="Inter"),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                )
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
    st.markdown('<p class="sub-header">Acompanhamento diario de metas de faturamento e pedidos</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Hoje", "Historico"])
    with tab1:
        try:
            meta_calc = db_metas.calcular_meta_diaria()
            meta_dia = db_metas.buscar_meta_dia()

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(_kpi_html(
                    "META FATURAMENTO",
                    f"R$ {meta_calc.get('meta_faturamento', 0):,.2f}",
                    f"Break-even x 1.3",
                    "neutral"
                ), unsafe_allow_html=True)
            with c2:
                st.markdown(_kpi_html(
                    "META PEDIDOS",
                    str(meta_calc.get("meta_pedidos", 0)),
                    f"Ticket medio: R$ {meta_calc.get('ticket_medio', 0):.2f}",
                    "neutral"
                ), unsafe_allow_html=True)

            if meta_dia:
                st.markdown('<div class="section-title">PROGRESSO DE HOJE</div>', unsafe_allow_html=True)
                pct_fat = (meta_dia.get("realizado_faturamento", 0) / meta_dia["meta_faturamento"] * 100) if meta_dia.get("meta_faturamento", 0) > 0 else 0
                pct_ped = (meta_dia.get("realizado_pedidos", 0) / meta_dia["meta_pedidos"] * 100) if meta_dia.get("meta_pedidos", 0) > 0 else 0

                g1, g2 = st.columns(2)
                with g1:
                    fig = _gauge_chart(pct_fat, 100, "FATURAMENTO", cor_bom="#10b981", cor_ruim="#ef4444")
                    st.plotly_chart(fig, use_container_width=True)
                with g2:
                    fig = _gauge_chart(pct_ped, 100, "PEDIDOS", cor_bom="#10b981", cor_ruim="#ef4444")
                    st.plotly_chart(fig, use_container_width=True)

                with st.form("atualizar_meta"):
                    st.subheader("Atualizar Progresso")
                    fat_r = st.number_input("Faturamento realizado", value=float(meta_dia.get("realizado_faturamento", 0)), step=10.0)
                    ped_r = st.number_input("Pedidos realizados", value=int(meta_dia.get("realizado_pedidos", 0)), step=1)
                    if st.form_submit_button("Salvar", type="primary"):
                        db_metas.atualizar_progresso(fat_r, ped_r)
                        st.success("Progresso atualizado!")
                        st.rerun()
            else:
                if st.button("Registrar Meta de Hoje", type="primary"):
                    db_metas.registrar_meta_dia()
                    st.success("Meta registrada!")
                    st.rerun()
        except Exception as e:
            st.caption(str(e))

    with tab2:
        try:
            taxa = db_metas.taxa_batimento(30)
            if taxa:
                st.markdown(_kpi_html(
                    "TAXA DE BATIMENTO (30d)",
                    f"{taxa.get('taxa_batimento', 0):.0f}%",
                    f"{taxa.get('dias_batidos', 0)} de {taxa.get('total_dias', 0)} dias",
                    "up" if taxa.get("taxa_batimento", 0) >= 70 else "down"
                ), unsafe_allow_html=True)
        except Exception as e:
            st.caption(str(e))


# ============================================================
# PREVISAO DE COMPRAS
# ============================================================
def render_compras():
    st.markdown('<p class="main-header">PREVISAO DE COMPRAS</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Listas de compras inteligentes baseadas em consumo medio</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Gerar Lista", "Listas Anteriores"])
    with tab1:
        try:
            dias_cob = st.slider("Dias de cobertura", 3, 14, 7, key="compras_dias")
            if st.button("Gerar Lista de Compras", type="primary"):
                lista = db_previsao_compras.gerar_lista_compras(dias_cob)
                if lista:
                    st.success(f"Lista gerada com {len(lista)} itens!")
                    df_lista = pd.DataFrame(lista)
                    st.dataframe(df_lista, use_container_width=True)
                else:
                    st.info("Sem dados de consumo para gerar lista.")

            st.markdown('<div class="section-title">CONSUMO MEDIO (7 DIAS)</div>', unsafe_allow_html=True)
            consumo = db_previsao_compras.calcular_consumo_medio()
            if consumo:
                df_c = pd.DataFrame(consumo)
                st.dataframe(df_c, use_container_width=True)
        except Exception as e:
            st.caption(str(e))

    with tab2:
        try:
            listas = db_previsao_compras.listar_listas()
            if listas:
                for l in listas[:10]:
                    with st.expander(f"Lista {l.get('data_geracao', '?')} — {l.get('dias_cobertura', '?')} dias"):
                        itens = db_previsao_compras.itens_lista(l["id"])
                        if itens:
                            df_i = pd.DataFrame(itens)
                            st.dataframe(df_i, use_container_width=True)
            else:
                st.info("Nenhuma lista gerada ainda.")
        except Exception as e:
            st.caption(str(e))


# ============================================================
# PRODUTIVIDADE
# ============================================================
def render_produtividade():
    st.markdown('<p class="main-header">PRODUTIVIDADE</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Metricas de eficiencia operacional por turno</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Metricas", "Registrar", "Historico"])
    with tab1:
        try:
            metricas = db_produtividade.metricas_produtividade(30)
            if metricas:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(_kpi_html(
                        "PEDIDOS / HORA",
                        f"{metricas.get('pedidos_por_hora', 0):.1f}",
                        "Media geral", "neutral"
                    ), unsafe_allow_html=True)
                with c2:
                    st.markdown(_kpi_html(
                        "FATURAMENTO / HORA",
                        f"R$ {metricas.get('faturamento_por_hora', 0):,.2f}",
                        "Media geral", "neutral"
                    ), unsafe_allow_html=True)
                with c3:
                    st.markdown(_kpi_html(
                        "MELHOR TURNO",
                        metricas.get("melhor_turno", "—"),
                        "Maior produtividade", "up"
                    ), unsafe_allow_html=True)

                turnos = db_produtividade.analise_por_turno(30)
                if turnos:
                    df_t = pd.DataFrame(turnos)
                    fig = px.bar(
                        df_t, x="turno", y="media_pedidos",
                        color="media_faturamento",
                        color_continuous_scale=["#111827", "#e94560"],
                        title="Produtividade por Turno"
                    )
                    fig.update_layout(
                        height=300,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#6b7280", family="Inter"),
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Registre dados de producao para ver metricas.")
        except Exception as e:
            st.caption(str(e))

    with tab2:
        try:
            with st.form("reg_producao"):
                st.subheader("Registrar Producao")
                data_p = st.date_input("Data", value=date.today())
                turno = st.selectbox("Turno", ["almoco", "jantar", "noite"])
                ped_r = st.number_input("Pedidos realizados", min_value=0, step=1)
                fat_r = st.number_input("Faturamento do turno", min_value=0.0, step=10.0)
                horas = st.number_input("Horas trabalhadas", min_value=0.5, max_value=12.0, value=5.0, step=0.5)
                func = st.number_input("Funcionarios no turno", min_value=1, max_value=10, value=2, step=1)
                obs = st.text_area("Observacoes", placeholder="Opcional")
                if st.form_submit_button("Registrar", type="primary"):
                    db_produtividade.registrar_producao(
                        data=str(data_p), turno=turno,
                        pedidos_realizados=ped_r, faturamento=fat_r,
                        horas_trabalhadas=horas, funcionarios=func,
                        observacoes=obs
                    )
                    st.success("Producao registrada!")
                    st.rerun()
        except Exception as e:
            st.caption(str(e))

    with tab3:
        try:
            registros = db_produtividade.listar_registros(30)
            if registros:
                df_reg = pd.DataFrame(registros)
                st.dataframe(df_reg, use_container_width=True)

                # Opcao de excluir
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
