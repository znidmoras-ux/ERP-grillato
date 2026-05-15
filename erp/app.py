"""
Grillato ERP - Dashboard Principal (Streamlit)
Sistema completo de gestão para hamburgueria.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import os
import sys

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from erp import db_insumos, db_produtos, db_fornecedores, db_notas_fiscais, db_pedidos, db_financeiro

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Grillato ERP",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #e94560;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 0.9rem;
        color: #8a8a9a;
        margin-top: -10px;
    }
    .metric-card {
        background: #16213e;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.4rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🍔 GRILLATO ERP")
        st.caption("Sistema de Gestão v2.0")
        st.divider()

        menu = st.radio(
            "Menu",
            [
                "📊 Dashboard",
                "📦 Insumos",
                "🍔 Produtos & Fichas",
                "🏭 Fornecedores",
                "📄 Notas Fiscais",
                "🛒 Pedidos",
                "💰 Financeiro",
                "📈 CMV & Margem",
                "⚙️ Custos Fixos",
            ],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption(f"📅 {date.today().strftime('%d/%m/%Y')}")
        return menu


# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================
def render_dashboard():
    st.markdown('<p class="main-header">PAINEL DE CONTROLE</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Visão geral da operação Grillato</p>', unsafe_allow_html=True)
    st.divider()

    try:
        # KPIs superiores
        cmv_dados = db_produtos.cmv_todos_produtos()
        alertas = db_insumos.estoque_alertas()
        custos = db_financeiro.total_custos_fixos_mensal()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_produtos = len(cmv_dados) if cmv_dados else 0
            st.metric("Produtos Ativos", total_produtos)
        with col2:
            alertas_criticos = len([a for a in alertas if a["status_estoque"] in ("SEM_ESTOQUE", "ABAIXO_MINIMO")]) if alertas else 0
            st.metric("Alertas Estoque", alertas_criticos, delta=None)
        with col3:
            st.metric("Custo Fixo/Mês", f"R$ {custos:,.2f}")
        with col4:
            custo_dia = custos / 22
            st.metric("Custo Fixo/Dia", f"R$ {custo_dia:,.2f}")

        st.divider()

        # CMV dos produtos
        if cmv_dados:
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("CMV por Produto")
                df_cmv = pd.DataFrame(cmv_dados)
                fig = px.bar(
                    df_cmv, x="nome", y="cmv_pct",
                    color="cmv_pct",
                    color_continuous_scale=["#27ae60", "#f39c12", "#e74c3c"],
                    labels={"nome": "Produto", "cmv_pct": "CMV %"},
                )
                fig.add_hline(y=35, line_dash="dash", line_color="red",
                              annotation_text="Meta 35%")
                fig.update_layout(height=350, margin=dict(t=20, b=40))
                st.plotly_chart(fig, use_container_width=True)

            with col_b:
                st.subheader("Lucro por Produto")
                fig2 = px.bar(
                    df_cmv, x="nome", y="lucro",
                    color="lucro",
                    color_continuous_scale=["#e74c3c", "#f39c12", "#27ae60"],
                    labels={"nome": "Produto", "lucro": "Lucro R$"},
                )
                fig2.update_layout(height=350, margin=dict(t=20, b=40))
                st.plotly_chart(fig2, use_container_width=True)

        # Alertas de estoque
        if alertas:
            criticos = [a for a in alertas if a["status_estoque"] in ("SEM_ESTOQUE", "ABAIXO_MINIMO")]
            if criticos:
                st.warning(f"⚠️ {len(criticos)} insumo(s) com estoque crítico!")
                for a in criticos:
                    st.error(f"**{a['nome']}**: {a['estoque_atual']} {a['unidade_compra']} "
                            f"(mínimo: {a['estoque_minimo']})")

    except Exception as e:
        st.info("📋 Configure a conexão com o Supabase para ver os dados do dashboard.")
        st.caption(f"Detalhes: {e}")


# ============================================================
# INSUMOS
# ============================================================
def render_insumos():
    st.markdown('<p class="main-header">INSUMOS</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Cadastro de ingredientes, embalagens e materiais</p>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Lista", "➕ Cadastrar", "📦 Estoque", "📊 Movimentações"])

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
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "nome": "Insumo",
                        "unidade_compra": "Un. Compra",
                        "unidade_uso": "Un. Uso",
                        "custo_unitario": st.column_config.NumberColumn("Custo Unit.", format="R$ %.4f"),
                        "estoque_atual": st.column_config.NumberColumn("Estoque", format="%.3f"),
                        "estoque_minimo": st.column_config.NumberColumn("Mínimo", format="%.3f"),
                    }
                )

                # Editar/remover insumo
                st.subheader("Editar Insumo")
                nomes = {i["nome"]: i["id"] for i in insumos}
                sel = st.selectbox("Selecione o insumo", list(nomes.keys()), key="edit_insumo")
                if sel:
                    insumo = db_insumos.buscar_insumo(nomes[sel])
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        novo_custo = st.number_input("Custo unitário", value=float(insumo.get("custo_unitario", 0)), format="%.4f", key="ed_custo")
                    with col2:
                        novo_estoque = st.number_input("Estoque atual", value=float(insumo.get("estoque_atual", 0)), format="%.3f", key="ed_est")
                    with col3:
                        novo_minimo = st.number_input("Estoque mínimo", value=float(insumo.get("estoque_minimo", 0)), format="%.3f", key="ed_min")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("💾 Salvar Alterações", type="primary", key="btn_salvar_insumo"):
                            db_insumos.atualizar_insumo(nomes[sel], {
                                "custo_unitario": novo_custo,
                                "estoque_atual": novo_estoque,
                                "estoque_minimo": novo_minimo,
                            })
                            st.success("Insumo atualizado!")
                            st.rerun()
                    with col_b:
                        if st.button("🗑️ Desativar Insumo", key="btn_desativar_insumo"):
                            db_insumos.desativar_insumo(nomes[sel])
                            st.success("Insumo desativado!")
                            st.rerun()
            else:
                st.info("Nenhum insumo cadastrado ainda.")
        except Exception as e:
            st.info("Configure o Supabase para gerenciar insumos.")
            st.caption(str(e))

    with tab2:
        st.subheader("Novo Insumo")
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
                custo_un = st.number_input("Custo unitário (por un. uso)", min_value=0.0, format="%.4f")
            with col2:
                fornecedor = st.selectbox("Fornecedor principal", [""] + list(forn_map.keys()))
                unidade_uso = st.selectbox("Unidade de uso", ["g", "ml", "unid"])
                fator = st.number_input("Fator de conversão", value=1000.0, help="Ex: 1kg = 1000g")
            col3, col4 = st.columns(2)
            with col3:
                estoque = st.number_input("Estoque inicial", min_value=0.0, format="%.3f")
            with col4:
                est_min = st.number_input("Estoque mínimo", min_value=0.0, format="%.3f")

            if st.form_submit_button("Cadastrar Insumo", type="primary"):
                if nome:
                    dados = {
                        "nome": nome,
                        "unidade_compra": unidade_compra,
                        "unidade_uso": unidade_uso,
                        "fator_conversao": fator,
                        "custo_unitario": custo_un,
                        "estoque_atual": estoque,
                        "estoque_minimo": est_min,
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
                    st.warning("Preencha o nome do insumo.")

    with tab3:
        st.subheader("Alertas de Estoque")
        try:
            alertas = db_insumos.estoque_alertas()
            if alertas:
                df = pd.DataFrame(alertas)
                cores = {"SEM_ESTOQUE": "🔴", "ABAIXO_MINIMO": "🟠", "ATENCAO": "🟡", "OK": "🟢"}
                df["status"] = df["status_estoque"].map(cores) + " " + df["status_estoque"]
                st.dataframe(df[["nome", "categoria", "estoque_atual", "estoque_minimo",
                                "unidade_compra", "status", "fornecedor"]],
                            use_container_width=True, hide_index=True)

                # Ajuste rápido de estoque
                st.subheader("Ajuste Rápido")
                col1, col2, col3 = st.columns(3)
                with col1:
                    insumo_sel = st.selectbox("Insumo", [a["nome"] for a in alertas], key="ajuste_sel")
                with col2:
                    qtd_ajuste = st.number_input("Quantidade (+/-)", format="%.3f", key="ajuste_qtd")
                with col3:
                    obs_ajuste = st.text_input("Observação", key="ajuste_obs")
                if st.button("Aplicar Ajuste", key="btn_ajuste"):
                    insumo_id = next(a["id"] for a in alertas if a["nome"] == insumo_sel)
                    db_insumos.ajustar_estoque(insumo_id, qtd_ajuste, obs_ajuste)
                    st.success("Estoque ajustado!")
                    st.rerun()

                # Registrar perda
                st.subheader("Registrar Perda/Desvio")
                col1, col2, col3 = st.columns(3)
                with col1:
                    insumo_perda = st.selectbox("Insumo", [a["nome"] for a in alertas], key="perda_sel")
                with col2:
                    qtd_perda = st.number_input("Quantidade perdida", min_value=0.0, format="%.3f", key="perda_qtd")
                with col3:
                    motivo = st.text_input("Motivo", key="perda_motivo")
                if st.button("Registrar Perda", type="secondary", key="btn_perda"):
                    insumo_id = next(a["id"] for a in alertas if a["nome"] == insumo_perda)
                    db_insumos.registrar_perda(insumo_id, qtd_perda, motivo)
                    st.success("Perda registrada.")
                    st.rerun()
            else:
                st.info("Cadastre insumos para ver alertas.")
        except Exception as e:
            st.info("Configure o Supabase.")
            st.caption(str(e))

    with tab4:
        st.subheader("Histórico de Movimentações")
        try:
            movs = db_insumos.historico_movimentacoes()
            if movs:
                df = pd.DataFrame(movs)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma movimentação registrada.")
        except Exception as e:
            st.caption(str(e))


# ============================================================
# PRODUTOS & FICHAS TÉCNICAS
# ============================================================
def render_produtos():
    st.markdown('<p class="main-header">PRODUTOS & FICHAS TÉCNICAS</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Cardápio", "➕ Novo Produto", "📑 Ficha Técnica"])

    with tab1:
        try:
            produtos = db_produtos.listar_produtos()
            cmv = db_produtos.cmv_todos_produtos()
            cmv_map = {c["produto_id"]: c for c in cmv} if cmv else {}

            if produtos:
                for p in produtos:
                    c = cmv_map.get(p["id"], {})
                    with st.expander(f"🍔 {p['nome']} — R$ {p['preco_venda']:.2f}"):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Preço Venda", f"R$ {p['preco_venda']:.2f}")
                        with col2:
                            st.metric("Custo", f"R$ {c.get('custo_total', 0):.2f}")
                        with col3:
                            st.metric("Lucro", f"R$ {c.get('lucro', 0):.2f}")
                        with col4:
                            cmv_pct = c.get("cmv_pct", 0)
                            cor = "🟢" if cmv_pct < 30 else "🟡" if cmv_pct < 40 else "🔴"
                            st.metric("CMV", f"{cor} {cmv_pct:.1f}%")

                        # Editar preço
                        novo_preco = st.number_input(
                            "Novo preço", value=float(p["preco_venda"]),
                            format="%.2f", key=f"preco_{p['id']}"
                        )
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("Salvar Preço", key=f"btn_preco_{p['id']}"):
                                db_produtos.atualizar_produto(p["id"], {"preco_venda": novo_preco})
                                st.success("Preço atualizado!")
                                st.rerun()
                        with col_b:
                            if st.button("Desativar", key=f"btn_desat_{p['id']}"):
                                db_produtos.desativar_produto(p["id"])
                                st.warning("Produto desativado.")
                                st.rerun()

                        # Ficha técnica inline
                        ficha = db_produtos.listar_ficha_tecnica(p["id"])
                        if ficha:
                            st.caption("**Ficha Técnica:**")
                            for ing in ficha:
                                ins = ing.get("insumos", {})
                                st.text(f"  • {ins.get('nome', '?')} — {ing['quantidade']}{ins.get('unidade_uso', 'g')}")
            else:
                st.info("Nenhum produto cadastrado.")
        except Exception as e:
            st.info("Configure o Supabase.")
            st.caption(str(e))

    with tab2:
        st.subheader("Cadastrar Novo Produto")
        try:
            categorias = db_produtos.listar_categorias_produto()
            cat_map = {c["nome"]: c["id"] for c in categorias} if categorias else {}
        except:
            cat_map = {}

        with st.form("form_novo_produto"):
            nome = st.text_input("Nome do produto *")
            col1, col2 = st.columns(2)
            with col1:
                preco = st.number_input("Preço de venda (R$) *", min_value=0.0, format="%.2f")
                categoria = st.selectbox("Categoria", [""] + list(cat_map.keys()))
            with col2:
                descricao = st.text_area("Descrição")
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
                    st.warning("Preencha nome e preço.")

    with tab3:
        st.subheader("Montar Ficha Técnica")
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
                                nova_qtd = st.number_input(
                                    f"Qtd ({ins.get('unidade_uso', 'g')})",
                                    value=float(ing["quantidade"]),
                                    format="%.2f",
                                    key=f"ficha_{ing['id']}"
                                )
                                if nova_qtd != ing["quantidade"]:
                                    if st.button("Salvar", key=f"btn_ficha_{ing['id']}"):
                                        db_produtos.atualizar_gramatura(produto_id, ing["insumo_id"], nova_qtd)
                                        st.rerun()
                            with col3:
                                if st.button("❌", key=f"rm_ficha_{ing['id']}"):
                                    db_produtos.remover_ingrediente_ficha(produto_id, ing["insumo_id"])
                                    st.rerun()

                    st.divider()
                    st.caption("**Adicionar ingrediente:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        novo_ins = st.selectbox("Insumo", list(ins_map.keys()), key="add_ins")
                    with col2:
                        ins_info = ins_map.get(novo_ins, {})
                        nova_qtd = st.number_input(
                            f"Quantidade ({ins_info.get('unidade_uso', 'g')})",
                            min_value=0.0, format="%.2f", key="add_qtd"
                        )
                    with col3:
                        modo = st.text_input("Modo preparo", key="add_modo")
                    if st.button("➕ Adicionar à Ficha", type="primary"):
                        if nova_qtd > 0:
                            db_produtos.adicionar_ingrediente_ficha(
                                produto_id, ins_info["id"], nova_qtd, modo
                            )
                            st.success("Ingrediente adicionado!")
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
                            endereco = st.text_input("Endereço", value=f.get("endereco", "") or "", key=f"fend_{f['id']}")
                            obs = st.text_area("Observações", value=f.get("observacoes", "") or "", key=f"fo_{f['id']}")

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
                                st.warning("Fornecedor desativado.")
                                st.rerun()
            else:
                st.info("Nenhum fornecedor cadastrado.")
        except Exception as e:
            st.info("Configure o Supabase.")
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
                endereco = st.text_input("Endereço")
            obs = st.text_area("Observações")
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

    tab1, tab2 = st.tabs(["📋 Histórico", "➕ Registrar NF"])

    with tab1:
        try:
            notas = db_notas_fiscais.listar_notas()
            if notas:
                for nf in notas:
                    forn_nome = nf.get("fornecedores", {}).get("nome", "—") if nf.get("fornecedores") else "—"
                    with st.expander(f"📄 NF {nf.get('numero_nf', '—')} — {forn_nome} — R$ {nf['valor_total']:.2f} — {nf['data_emissao']}"):
                        detalhes = db_notas_fiscais.buscar_nota(nf["id"])
                        if detalhes.get("itens"):
                            df = pd.DataFrame(detalhes["itens"])
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        if st.button("🗑️ Excluir NF", key=f"del_nf_{nf['id']}"):
                            db_notas_fiscais.deletar_nota(nf["id"])
                            st.success("NF excluída.")
                            st.rerun()
            else:
                st.info("Nenhuma nota fiscal registrada.")
        except Exception as e:
            st.info("Configure o Supabase.")
            st.caption(str(e))

    with tab2:
        st.subheader("Registrar Nota Fiscal")
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
                numero_nf = st.text_input("Número NF")
            with col2:
                fornecedor = st.selectbox("Fornecedor", [""] + list(forn_map.keys()))
            with col3:
                data_nf = st.date_input("Data", value=date.today())

            st.subheader("Itens da NF")
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
                    valor_un = st.number_input("Valor unitário (R$)", min_value=0.0, format="%.2f", key=f"nf_val_{idx}")
                if insumo and qtd > 0 and valor_un > 0:
                    vt = round(qtd * valor_un, 2)
                    valor_total_calc += vt
                    itens_nf.append({
                        "insumo_id": ins_map[insumo]["id"],
                        "quantidade": qtd,
                        "valor_unitario": valor_un,
                        "valor_total": vt,
                    })

            st.metric("Total calculado", f"R$ {valor_total_calc:.2f}")

            if st.form_submit_button("Registrar Nota Fiscal", type="primary"):
                if itens_nf and fornecedor:
                    try:
                        dados_nf = {
                            "numero_nf": numero_nf,
                            "fornecedor_id": forn_map.get(fornecedor),
                            "data_emissao": data_nf.isoformat(),
                            "valor_total": valor_total_calc,
                        }
                        db_notas_fiscais.registrar_nota_fiscal(dados_nf, itens_nf)
                        st.success("✅ Nota fiscal registrada! Estoque e custos atualizados automaticamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Preencha fornecedor e pelo menos 1 item.")


# ============================================================
# PEDIDOS
# ============================================================
def render_pedidos():
    st.markdown('<p class="main-header">PEDIDOS</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Histórico", "➕ Novo Pedido", "📊 Por Canal"])

    with tab1:
        try:
            pedidos = db_pedidos.listar_pedidos()
            if pedidos:
                df = pd.DataFrame(pedidos)
                colunas = ["data_pedido", "numero_pedido", "canal", "total", "status"]
                colunas_existentes = [c for c in colunas if c in df.columns]
                st.dataframe(df[colunas_existentes], use_container_width=True, hide_index=True,
                            column_config={
                                "total": st.column_config.NumberColumn("Total", format="R$ %.2f"),
                            })
                # Excluir pedido
                st.subheader("Excluir Pedido")
                pedido_ids = {f"{p.get('numero_pedido', '—')} ({p['data_pedido'][:10]}) R${p['total']:.2f}": p["id"] for p in pedidos}
                sel = st.selectbox("Selecione", list(pedido_ids.keys()), key="del_pedido")
                if st.button("🗑️ Excluir", key="btn_del_pedido"):
                    db_pedidos.deletar_pedido(pedido_ids[sel])
                    st.success("Pedido excluído.")
                    st.rerun()
            else:
                st.info("Nenhum pedido registrado.")
        except Exception as e:
            st.caption(str(e))

    with tab2:
        st.subheader("Registrar Pedido")
        try:
            produtos = db_produtos.listar_produtos()
            prod_map = {p["nome"]: p for p in produtos} if produtos else {}
        except:
            prod_map = {}

        with st.form("form_pedido"):
            col1, col2, col3 = st.columns(3)
            with col1:
                numero = st.text_input("Nº Pedido")
            with col2:
                canal = st.selectbox("Canal", ["balcao", "ifood", "anota_ai", "whatsapp", "direto"])
            with col3:
                taxa_ent = st.number_input("Taxa entrega", min_value=0.0, format="%.2f")

            st.subheader("Itens")
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
                    itens_ped.append({
                        "produto_id": prod_map[prod]["id"],
                        "quantidade": qtd,
                        "preco_unitario": preco,
                        "preco_total": total_item,
                    })

            taxa_plat = st.number_input("Taxa plataforma (R$)", min_value=0.0, format="%.2f")
            desconto = st.number_input("Desconto (R$)", min_value=0.0, format="%.2f")
            total_pedido = subtotal + taxa_ent - desconto
            st.metric("Total", f"R$ {total_pedido:.2f}")

            if st.form_submit_button("Registrar Pedido", type="primary"):
                if itens_ped:
                    try:
                        dados = {
                            "numero_pedido": numero,
                            "canal": canal,
                            "subtotal": subtotal,
                            "taxa_entrega": taxa_ent,
                            "taxa_plataforma": taxa_plat,
                            "desconto": desconto,
                            "total": total_pedido,
                        }
                        db_pedidos.registrar_pedido(dados, itens_ped)
                        st.success("✅ Pedido registrado! Estoque atualizado automaticamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tab3:
        st.subheader("Vendas por Canal")
        try:
            col1, col2 = st.columns(2)
            with col1:
                di = st.date_input("De", value=date.today() - timedelta(days=30), key="canal_di")
            with col2:
                df_data = st.date_input("Até", value=date.today(), key="canal_df")
            resumo = db_pedidos.vendas_por_canal(di.isoformat(), df_data.isoformat())
            if resumo:
                dados_chart = [{"Canal": k, "Total": v["total"], "Pedidos": v["qtd"]} for k, v in resumo.items()]
                df = pd.DataFrame(dados_chart)
                fig = px.pie(df, values="Total", names="Canal", title="Faturamento por Canal")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.caption(str(e))


# ============================================================
# FINANCEIRO
# ============================================================
def render_financeiro():
    st.markdown('<p class="main-header">FINANCEIRO</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Runway", "📅 Fechamento Diário", "📈 Histórico"])

    with tab1:
        st.subheader("Análise de Runway")
        caixa = st.number_input("Caixa atual (R$)", value=9502.88, format="%.2f")
        if st.button("Calcular Runway", type="primary"):
            try:
                r = db_financeiro.calcular_runway(caixa)
                cor = "🔴" if r["risco"] == "CRITICO" else "🟡" if r["risco"] == "ALERTA" else "🟢"

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Runway", f"{cor} {r['runway_dias']} dias")
                with col2:
                    st.metric("Custo Fixo/Dia", f"R$ {r['custo_fixo_dia']:.2f}")
                with col3:
                    st.metric("Média Fat. 7d", f"R$ {r['media_faturamento_7d']:.2f}")

                if r["deficit_dia"] > 0:
                    st.error(f"⚠️ Déficit diário de R$ {r['deficit_dia']:.2f}. "
                            f"Com R$ {caixa:.2f} no caixa, restam {r['runway_dias']} dias.")
                else:
                    st.success("✅ Operação se pagando! Sem déficit diário.")
            except Exception as e:
                st.caption(str(e))

    with tab2:
        st.subheader("Fechamento do Dia")
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
            caixa_pos = st.number_input("Caixa após fechamento (R$)", format="%.2f")
            obs = st.text_input("Observações")

            if st.form_submit_button("Registrar Fechamento", type="primary"):
                try:
                    custos_dia = db_financeiro.total_custos_fixos_mensal() / 22
                    lucro = fat - custo_ins - custos_dia - taxas
                    db_financeiro.registrar_fechamento({
                        "data": data_fech.isoformat(),
                        "faturamento_bruto": fat,
                        "total_pedidos": ped_total,
                        "pedidos_direto": ped_direto,
                        "pedidos_ifood": ped_ifood,
                        "pedidos_outros": ped_total - ped_direto - ped_ifood,
                        "custo_insumos": custo_ins,
                        "custo_fixo_dia": round(custos_dia, 2),
                        "taxas_plataforma": taxas,
                        "lucro_bruto": round(lucro, 2),
                        "caixa_apos": caixa_pos,
                        "observacoes": obs,
                    })
                    st.success("✅ Fechamento registrado!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tab3:
        try:
            fechamentos = db_financeiro.listar_fechamentos()
            if fechamentos:
                df = pd.DataFrame(fechamentos)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["data"], y=df["faturamento_bruto"],
                                        name="Faturamento", line=dict(color="#27ae60")))
                fig.add_trace(go.Scatter(x=df["data"], y=df["lucro_bruto"],
                                        name="Lucro", line=dict(color="#3498db")))
                fig.update_layout(height=350, title="Evolução Financeira")
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(df, use_container_width=True, hide_index=True)

                # Excluir fechamento
                st.subheader("Remover Fechamento")
                fech_map = {f"{f['data']} — R$ {f['faturamento_bruto']:.2f}": f["id"] for f in fechamentos}
                sel = st.selectbox("Selecione", list(fech_map.keys()))
                if st.button("🗑️ Excluir Fechamento"):
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
    st.markdown('<p class="main-header">CMV & ENGENHARIA DE CARDÁPIO</p>', unsafe_allow_html=True)
    try:
        cmv = db_produtos.cmv_todos_produtos()
        if cmv:
            df = pd.DataFrame(cmv)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "nome": "Produto",
                    "preco_venda": st.column_config.NumberColumn("Venda", format="R$ %.2f"),
                    "custo_total": st.column_config.NumberColumn("Custo", format="R$ %.2f"),
                    "lucro": st.column_config.NumberColumn("Lucro", format="R$ %.2f"),
                    "cmv_pct": st.column_config.NumberColumn("CMV %", format="%.1f%%"),
                }
            )

            # Gráfico de margem
            fig = px.scatter(
                df, x="preco_venda", y="lucro", size="cmv_pct",
                color="cmv_pct", text="nome",
                color_continuous_scale=["#27ae60", "#f39c12", "#e74c3c"],
                labels={"preco_venda": "Preço Venda", "lucro": "Lucro R$", "cmv_pct": "CMV %"},
                title="Mapa de Rentabilidade"
            )
            fig.update_traces(textposition="top center")
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

            # Ranking
            st.subheader("Ranking de Lucratividade")
            df_sorted = df.sort_values("lucro", ascending=False)
            for i, row in df_sorted.iterrows():
                cor = "🟢" if row["cmv_pct"] < 30 else "🟡" if row["cmv_pct"] < 40 else "🔴"
                st.text(f"{cor} {row['nome']}: Lucro R$ {row['lucro']:.2f} | CMV {row['cmv_pct']:.1f}%")
        else:
            st.info("Cadastre produtos com fichas técnicas para ver o CMV.")
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
            st.metric("Total Mensal", f"R$ {total:,.2f}")
            st.metric("Custo/Dia (22 dias)", f"R$ {total/22:,.2f}")
            st.divider()

            if custos:
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
                                db_financeiro.atualizar_custo_fixo(c["id"], {
                                    "nome": nome, "valor": valor, "categoria": cat
                                })
                                st.success("Atualizado!")
                                st.rerun()
                        with col_b:
                            if st.button("🗑️ Desativar", key=f"btn_desat_cf_{c['id']}"):
                                db_financeiro.desativar_custo_fixo(c["id"])
                                st.warning("Desativado.")
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
                                                       "energia", "internet", "financeiro",
                                                       "administrativo", "outros"])
            with col3:
                recorrencia = st.selectbox("Recorrência", ["mensal", "semanal", "diario"])
            if st.form_submit_button("Cadastrar", type="primary"):
                if nome and valor > 0:
                    try:
                        db_financeiro.criar_custo_fixo({
                            "nome": nome, "valor": valor,
                            "categoria": categoria, "recorrencia": recorrencia,
                        })
                        st.success(f"✅ {nome} cadastrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))


# ============================================================
# ROTEADOR PRINCIPAL
# ============================================================
def main():
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


if __name__ == "__main__":
    main()
