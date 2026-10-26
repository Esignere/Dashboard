"""Interface Streamlit do protótipo FinanControl 2.0.

A aplicação reúne cinco áreas: painel, transações, relatórios, categorias e
configurações. O estado de demonstração (lançamentos, categorias e preferências)
fica em ``st.session_state`` durante a sessão do navegador; os cálculos e os
dados iniciais são fornecidos pelo módulo ``finance``. Não há persistência em
banco de dados ou comunicação com uma API.

Cada interação do Streamlit reexecuta este módulo. Por isso, os dados são
inicializados com ``setdefault`` e as ações de diálogos são guardadas no estado
da sessão para que o diálogo correto seja exibido após uma reexecução.
"""

from __future__ import annotations

import csv
from html import escape
import io
import uuid
from datetime import date
from typing import Any

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from finance import CATEGORY_DEFAULTS, format_brl, month_label, monthly_totals, seed_transactions, shift_month, summarize


# Configuração global da janela e paleta compartilhada por componentes e gráficos.
st.set_page_config(
    page_title="FinanControl 2.0",
    page_icon=":material/account_balance_wallet:",
    layout="wide",
    initial_sidebar_state="expanded",
)

PURPLE = "#9D00FF"
GREEN = "#39D98A"
RED = "#FF647C"
TEXT_MUTED = "#A49AAF"
CHART_COLORS = ["#9D00FF", "#37C8AB", "#FF9F43", "#53A6FF", "#FF6B81", "#A879FF"]

# Tema visual: CSS customiza o layout do Streamlit e as classes HTML usadas nas páginas.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&family=Material+Symbols+Rounded');
    /* Fundo, navegação, tipografia e componentes padrão do Streamlit. */
    :root { color-scheme: dark; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: #0A060E; }
    [data-testid="stSidebar"] { background: #120D1B; border-right: 1px solid #261D32; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
    [data-testid="stMainBlockContainer"] { max-width: 1540px; padding: 2rem 2.6rem 3rem; }
    h1, h2, h3 { font-family: 'Manrope', sans-serif !important; letter-spacing: -0.035em; }
    h1 { font-size: 2rem !important; font-weight: 800 !important; }
    h2 { font-size: 1.22rem !important; font-weight: 700 !important; }
    h3 { font-size: 1rem !important; font-weight: 700 !important; }
    p, label, [data-testid="stCaption"] { color: #A49AAF; }
    [data-testid="stMetric"] { padding: .15rem 0; }
    [data-testid="stMetricLabel"] { color: #A49AAF; font-size: .83rem; }
    [data-testid="stMetricValue"] { color: #F5F3FA; font-family: 'Manrope', sans-serif; font-size: 1.6rem; font-weight: 800; }
    [data-testid="stMetricDelta"] { font-size: .75rem; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: linear-gradient(145deg, #1B1427, #171020); border-color: #2A2038; border-radius: 17px; box-shadow: 0 8px 28px rgba(0,0,0,.16); }
    [data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: #493260; }
    [data-testid="stButton"] button, [data-testid="stDownloadButton"] button { border-radius: 10px; font-weight: 600; transition: all .18s ease; }
    [data-testid="stButton"] button[kind="primary"], [data-testid="stDownloadButton"] button[kind="primary"] { background: linear-gradient(110deg, #7A00FF, #9D00FF); border: 0; color: white; box-shadow: 0 5px 18px rgba(122,0,255,.25); }
    [data-testid="stButton"] button[kind="primary"]:hover { filter: brightness(1.12); transform: translateY(-1px); }
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stDateInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] > div, [data-testid="stTextArea"] textarea { background: #120D1B; border-color: #30243D; border-radius: 10px; }
    [data-testid="stRadio"] label { padding: .25rem .1rem; }
    [data-testid="stSidebar"] [data-testid="stRadio"] > div { gap: .3rem; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { border-radius: 10px; padding: .58rem .75rem; color: #BDB4C8; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background: rgba(157,0,255,.16); color: #F5F3FA; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p { color: #F5F3FA; }
    [data-testid="stRadio"] input { accent-color: #9D00FF; }
    [data-testid="stPopover"] button { border-radius: 10px; }
    /* Classes auxiliares para marca, perfil, cabeçalhos e valores financeiros. */
    .brand-lockup { display:flex; align-items:center; gap:11px; margin: .1rem 0 2.2rem; }
    .brand-mark { width:38px; height:38px; border-radius:12px; display:grid; place-items:center; color:#fff; background:linear-gradient(145deg,#9D00FF,#6200C9); box-shadow:0 5px 20px #7a00ff55; font-size:21px; }
    .brand-name { color:#F5F3FA; font-family:Manrope,sans-serif; font-size:15px; font-weight:800; line-height:1.15; }
    .brand-version { color:#A49AAF; font-size:10px; margin-top:3px; letter-spacing:.06em; }
    .eyebrow { color:#A49AAF; font-size:.74rem; letter-spacing:.09em; text-transform:uppercase; font-weight:700; margin-bottom:.3rem; }
    .page-subtitle { color:#A49AAF; margin-top:-.55rem; font-size:.92rem; }
    .sidebar-profile { border-top:1px solid #2A2038; margin-top:2rem; padding-top:1rem; display:flex; align-items:center; gap:10px; }
    .avatar { width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#8546FF,#D271FF); display:grid; place-items:center; color:white; font-weight:700; }
    .profile-name { color:#F5F3FA; font-weight:600; font-size:.82rem; }
    .profile-plan { color:#A49AAF; font-size:.7rem; margin-top:2px; }
    .section-head { display:flex; align-items:center; justify-content:space-between; gap:1rem; }
    .amount-positive { color:#39D98A; font-weight:700; }
    .amount-negative { color:#FF647C; font-weight:700; }
    .small-muted { color:#A49AAF; font-size:.75rem; }
    .transaction-heading { color:#8E849A; font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; }
    .transaction-title { color:#F5F3FA; font-weight:600; font-size:.88rem; }
    .stPlotlyChart { border-radius:12px; }
    /* Ajustes de espaçamento para telas menores. */
    @media (max-width: 900px) { [data-testid="stMainBlockContainer"] { padding:1.4rem 1.2rem 2rem; } }
    @media (max-width: 640px) { [data-testid="stMainBlockContainer"] { padding:1rem .85rem 1.5rem; } h1 { font-size:1.6rem !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)


# Rótulos e ícones da navegação lateral; PAGE_OPTIONS inclui o texto do controle.
PAGES = {
    "Dashboard": ":material/dashboard:",
    "Transações": ":material/swap_horiz:",
    "Relatórios": ":material/monitoring:",
    "Categorias": ":material/category:",
    "Configurações": ":material/settings:",
}
PAGE_OPTIONS = {page: f"{icon}  {page}" for page, icon in PAGES.items()}


def initialize_state() -> None:
    """Cria valores iniciais apenas para as chaves ainda ausentes da sessão.

    As transações e categorias são independentes por sessão do navegador; as
    demais chaves controlam a navegação, os diálogos e preferências do usuário.
    """
    st.session_state.setdefault("transactions", seed_transactions())
    st.session_state.setdefault("categories", [item.copy() for item in CATEGORY_DEFAULTS])
    st.session_state.setdefault("active_page", "Dashboard")
    st.session_state.setdefault("nav_option", PAGE_OPTIONS["Dashboard"])
    st.session_state.setdefault("modal_action", None)
    st.session_state.setdefault("editing_id", None)
    st.session_state.setdefault("monthly_goal", 3000.0)
    st.session_state.setdefault("user_name", "Rafael Mendes")


initialize_state()


def category_names(transaction_type: str | None = None) -> list[str]:
    """Retorna nomes de categorias, opcionalmente filtradas por entrada ou saída.

    Args:
        transaction_type: Tipo financeiro a considerar; ``None`` inclui todos.
    """
    categories = st.session_state.categories
    if transaction_type:
        categories = [item for item in categories if item["type"] == transaction_type]
    return [item["name"] for item in categories]


def current_month_transactions() -> list[dict[str, Any]]:
    """Seleciona os lançamentos cuja data pertence ao mês e ano atuais."""
    now = date.today()
    return [
        item for item in st.session_state.transactions
        if item["date"].year == now.year and item["date"].month == now.month
    ]


def header(title: str, subtitle: str) -> None:
    """Desenha o título padronizado e o subtítulo de uma página."""
    st.markdown(f"<div class='eyebrow'>Finanças pessoais</div><h1>{title}</h1><div class='page-subtitle'>{subtitle}</div>", unsafe_allow_html=True)


def transaction_dialog(edit_id: str | None = None) -> None:
    """Exibe formulário para criar um lançamento ou editar um existente.

    A validação impede descrição vazia, valor não positivo e categoria
    incompatível com o tipo. Ao salvar, atualiza a sessão e fecha o diálogo.

    Args:
        edit_id: Identificador do lançamento a editar; ``None`` cria um novo.
    """
    existing = next((item for item in st.session_state.transactions if item["id"] == edit_id), None)
    is_editing = existing is not None
    transaction_type = st.selectbox(
        "Tipo",
        ["Entrada", "Saída"],
        index=0 if not existing or existing["type"] == "Entrada" else 1,
        key=f"tx_type_{edit_id or 'new'}",
    )
    options = category_names(transaction_type)
    default_category = existing["category"] if existing and existing["category"] in options else (options[0] if options else "")
    with st.form(f"transaction-form-{edit_id or 'new'}", clear_on_submit=not is_editing):
        description = st.text_input("Descrição", value=existing["description"] if existing else "", placeholder="Ex.: mercado do mês")
        amount = st.number_input("Valor (R$)", min_value=0.0, value=float(existing["amount"]) if existing else 0.0, step=10.0, format="%.2f")
        category = st.selectbox("Categoria", options, index=options.index(default_category) if default_category else 0, disabled=not options)
        transaction_date = st.date_input("Data", value=existing["date"] if existing else date.today())
        notes = st.text_area("Observações (opcional)", value=existing.get("notes", "") if existing else "", height=80)
        left, right = st.columns(2)
        submitted = left.form_submit_button("Salvar alterações" if is_editing else "Adicionar transação", type="primary", width="stretch")
        cancelled = right.form_submit_button("Cancelar", width="stretch")

    if cancelled:
        st.session_state.modal_action = None
        st.rerun()
    if submitted:
        if not description.strip():
            st.error("Informe uma descrição para continuar.")
        elif amount <= 0:
            st.error("O valor precisa ser maior que zero.")
        elif not category or category not in category_names(transaction_type):
            st.error("Selecione uma categoria válida para o tipo escolhido.")
        else:
            record = {
                "id": existing["id"] if existing else str(uuid.uuid4()),
                "description": description.strip(),
                "amount": float(amount),
                "type": transaction_type,
                "category": category,
                "date": transaction_date,
                "notes": notes.strip(),
            }
            if existing:
                st.session_state.transactions = [
                    record if item["id"] == existing["id"] else item
                    for item in st.session_state.transactions
                ]
            else:
                st.session_state.transactions.append(record)
            st.session_state.modal_action = None
            st.toast("Transação atualizada." if is_editing else "Transação adicionada.", icon=":material/check_circle:")
            st.rerun()


@st.dialog("Confirmar exclusão", width="small")
def delete_dialog(transaction_id: str) -> None:
    """Pede confirmação e, se aprovado, remove um lançamento da sessão."""
    item = next((row for row in st.session_state.transactions if row["id"] == transaction_id), None)
    if item is None:
        st.session_state.modal_action = None
        st.rerun()
    st.write(f"Excluir **{item['description']}** de {format_brl(item['amount'])}? Essa ação não pode ser desfeita.")
    confirm_col, cancel_col = st.columns(2)
    if confirm_col.button("Excluir transação", type="primary", width="stretch"):
        st.session_state.transactions = [row for row in st.session_state.transactions if row["id"] != transaction_id]
        st.session_state.modal_action = None
        st.toast("Transação excluída.", icon=":material/delete:")
        st.rerun()
    if cancel_col.button("Cancelar", width="stretch"):
        st.session_state.modal_action = None
        st.rerun()


@st.dialog("Categoria", width="small")
def category_dialog(edit_name: str | None = None) -> None:
    """Exibe formulário para criar ou alterar uma categoria.

    Não permite nomes vazios ou repetidos. Ao renomear, também atualiza os
    lançamentos que referenciavam o nome anterior.

    Args:
        edit_name: Nome da categoria existente; ``None`` cria uma nova.
    """
    existing = next((item for item in st.session_state.categories if item["name"] == edit_name), None)
    with st.form(f"category-form-{edit_name or 'new'}"):
        name = st.text_input("Nome", value=existing["name"] if existing else "")
        transaction_type = st.selectbox(
            "Tipo",
            ["Entrada", "Saída"],
            index=0 if existing and existing["type"] == "Entrada" else 1,
            disabled=existing is not None,
        )
        icon = st.selectbox(
            "Ícone",
            ["category", "payments", "work", "restaurant", "directions_car", "home", "favorite", "school", "movie", "shopping_bag"],
            index=["category", "payments", "work", "restaurant", "directions_car", "home", "favorite", "school", "movie", "shopping_bag"].index(existing["icon"]) if existing and existing["icon"] in ["category", "payments", "work", "restaurant", "directions_car", "home", "favorite", "school", "movie", "shopping_bag"] else 0,
        )
        color = st.color_picker("Cor da categoria", value=existing["color"] if existing else PURPLE)
        save = st.form_submit_button("Salvar categoria", type="primary", width="stretch")
        cancel = st.form_submit_button("Cancelar", width="stretch")
    if cancel:
        st.session_state.modal_action = None
        st.rerun()
    if save:
        clean_name = name.strip()
        duplicate = any(item["name"].casefold() == clean_name.casefold() and item["name"] != edit_name for item in st.session_state.categories)
        if not clean_name:
            st.error("Informe um nome para a categoria.")
        elif duplicate:
            st.error("Já existe uma categoria com esse nome.")
        else:
            updated = {"name": clean_name, "type": transaction_type, "icon": icon, "color": color}
            if existing:
                st.session_state.categories = [updated if item["name"] == edit_name else item for item in st.session_state.categories]
                for transaction in st.session_state.transactions:
                    if transaction["category"] == edit_name:
                        transaction["category"] = clean_name
            else:
                st.session_state.categories.append(updated)
            st.session_state.modal_action = None
            st.toast("Categoria salva.", icon=":material/check_circle:")
            st.rerun()


@st.dialog("Excluir categoria", width="small")
def category_delete_dialog(name: str) -> None:
    """Exclui uma categoria, reatribuindo seus lançamentos quando necessário.

    A exclusão é bloqueada quando há lançamentos associados e não existe outra
    categoria do mesmo tipo para receber essas movimentações.

    Args:
        name: Nome da categoria que será removida.
    """
    usage_count = sum(item["category"] == name for item in st.session_state.transactions)
    st.write(f"A categoria **{name}** está vinculada a {usage_count} transação(ões).")
    category = next(item for item in st.session_state.categories if item["name"] == name)
    replacements = [item["name"] for item in st.session_state.categories if item["type"] == category["type"] and item["name"] != name]
    replacement = None
    if usage_count and replacements:
        preferred = "Outros" if "Outros" in replacements else replacements[0]
        replacement = st.selectbox("Reatribuir movimentações para", replacements, index=replacements.index(preferred))
    elif usage_count:
        st.warning("Não há outra categoria deste tipo. Crie uma categoria de substituição antes de excluir.")
        if st.button("Entendi", width="stretch"):
            st.session_state.modal_action = None
            st.rerun()
        return
    left, right = st.columns(2)
    if left.button("Excluir", type="primary", width="stretch"):
        if replacement:
            for transaction in st.session_state.transactions:
                if transaction["category"] == name:
                    transaction["category"] = replacement
        st.session_state.categories = [item for item in st.session_state.categories if item["name"] != name]
        st.session_state.modal_action = None
        st.toast("Categoria excluída.", icon=":material/delete:")
        st.rerun()
    if right.button("Cancelar", width="stretch"):
        st.session_state.modal_action = None
        st.rerun()


def transaction_rows(records: list[dict[str, Any]], key_prefix: str, actions: bool = True) -> None:
    """Renderiza lançamentos em linhas, com ações opcionais de edição e exclusão.

    ``key_prefix`` diferencia as chaves dos botões quando a tabela aparece em
    mais de uma página. Descrições e observações são escapadas antes do HTML.
    """
    if not records:
        st.caption("Nenhuma transação encontrada para os filtros selecionados.")
        return
    widths = [2.4, 1.15, 1.05, 1.05, 1.25, .9] if actions else [2.7, 1.25, 1.1, 1.25, .9]
    headers = st.columns(widths)
    labels = ["Descrição", "Categoria", "Data", "Tipo", "Valor", "Ações"] if actions else ["Descrição", "Categoria", "Data", "Tipo", "Valor"]
    for col, label in zip(headers, labels):
        col.markdown(f"<div class='transaction-heading'>{label}</div>", unsafe_allow_html=True)
    for item in records:
        cols = st.columns(widths)
        cols[0].markdown(
            f"<div class='transaction-title'>{escape(item['description'])}</div><div class='small-muted'>{escape(item.get('notes') or 'Movimentação financeira')}</div>",
            unsafe_allow_html=True,
        )
        cols[1].badge(item["category"], color="violet" if item["type"] == "Entrada" else "gray")
        cols[2].markdown(item["date"].strftime("%d/%m/%Y"))
        cols[3].badge(item["type"], color="green" if item["type"] == "Entrada" else "red")
        amount_color = "amount-positive" if item["type"] == "Entrada" else "amount-negative"
        sign = "+" if item["type"] == "Entrada" else "−"
        value = f"{sign} {format_brl(item['amount'])}"
        if actions:
            cols[4].markdown(f"<div class='{amount_color}'>{value}</div>", unsafe_allow_html=True)
            with cols[5]:
                edit_col, delete_col = st.columns(2, gap="small")
                with edit_col:
                    edit_clicked = st.button("✎", key=f"{key_prefix}-edit-{item['id']}", help="Editar transação")
                with delete_col:
                    delete_clicked = st.button("×", key=f"{key_prefix}-delete-{item['id']}", help="Excluir transação")
            if edit_clicked:
                st.session_state.modal_action = "edit_transaction"
                st.session_state.editing_id = item["id"]
                st.rerun()
            if delete_clicked:
                st.session_state.modal_action = "delete_transaction"
                st.session_state.editing_id = item["id"]
                st.rerun()
        else:
            cols[4].markdown(f"<div class='{amount_color}'>{value}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:1px;background:#2A2038;margin:.35rem 0 .8rem'></div>", unsafe_allow_html=True)


def plot_layout(fig: go.Figure, height: int = 300) -> go.Figure:
    """Aplica aos gráficos Plotly o tema escuro compartilhado pelo aplicativo.

    Args:
        fig: Figura já preenchida com dados e traces.
        height: Altura do gráfico em pixels.

    Returns:
        A mesma figura com layout, fontes, legenda e cores de fundo padronizados.
    """
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "DM Sans, sans-serif", "color": TEXT_MUTED, "size": 11},
        margin={"l": 8, "r": 8, "t": 18, "b": 8},
        legend={"orientation": "h", "y": 1.12, "x": 0, "font": {"size": 11}},
        hoverlabel={"bgcolor": "#21172D", "bordercolor": "#493260", "font": {"color": "#F5F3FA"}},
    )
    return fig


def monthly_totals_for_year(transactions: list[dict[str, Any]], year: int) -> list[dict[str, Any]]:
    """Agrupa entradas, saídas e saldo por mês para um ano civil completo.

    Inclui os 12 meses, inclusive aqueles sem lançamentos, para manter os eixos
    dos relatórios consistentes.
    """
    totals = []
    for month in range(1, 13):
        selected = [
            item for item in transactions
            if item["date"].year == year and item["date"].month == month
        ]
        summary = summarize(selected)
        totals.append({
            "month": date(year, month, 1),
            "label": month_label(date(year, month, 1)),
            "income": summary["income"],
            "expenses": summary["expenses"],
            "balance": summary["balance"],
        })
    return totals


def dashboard() -> None:
    """Monta o painel com indicadores, gráficos e os lançamentos mais recentes.

    Os indicadores comparam o mês atual ao anterior; os gráficos mostram fluxo
    financeiro e distribuição das despesas do mês corrente.
    """
    top = st.columns([2.5, 1.05, .55, 1.15], vertical_alignment="bottom")
    with top[0]:
        header("Visão geral", "Acompanhe sua vida financeira em um só lugar")
    period = top[1].selectbox("Período", ["Últimos 6 meses", "Este ano", "Este mês"], label_visibility="collapsed", key="dashboard_period")
    with top[2]:
        with st.popover(":material/notifications:", help="Notificações"):
            st.markdown("### Tudo em dia")
            st.caption("Você não tem notificações novas.")
    with top[3]:
        if st.button("+ Nova transação", type="primary", width="stretch"):
            st.session_state.modal_action = "new_transaction"
            st.rerun()

    transactions = st.session_state.transactions
    now = date.today()
    current = [item for item in transactions if item["date"].year == now.year and item["date"].month == now.month]
    previous_month = shift_month(date(now.year, now.month, 1), -1)
    previous = [item for item in transactions if item["date"].year == previous_month.year and item["date"].month == previous_month.month]
    current_summary = summarize(current)
    previous_summary = summarize(previous)
    all_balance = summarize(transactions)["balance"]
    previous_balance = all_balance - current_summary["balance"]
    balance_change = ((all_balance / previous_balance) - 1) * 100 if previous_balance else 0
    income_change = ((current_summary["income"] / previous_summary["income"]) - 1) * 100 if previous_summary["income"] else 0
    expense_change = ((previous_summary["expenses"] - current_summary["expenses"]) / previous_summary["expenses"]) * 100 if previous_summary["expenses"] else 0
    prior_savings = previous_summary["savings"]
    savings_change = ((current_summary["savings"] / prior_savings) - 1) * 100 if prior_savings else 0
    st.space("medium")
    kpis = st.columns(4)
    cards = [
        (":material/account_balance_wallet: Saldo total", format_brl(all_balance), f"{balance_change:+.1f}% vs. mês anterior"),
        (":material/trending_up: Entradas do mês", format_brl(current_summary["income"]), f"{income_change:+.1f}% vs. mês anterior"),
        (":material/trending_down: Saídas do mês", format_brl(current_summary["expenses"]), f"{expense_change:+.1f}% {'menor' if expense_change >= 0 else 'maior'} vs. mês anterior"),
        (":material/savings: Economia mensal", format_brl(current_summary["savings"]), f"{savings_change:+.1f}% vs. mês anterior"),
    ]
    for col, (label, value, delta) in zip(kpis, cards):
        with col.container(border=True):
            st.metric(label, value, delta, delta_color="normal")
    st.space("medium")

    totals = monthly_totals(transactions, 12 if period == "Este ano" else (1 if period == "Este mês" else 6))
    left, right = st.columns([1.65, 1])
    with left.container(border=True):
        st.markdown("#### Fluxo financeiro")
        st.caption("Entradas e saídas ao longo do período")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[row["label"] for row in totals], y=[row["income"] for row in totals],
            name="Entradas", mode="lines+markers", line={"color": PURPLE, "width": 3, "shape": "spline"},
            marker={"size": 6, "color": PURPLE}, fill="tozeroy", fillcolor="rgba(157,0,255,.10)",
            hovertemplate="%{x}<br>Entradas: R$ %{y:,.2f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[row["label"] for row in totals], y=[row["expenses"] for row in totals],
            name="Saídas", mode="lines+markers", line={"color": GREEN, "width": 3, "shape": "spline"},
            marker={"size": 6, "color": GREEN}, hovertemplate="%{x}<br>Saídas: R$ %{y:,.2f}<extra></extra>",
        ))
        fig.update_yaxes(showgrid=True, gridcolor="#2A2038", zeroline=False, tickprefix="R$ ", tickformat="~s")
        fig.update_xaxes(showgrid=False, tickfont={"color": "#A49AAF"})
        plot_layout(fig, 300)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with right.container(border=True):
        st.markdown("#### Despesas por categoria")
        st.caption(f"Distribuição de {month_label(now)}")
        by_category: dict[str, float] = {}
        for item in current:
            if item["type"] == "Saída":
                by_category[item["category"]] = by_category.get(item["category"], 0) + item["amount"]
        if by_category:
            donut = px.pie(
                names=list(by_category), values=list(by_category.values()), hole=.72,
                color_discrete_sequence=CHART_COLORS,
            )
            donut.update_traces(
                textinfo="percent", textfont={"color": "#F5F3FA", "size": 11},
                hovertemplate="%{label}<br>R$ %{value:,.2f} (%{percent})<extra></extra>",
                marker={"line": {"color": "#181222", "width": 3}},
            )
            plot_layout(donut, 250)
            donut.update_layout(showlegend=True, legend={"orientation": "h", "y": -.08, "x": 0, "font": {"size": 10}})
            st.plotly_chart(donut, width="stretch", config={"displayModeBar": False})
        else:
            st.info("Adicione despesas neste mês para visualizar a distribuição.")
        st.markdown(f"<div class='small-muted'>Total de saídas <span style='float:right;color:#F5F3FA;font-weight:700'>{format_brl(current_summary['expenses'])}</span></div>", unsafe_allow_html=True)

    st.space("medium")
    st.markdown("#### Transações recentes")
    if st.button("Ver todas", key="dashboard-view-all", type="secondary"):
        st.session_state.active_page = "Transações"
        st.session_state.nav_option = PAGE_OPTIONS["Transações"]
        st.rerun()
    recent = sorted(transactions, key=lambda row: (row["date"], row["id"]), reverse=True)[:5]
    with st.container(border=True):
        transaction_rows(recent, "dashboard")


def transactions_page() -> None:
    """Monta a lista de transações com busca, filtros e paginação."""
    header("Transações", "Acompanhe entradas e saídas em um só lugar")
    st.space("medium")
    top = st.columns([1.5, 1, 1, 1, 1.1], vertical_alignment="bottom")
    search = top[0].text_input("Pesquisar", placeholder="Buscar transação...", key="tx_search")
    category_filter = top[1].selectbox("Categoria", ["Todas"] + category_names(), key="tx_category_filter")
    type_filter = top[2].selectbox("Tipo", ["Todos", "Entrada", "Saída"], key="tx_type_filter")
    month_options = sorted({(item["date"].year, item["date"].month) for item in st.session_state.transactions}, reverse=True)
    month_labels = ["Todos os períodos"] + [f"{month_label(date(year, month, 1))} {year}" for year, month in month_options]
    month_filter = top[3].selectbox("Período", month_labels, key="tx_month_filter")
    with top[4]:
        if st.button("+ Nova transação", type="primary", width="stretch", key="tx-new"):
            st.session_state.modal_action = "new_transaction"
            st.rerun()
    rows = list(st.session_state.transactions)
    if search.strip():
        query = search.strip().casefold()
        rows = [item for item in rows if query in item["description"].casefold() or query in item["category"].casefold()]
    if category_filter != "Todas":
        rows = [item for item in rows if item["category"] == category_filter]
    if type_filter != "Todos":
        rows = [item for item in rows if item["type"] == type_filter]
    if month_filter != "Todos os períodos":
        year, month = month_options[month_labels.index(month_filter) - 1]
        rows = [item for item in rows if item["date"].year == year and item["date"].month == month]
    rows.sort(key=lambda item: (item["date"], item["id"]), reverse=True)
    page_size = 6
    total_pages = max(1, (len(rows) + page_size - 1) // page_size)
    st.session_state.tx_page = min(st.session_state.get("tx_page", 1), total_pages)
    page_number = st.session_state.tx_page
    paged = rows[(page_number - 1) * page_size:page_number * page_size]
    with st.container(border=True):
        transaction_rows(paged, "transactions")
    page_cols = st.columns([2, 1, 2])
    page_cols[0].caption(f"{len(rows)} transação(ões)")
    with page_cols[1]:
        previous_col, next_col = st.columns(2)
        if previous_col.button("← Anterior", disabled=page_number <= 1, width="stretch"):
            st.session_state.tx_page -= 1
            st.rerun()
        if next_col.button("Próxima →", disabled=page_number >= total_pages, width="stretch"):
            st.session_state.tx_page += 1
            st.rerun()
    page_cols[2].markdown(f"<div style='text-align:right;color:#A49AAF;padding-top:.5rem'>Página {page_number} de {total_pages}</div>", unsafe_allow_html=True)


def reports_page() -> None:
    """Monta relatórios filtráveis e a exportação dos lançamentos em CSV.

    Ano, mês, período de datas e categoria limitam os indicadores, os gráficos
    e o conteúdo exportado.
    """
    header("Relatórios", "Entenda seus hábitos e acompanhe sua evolução financeira")
    st.space("medium")
    transactions = st.session_state.transactions
    years = sorted({item["date"].year for item in transactions}, reverse=True) or [date.today().year]
    filters = st.columns([.8, .9, 1.25, 1.7, 1])
    year = filters[0].selectbox("Ano", years, key="report_year")
    months = ["Todos"] + [month_label(date(year, month, 1)) for month in range(1, 13)]
    month = filters[1].selectbox("Mês", months, key="report_month")
    category = filters[2].selectbox("Categoria", ["Todas"] + category_names(), key="report_category")
    date_range = filters[3].date_input(
        "Intervalo de datas",
        value=(date(year, 1, 1), date(year, 12, 31)),
        key="report_date_range",
    )
    st.caption("Os filtros se aplicam aos indicadores, gráficos e arquivo CSV.")
    filtered = [item for item in transactions if item["date"].year == year]
    if month != "Todos":
        month_number = next(index for index in range(1, 13) if month_label(date(year, index, 1)) == month)
        filtered = [item for item in filtered if item["date"].month == month_number]
    if len(date_range) == 2:
        filtered = [item for item in filtered if date_range[0] <= item["date"] <= date_range[1]]
    if category != "Todas":
        filtered = [item for item in filtered if item["category"] == category]
    summary = summarize(filtered)
    previous_period = [
        item for item in transactions
        if item["date"].year == year - 1
        and (month == "Todos" or item["date"].month == month_number)
        and (category == "Todas" or item["category"] == category)
    ]
    prev_summary = summarize(previous_period)
    metrics = st.columns(3)
    metrics[0].metric("Entradas no período", format_brl(summary["income"]), f"{len([i for i in filtered if i['type'] == 'Entrada'])} movimentações")
    metrics[1].metric("Saídas no período", format_brl(summary["expenses"]), f"{len([i for i in filtered if i['type'] == 'Saída'])} movimentações", delta_color="inverse")
    metrics[2].metric("Saldo do período", format_brl(summary["balance"]), f"{summary['balance'] - prev_summary['balance']:+,.2f} vs. ano anterior")
    st.space("medium")
    chart_left, chart_right = st.columns(2)
    with chart_left.container(border=True):
        st.markdown("#### Entradas e saídas")
        filtered_months = monthly_totals_for_year(filtered, year)
        flow = go.Figure()
        flow.add_trace(go.Bar(x=[row["label"] for row in filtered_months], y=[row["income"] for row in filtered_months], name="Entradas", marker_color=PURPLE, hovertemplate="%{x}<br>Entradas: R$ %{y:,.2f}<extra></extra>"))
        flow.add_trace(go.Bar(x=[row["label"] for row in filtered_months], y=[row["expenses"] for row in filtered_months], name="Saídas", marker_color=GREEN, hovertemplate="%{x}<br>Saídas: R$ %{y:,.2f}<extra></extra>"))
        flow.update_layout(barmode="group")
        flow.update_yaxes(showgrid=True, gridcolor="#2A2038", tickprefix="R$ ", tickformat="~s")
        plot_layout(flow, 310)
        st.plotly_chart(flow, width="stretch", config={"displayModeBar": False})
    with chart_right.container(border=True):
        st.markdown("#### Evolução do saldo")
        grouped = monthly_totals_for_year(filtered, year)
        running = 0.0
        balances = []
        for row in grouped:
            running += row["balance"]
            balances.append(running)
        balance_fig = go.Figure(go.Scatter(
            x=[row["label"] for row in grouped], y=balances, mode="lines+markers",
            line={"color": PURPLE, "width": 3, "shape": "spline"},
            fill="tozeroy", fillcolor="rgba(157,0,255,.12)",
            hovertemplate="%{x}<br>Saldo acumulado: R$ %{y:,.2f}<extra></extra>",
        ))
        balance_fig.update_yaxes(showgrid=True, gridcolor="#2A2038", tickprefix="R$ ", tickformat="~s")
        plot_layout(balance_fig, 310)
        st.plotly_chart(balance_fig, width="stretch", config={"displayModeBar": False})
    lower_left, lower_right = st.columns([1, 1.3])
    with lower_left.container(border=True):
        st.markdown("#### Despesas por categoria")
        expenses: dict[str, float] = {}
        for item in filtered:
            if item["type"] == "Saída":
                expenses[item["category"]] = expenses.get(item["category"], 0) + item["amount"]
        if expenses:
            fig = px.pie(names=list(expenses), values=list(expenses.values()), hole=.68, color_discrete_sequence=CHART_COLORS)
            fig.update_traces(hovertemplate="%{label}<br>R$ %{value:,.2f} (%{percent})<extra></extra>", textinfo="percent")
            plot_layout(fig, 270)
            fig.update_layout(showlegend=True, legend={"orientation": "h", "y": -.08, "x": 0, "font": {"size": 10}})
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        else:
            st.caption("Sem despesas para este filtro.")
    with lower_right.container(border=True):
        st.markdown("#### Comparação entre meses")
        comparison = monthly_totals_for_year(filtered, year)
        comparison_fig = go.Figure()
        comparison_fig.add_trace(go.Bar(x=[row["label"] for row in comparison], y=[row["income"] for row in comparison], name="Entradas", marker_color=PURPLE))
        comparison_fig.add_trace(go.Bar(x=[row["label"] for row in comparison], y=[row["expenses"] for row in comparison], name="Saídas", marker_color=GREEN))
        comparison_fig.update_layout(barmode="group")
        comparison_fig.update_yaxes(showgrid=True, gridcolor="#2A2038", tickprefix="R$ ", tickformat="~s")
        plot_layout(comparison_fig, 270)
        st.plotly_chart(comparison_fig, width="stretch", config={"displayModeBar": False})
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Descrição", "Categoria", "Data", "Tipo", "Valor", "Observações"])
    for item in sorted(filtered, key=lambda row: row["date"]):
        writer.writerow([item["description"], item["category"], item["date"].strftime("%d/%m/%Y"), item["type"], f"{item['amount']:.2f}".replace(".", ","), item.get("notes", "")])
    st.download_button("Exportar relatório CSV", output.getvalue().encode("utf-8-sig"), file_name="financontrol-relatorio.csv", mime="text/csv", type="primary")


def categories_page() -> None:
    """Lista categorias de entrada e saída e oferece ações de manutenção."""
    top = st.columns([2, 1], vertical_alignment="bottom")
    with top[0]:
        header("Categorias", "Organize suas movimentações com a sua identidade visual")
    with top[1]:
        if st.button("+ Nova categoria", type="primary", width="stretch"):
            st.session_state.modal_action = "new_category"
            st.rerun()
    st.space("medium")
    for kind in ["Entrada", "Saída"]:
        records = [item for item in st.session_state.categories if item["type"] == kind]
        st.markdown(f"#### Categorias de {kind.lower()}s")
        for start in range(0, len(records), 3):
            cols = st.columns(3)
            for col, item in zip(cols, records[start:start + 3]):
                with col.container(border=True):
                    col.markdown(
                        f"<div style='display:flex;align-items:center;gap:12px'><span style='width:38px;height:38px;border-radius:12px;background:{item['color']}22;color:{item['color']};display:grid;place-items:center'><span class='material-symbols-rounded'>{escape(item['icon'])}</span></span><div><div style='font-weight:700;color:#F5F3FA'>{escape(item['name'])}</div><div class='small-muted'>{escape(item['type'])}</div></div></div>",
                        unsafe_allow_html=True,
                    )
                    edit_col, delete_col = st.columns(2)
                    if edit_col.button("Editar", key=f"category-edit-{item['name']}", width="stretch"):
                        st.session_state.editing_id = item["name"]
                        st.session_state.modal_action = "edit_category"
                        st.rerun()
                    if delete_col.button("Excluir", key=f"category-delete-{item['name']}", width="stretch"):
                        st.session_state.editing_id = item["name"]
                        st.session_state.modal_action = "delete_category"
                        st.rerun()


def settings_page() -> None:
    """Monta as preferências do perfil, meta de economia e restauração de dados.

    As preferências são locais à sessão; restaurar dados repõe lançamentos e
    categorias de demonstração sem alterar o restante das configurações.
    """
    header("Configurações", "Personalize sua experiência no FinanControl")
    st.space("medium")
    with st.container(border=True):
        st.markdown("#### Perfil")
        st.text_input("Nome", key="user_name")
        st.text_input("E-mail", value="rafael@email.com", disabled=True)
        st.caption("Seu perfil é local a esta demonstração.")
    st.space("small")
    with st.container(border=True):
        st.markdown("#### Preferências")
        st.number_input("Meta mensal de economia (R$)", min_value=0.0, step=100.0, key="monthly_goal")
        st.toggle("Receber notificações de resumo mensal", value=True, key="monthly_notifications")
        savings = summarize(current_month_transactions())["savings"]
        progress = max(0.0, min(savings / st.session_state.monthly_goal, 1.0)) if st.session_state.monthly_goal else 0.0
        st.progress(progress, text=f"{format_brl(savings)} economizados de {format_brl(st.session_state.monthly_goal)}")
    with st.container(border=True):
        st.markdown("#### Dados e privacidade")
        st.caption("Este protótipo usa somente dados de demonstração mantidos durante a sessão. Nenhum banco de dados ou serviço externo está conectado.")
        if st.button("Restaurar dados de demonstração"):
            st.session_state.transactions = seed_transactions()
            st.session_state.categories = [item.copy() for item in CATEGORY_DEFAULTS]
            st.toast("Dados de demonstração restaurados.")
            st.rerun()


# Navegação global: atualiza a página ativa e apresenta o perfil da sessão.
with st.sidebar:
    st.markdown(
        "<div class='brand-lockup'><div class='brand-mark'>◈</div><div><div class='brand-name'>FinanControl</div><div class='brand-version'>FINANÇAS, COM CLAREZA · 2.0</div></div></div>",
        unsafe_allow_html=True,
    )
    selected_option = st.radio(
        "Navegação",
        list(PAGE_OPTIONS.values()),
        key="nav_option",
        label_visibility="collapsed",
    )
    selected = next(page for page, option in PAGE_OPTIONS.items() if option == selected_option)
    st.session_state.active_page = selected
    st.markdown(
        f"<div class='sidebar-profile'><div class='avatar'>RM</div><div><div class='profile-name'>{escape(st.session_state.user_name)}</div><div class='profile-plan'>Plano pessoal · Gratuito</div></div><span style='margin-left:auto;color:#A49AAF'>⋯</span></div>",
        unsafe_allow_html=True,
    )

# Despacho da página ativa. Os diálogos são processados ao final para que
# possam ser abertos por ações iniciadas em qualquer página.
if selected == "Dashboard":
    dashboard()
elif selected == "Transações":
    transactions_page()
elif selected == "Relatórios":
    reports_page()
elif selected == "Categorias":
    categories_page()
else:
    settings_page()

action = st.session_state.modal_action
if action == "new_transaction":
    transaction_dialog()
elif action == "edit_transaction":
    transaction_dialog(st.session_state.editing_id)
elif action == "delete_transaction":
    delete_dialog(st.session_state.editing_id)
elif action == "new_category":
    category_dialog()
elif action == "edit_category":
    category_dialog(st.session_state.editing_id)
elif action == "delete_category":
    category_delete_dialog(st.session_state.editing_id)
