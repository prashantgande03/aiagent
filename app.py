import os
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)
api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("Apikey") or "").strip()
model = "gemini-flash-lite-latest"
interactions_url = "https://generativelanguage.googleapis.com/v1beta/interactions"

CURRENCIES = {
    "INR (₹)": "₹",
    "USD ($)": "$",
    "EUR (€)": "€",
    "GBP (£)": "£",
}
CATEGORIES = [
    "Housing",
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Shopping",
    "Entertainment",
    "Education",
    "Other",
]

st.set_page_config(
    page_title="PocketWise | Personal Finance",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
    .stApp { background: #f5f7f6; color: #172a23; }
    [data-testid="stMain"] > div { max-width: 1280px; }
    .hero {
        padding: 1.8rem 2rem; border-radius: 20px; color: white;
        background: linear-gradient(115deg, #123d32 0%, #17664d 68%, #25805e 100%);
        margin: .25rem 0 1.25rem;
        box-shadow: 0 10px 28px rgba(18, 61, 50, .12);
    }
    .hero .eyebrow {
        margin: 0 0 .45rem; color: #b8ddca; font-size: .75rem;
        font-weight: 700; letter-spacing: .12em;
    }
    .hero h1 { margin: 0; color: white; font-size: 2rem; letter-spacing: -.03em; }
    .hero p { margin: .45rem 0 0; color: #d7eee3; font-size: 1rem; }
    div[data-testid="stMetric"] {
        background: white; padding: 1rem 1.15rem; border-radius: 14px;
        border: 1px solid #e4ebe6; box-shadow: 0 2px 8px rgba(23, 42, 35, .03);
    }
    div[data-testid="stMetricLabel"] p { color: #53665d; font-weight: 600; }
    div[data-testid="stMetricValue"] { color: #163f32; }
    div[data-testid="stTabs"] button { font-weight: 600; }
    div[data-testid="stForm"] {
        background: white; border: 1px solid #e4ebe6; border-radius: 14px;
        padding: 1rem;
    }
    div[data-testid="stExpander"] {
        background: white; border: 1px solid #e4ebe6; border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "interaction_id" not in st.session_state:
    st.session_state.interaction_id = None
if "transactions" not in st.session_state:
    st.session_state.transactions = []

st.markdown(
    """
    <div class="hero">
      <p class="eyebrow">POCKETWISE · PERSONAL FINANCE</p>
      <h1>Make your money work for you.</h1>
      <p>A simple monthly plan, a clear view of your expenses, and practical guidance in one place.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    "Personal finance workspace  ·  No bank connection  ·  Your entries stay in this browser session"
)

month_key = date.today().strftime("%Y-%m")
month_label = date.today().strftime("%B %Y")
month_transactions = [
    transaction
    for transaction in st.session_state.transactions
    if transaction["date"].startswith(month_key)
]
monthly_spending = sum(transaction["amount"] for transaction in month_transactions)
monthly_salary = st.session_state.get("monthly_salary", 0.0)
other_income = st.session_state.get("other_income", 0.0)
monthly_income = monthly_salary + other_income
monthly_budget = st.session_state.get("monthly_budget", 0.0)
savings_goal = st.session_state.get("savings_goal", 0.0)
remaining_budget = monthly_budget - monthly_spending
estimated_savings = monthly_income - monthly_spending
savings_progress = (
    max(0.0, min(estimated_savings / savings_goal, 1.0))
    if savings_goal > 0
    else 0.0
)

st.subheader("1. Set your monthly plan")
st.caption(
    "Use your usual after-tax amounts. These are planning figures, not bank data. "
    "Choose one currency for all amounts."
)
with st.container(border=True):
    income_columns = st.columns([1.2, 1.2, 1])
    with income_columns[0]:
        currency_name = st.selectbox(
            "Display currency",
            list(CURRENCIES),
            help="Choose the currency for all entered and displayed amounts. This changes the symbol only; it does not convert values.",
        )
        currency_symbol = CURRENCIES[currency_name]
    with income_columns[1]:
        monthly_salary = st.number_input(
            f"1. Monthly salary ({currency_symbol})",
            min_value=0.0,
            step=1000.0,
            key="monthly_salary",
            help="Your regular salary after tax for a typical month. Enter 0 if you do not receive a salary.",
        )
        st.caption("Your regular pay after tax. This is income, not an expense.")
    with income_columns[2]:
        other_income = st.number_input(
            f"2. Other monthly income ({currency_symbol})",
            min_value=0.0,
            step=500.0,
            key="other_income",
            help="Include other income you expect this month, such as freelance work or benefits. Leave at 0 if none.",
        )
        st.caption("Extra money you expect, such as freelance or side-work income.")
    plan_columns = st.columns(2)
    with plan_columns[0]:
        monthly_budget = st.number_input(
            f"3. Monthly expense budget ({currency_symbol})",
            min_value=0.0,
            step=1000.0,
            key="monthly_budget",
            help="Your planned maximum spending for the month. Record actual expenses in the Expense tracker tab.",
        )
        st.caption("How much you plan to spend this month. Log each actual purchase in Expense tracker.")
    with plan_columns[1]:
        savings_goal = st.number_input(
            f"4. Monthly savings target ({currency_symbol})",
            min_value=0.0,
            step=500.0,
            key="savings_goal",
            help="How much you want to save this month. Progress is estimated from income minus logged expenses.",
        )
        st.caption("How much you want to put aside this month. This is your goal, not an expense.")

monthly_income = monthly_salary + other_income
remaining_budget = monthly_budget - monthly_spending
estimated_savings = monthly_income - monthly_spending
savings_progress = (
    max(0.0, min(estimated_savings / savings_goal, 1.0))
    if savings_goal > 0
    else 0.0
)

with st.expander("What am I entering, and how are these numbers calculated?"):
    st.markdown(
        f"""
        **Set your plan above:** enter your after-tax salary, any other income you expect,
        your expense budget, and your savings target. Use **{currency_name}** for every
        amount. These are your own estimates, not imported account data.

        **Log expenses** in the Expense tracker tab. Add each purchase or bill with its
        amount, category, and date. Only expenses dated in **{month_label}** count in
        this month's overview. Income is entered in your monthly plan, not as an expense.

        **The overview uses these formulas:**
        - **Monthly income** = take-home salary + other monthly income.
        - **Spent this month** = sum of logged expenses dated in {month_label}.
        - **Budget remaining** = monthly spending limit − spent this month.
          A negative result means spending is over budget.
        - **Estimated savings** = monthly income − spent this month.
          This is only an estimate based on expenses you logged; unrecorded bills or
          other income are not included.
        - **Savings goal progress** = estimated savings ÷ savings goal, capped at 100%.
          If estimated savings are negative, progress is 0%.
        - **Spending by category** groups this month's logged expenses by the category
          you selected.
        """
    )

st.subheader(f"2. Your monthly snapshot · {month_label}")
metric_columns = st.columns(4)
metric_columns[0].metric(
    "Planned income",
    f"{currency_symbol}{monthly_income:,.2f}",
    help="Take-home salary plus other monthly income entered in your plan.",
)
metric_columns[1].metric(
    "Expenses logged",
    f"{currency_symbol}{monthly_spending:,.2f}",
    help=f"Sum of expenses you entered with a date in {month_label}.",
)
metric_columns[2].metric(
    "Spending limit left",
    f"{currency_symbol}{remaining_budget:,.2f}",
    delta="Over budget" if remaining_budget < 0 else None,
    delta_color="inverse",
    help="Your monthly spending limit minus this month's logged expenses.",
)
metric_columns[3].metric(
    "Estimated amount left",
    f"{currency_symbol}{estimated_savings:,.2f}",
    help="Planned income minus expenses logged so far. This is an estimate, not a bank balance.",
)

overview, transactions_tab, assistant_tab = st.tabs(
    ["Monthly overview", "Expense tracker", "Finance assistant"]
)

with overview:
    st.subheader("3. Understand your spending")
    chart_column, goal_column = st.columns([1.5, 1])
    with chart_column:
        st.subheader("Spending by category")
        st.caption(
            f"Total of expenses dated in {month_label}, grouped by the category "
            "you chose when entering each expense."
        )
        if month_transactions:
            category_totals = (
                pd.DataFrame(month_transactions)
                .groupby("category")["amount"]
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(category_totals, horizontal=True, color="#18745a")
        else:
            st.info("Add a transaction to see where your money is going.")
    with goal_column:
        st.subheader("Savings goal")
        if savings_goal > 0:
            st.progress(savings_progress)
            st.caption(
                f"{currency_symbol}{max(estimated_savings, 0):,.2f} of "
                f"{currency_symbol}{savings_goal:,.2f} estimated"
            )
        else:
            st.caption("Set a monthly savings target in your plan above to track progress.")
        if monthly_budget > 0:
            budget_used = monthly_spending / monthly_budget
            if budget_used > 1:
                st.warning(
                    f"You are {currency_symbol}{abs(remaining_budget):,.2f} over your monthly budget."
                )
            else:
                st.caption(f"{budget_used:.0%} of your monthly budget used.")
        else:
            st.caption("Add a monthly spending limit in your plan above to see a budget check.")

with transactions_tab:
    st.subheader("Log a purchase or bill")
    st.caption(
        "Record each expense once. Use the selected currency. It counts in this month's "
        "totals only when its date is in "
        f"{month_label}."
    )
    with st.form("transaction_form", clear_on_submit=True):
        input_columns = st.columns([1, 1])
        transaction_description = input_columns[0].text_input(
            "Description",
            placeholder="e.g. Weekly groceries",
            help="Add a short name so you can recognize the transaction.",
        )
        transaction_amount = input_columns[1].number_input(
            f"Amount ({currency_symbol})",
            min_value=0.0,
            value=0.0,
            step=100.0,
            help="Enter the amount you paid, in the selected currency.",
        )
        detail_columns = st.columns([1, 1])
        transaction_category = detail_columns[0].selectbox(
            "Expense category",
            CATEGORIES,
            help="Choose the category that best matches this purchase or bill.",
        )
        transaction_date = detail_columns[1].date_input(
            "Date paid",
            value=date.today(),
            help="The date determines which month's totals include this expense.",
        )
        add_transaction = st.form_submit_button("＋  Add expense", type="primary")
    if add_transaction:
        if not transaction_description.strip():
            st.error("Add a description so you can identify this expense.")
        elif transaction_amount <= 0:
            st.error("Enter an amount greater than zero.")
        else:
            st.session_state.transactions.append(
                {
                    "date": transaction_date.isoformat(),
                    "description": transaction_description.strip(),
                    "category": transaction_category,
                    "amount": float(transaction_amount),
                }
            )
            st.rerun()

    st.subheader("Expense history")
    if st.session_state.transactions:
        transaction_frame = pd.DataFrame(st.session_state.transactions)
        transaction_frame = transaction_frame.rename(
            columns={
                "date": "Date",
                "description": "Description",
                "category": "Category",
                "amount": "Amount",
            }
        )
        transaction_frame["Amount"] = transaction_frame["Amount"].map(
            lambda amount: f"{currency_symbol}{amount:,.2f}"
        )
        st.dataframe(
            transaction_frame.sort_values("Date", ascending=False),
            hide_index=True,
            width="stretch",
        )
        if st.button("Clear all expenses"):
            st.session_state.transactions = []
            st.rerun()
    else:
        st.info("Your expense list is empty. Add an expense above to get started.")

with assistant_tab:
    st.subheader("Ask PocketWise")
    st.caption(
        "Get help with budgeting, saving habits, debt concepts, or understanding your spending."
    )
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.text_area(
        "Your finance question",
        key="question_input",
        placeholder="How can I adjust my budget to save more each month?",
        height=100,
    )
    cleaned_question = question.strip()
    if st.button("Ask PocketWise", type="primary"):
        if not cleaned_question:
            st.error("Enter a question before sending.")
        elif len(cleaned_question) > 1000:
            st.error("Keep your question to 1,000 characters or fewer.")
        elif not any(character.isalnum() for character in cleaned_question):
            st.error("Your question must include at least one letter or number.")
        elif not api_key:
            st.error(
                f"Gemini API key not found. Add `GEMINI_API_KEY=your_key` to "
                f"`{ENV_PATH.name}` and restart the app."
            )
        else:
            category_totals = (
                pd.DataFrame(month_transactions).groupby("category")["amount"].sum()
                if month_transactions
                else pd.Series(dtype=float)
            )
            category_summary = ", ".join(
                f"{category} {amount:.2f}"
                for category, amount in category_totals.items()
            ) or "none recorded"
            financial_snapshot = (
                f"Currency: {currency_name}. Monthly take-home salary: {monthly_salary:.2f}. "
                f"Other monthly income: {other_income:.2f}. Total planned monthly income: "
                f"{monthly_income:.2f}. Monthly spending budget: {monthly_budget:.2f}. "
                f"Monthly savings goal: {savings_goal:.2f}. "
                f"Expenses recorded this month: {monthly_spending:.2f}. "
                f"Estimated monthly savings from the entered figures: {estimated_savings:.2f}. "
                f"Expenses by category: {category_summary}."
            )
            finance_prompt = (
                "You are PocketWise, a helpful personal finance education and budgeting assistant. "
                "Be supportive, practical, clear, and non-judgmental. Use the user's provided "
                "financial snapshot when relevant, and distinguish estimates from verified facts. "
                "Ask a brief clarifying question if important details are missing. Never claim to "
                "be a licensed financial, tax, or legal professional; do not promise returns or "
                "give individualized buy/sell investment instructions. For complex tax, legal, "
                "debt, or investment decisions, explain general considerations and suggest a "
                "qualified professional. Do not ask for or repeat passwords, PINs, full card "
                "numbers, bank account numbers, or other authentication secrets. You cannot access "
                "accounts or move money. Do not invent rates, laws, or account details. "
                f"\n\nUser's current financial snapshot:\n{financial_snapshot}"
            )
            conversation = [
                *st.session_state.messages,
                {"role": "user", "content": cleaned_question},
            ]
            try:
                with st.spinner("Thinking through your question..."):
                    response = requests.post(
                        interactions_url,
                        headers={"x-goog-api-key": api_key},
                        json={
                            "model": model,
                            "input": cleaned_question,
                            "system_instruction": finance_prompt,
                            "previous_interaction_id": st.session_state.interaction_id,
                            "generation_config": {"max_output_tokens": 1024},
                        },
                        timeout=(10, 60),
                    )
                    response.raise_for_status()
                    interaction = response.json()
                answer = "\n".join(
                    part["text"]
                    for step in interaction.get("steps", [])
                    if step.get("type") == "model_output"
                    for part in step.get("content", [])
                    if isinstance(part.get("text"), str)
                ).strip()
                if not answer:
                    st.error("PocketWise returned an empty response. Please try again.")
                else:
                    st.session_state.interaction_id = interaction.get("id")
                    st.session_state.messages = [
                        *conversation,
                        {"role": "assistant", "content": answer},
                    ]
                    st.rerun()
            except requests.exceptions.JSONDecodeError:
                st.error("Gemini returned a response that could not be read. Please try again.")
            except requests.Timeout:
                st.error("Gemini took too long to respond. Please try again.")
            except requests.HTTPError as error:
                status = error.response.status_code if error.response is not None else "unknown"
                details = error.response.text[:500] if error.response is not None else str(error)
                st.error(f"Gemini returned HTTP {status}: {details}")
            except requests.RequestException as error:
                st.error(f"Could not connect to Gemini: {error}")

    if st.button("Clear assistant conversation"):
        st.session_state.messages = []
        st.session_state.interaction_id = None
        st.rerun()
