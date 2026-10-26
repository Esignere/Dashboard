"""Demo finance data and calculations, isolated for a future API-backed repository."""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Any


CATEGORY_DEFAULTS: list[dict[str, str]] = [
    {"name": "Salário", "icon": "payments", "color": "#9D00FF", "type": "Entrada"},
    {"name": "Freelance", "icon": "work", "color": "#7A00FF", "type": "Entrada"},
    {"name": "Alimentação", "icon": "restaurant", "color": "#FF9F43", "type": "Saída"},
    {"name": "Transporte", "icon": "directions_car", "color": "#37C8AB", "type": "Saída"},
    {"name": "Moradia", "icon": "home", "color": "#A879FF", "type": "Saída"},
    {"name": "Saúde", "icon": "favorite", "color": "#FF6B81", "type": "Saída"},
    {"name": "Educação", "icon": "school", "color": "#53A6FF", "type": "Saída"},
    {"name": "Lazer", "icon": "movie", "color": "#FF7CA8", "type": "Saída"},
    {"name": "Outros", "icon": "category", "color": "#A49AAF", "type": "Saída"},
]

MONTHS_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def shift_month(month: date, offset: int) -> date:
    """Return the first day of the month offset from ``month``."""
    month_index = month.year * 12 + month.month - 1 + offset
    year, month_number = divmod(month_index, 12)
    return date(year, month_number + 1, 1)


def month_label(value: date) -> str:
    return MONTHS_PT[value.month - 1].capitalize()


def format_brl(value: float) -> str:
    formatted = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"


def seed_transactions(today: date | None = None) -> list[dict[str, Any]]:
    """Create a coherent six-month demo ledger with the requested October totals."""
    today = today or date.today()
    current_month = date(today.year, today.month, 1)
    earlier_months = [shift_month(current_month, offset) for offset in range(-5, 0)]

    history = [
        (5000, 3800),
        (4700, 3800),
        (5200, 3800),
        (5000, 4000),
        (5100, 3800),
    ]
    transactions: list[dict[str, Any]] = []
    for month, (income, expense) in zip(earlier_months, history):
        transactions.extend(
            [
                {
                    "id": f"income-{month:%Y%m}",
                    "description": "Salário",
                    "amount": float(income),
                    "type": "Entrada",
                    "category": "Salário",
                    "date": date(month.year, month.month, min(5, monthrange(month.year, month.month)[1])),
                    "notes": "",
                },
                {
                    "id": f"expense-{month:%Y%m}",
                    "description": "Despesas da casa",
                    "amount": float(expense),
                    "type": "Saída",
                    "category": "Moradia",
                    "date": date(month.year, month.month, min(18, monthrange(month.year, month.month)[1])),
                    "notes": "",
                },
            ]
        )

    day = min(today.day, monthrange(today.year, today.month)[1])
    current_transactions = [
        ("salary-current", "Salário", 4500, "Entrada", "Salário", min(5, day)),
        ("freelance-current", "Freelance", 500, "Entrada", "Freelance", min(12, day)),
        ("market-current", "Supermercado", 780, "Saída", "Alimentação", min(14, day)),
        ("internet-current", "Conta de internet", 180, "Saída", "Outros", min(16, day)),
        ("transport-current", "Transporte", 320, "Saída", "Transporte", min(18, day)),
        ("rent-current", "Aluguel", 800, "Saída", "Moradia", min(20, day)),
        ("leisure-current", "Lazer", 270, "Saída", "Lazer", day),
    ]
    for identifier, description, amount, transaction_type, category, transaction_day in current_transactions:
        transactions.append(
            {
                "id": identifier,
                "description": description,
                "amount": float(amount),
                "type": transaction_type,
                "category": category,
                "date": date(today.year, today.month, transaction_day),
                "notes": "",
            }
        )
    return transactions


def summarize(transactions: list[dict[str, Any]]) -> dict[str, float]:
    income = sum(item["amount"] for item in transactions if item["type"] == "Entrada")
    expenses = sum(item["amount"] for item in transactions if item["type"] == "Saída")
    return {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
        "savings": income - expenses,
    }


def monthly_totals(transactions: list[dict[str, Any]], months: int = 6) -> list[dict[str, Any]]:
    today = date.today()
    selected_months = [shift_month(date(today.year, today.month, 1), offset) for offset in range(-(months - 1), 1)]
    totals = []
    for month in selected_months:
        items = [
            item
            for item in transactions
            if item["date"].year == month.year and item["date"].month == month.month
        ]
        summary = summarize(items)
        totals.append(
            {
                "month": month,
                "label": month_label(month),
                "income": summary["income"],
                "expenses": summary["expenses"],
                "balance": summary["balance"],
            }
        )
    return totals
