import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Page Configuration for mobile viewports
st.set_page_config(page_title="FINFLOW", page_icon="⚡", layout="centered")

# 2. Premium Dark UI Style Injection (Forces the dark executive dashboard look on phones)
st.markdown("""
    <style>
    /* Dark Theme Backgrounds */
    .stApp { background-color: #0B0F19 !important; color: #F8FAFC !important; }
    header, footer { visibility: hidden !important; }
    
    /* Global Typography */
    h1, h2, h3, p, span, label { color: #FFFFFF !important; font-family: 'Inter', sans-serif; }
    h1 { font-size: 28px !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    .stCaption { color: #94A3B8 !important; font-size: 14px !important; }
    
    /* Neon Cards & Gauges styling wrapper */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #161D2F, #111625) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
    }
    div[data-testid="stMetricLabel"] > div {
        color: #94A3B8 !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #FFFFFF !important;
        font-size: 26px !important;
        font-weight: 700 !important;
    }
    
    /* Custom Neon Glowing Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #06B6D4, #3B82F6) !important;
        border-radius: 10px !important;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.5) !important;
    }
    
    /* Streamlit native Table overrides for dark mode readability */
    div[data-testid="stTable"] table {
        background-color: #111625 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        border: none !important;
    }
    div[data-testid="stTable"] th {
        background-color: #161D2F !important;
        color: #06B6D4 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stTable"] td {
        color: #E2E8F0 !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Custom Notification Blocks */
    .custom-pending-card {
        background: rgba(239, 68, 68, 0.1) !important;
        border-left: 4px solid #EF4444 !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
        margin-bottom: 10px !important;
    }
    .custom-safe-card {
        background: rgba(16, 185, 129, 0.1) !important;
        border-left: 4px solid #10B981 !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
        margin-bottom: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. DB Connector Initializer
@st.cache_resource
def init_connection():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = init_connection()
except Exception as e:
    st.error("Connection failed.")
    st.stop()

# 4. Global Variables
current_month = datetime.now().strftime("%Y-%m")

# UI Headers
st.title("⚡ FINFLOW CONTROL CENTER")
st.caption(f"Active Monitoring Accounting Window: **{datetime.now().strftime('%B %Y')}**")
st.markdown("<br>", unsafe_allow_html=True)

# 5. Core Data Load Shifting
@st.cache_data(ttl=3)
def fetch_financial_matrices(target_month):
    master_data = supabase.table("recurring_debits").select("*").execute().data
    logs_data = supabase.table("debit_logs").select("*").eq("billing_month", target_month).execute().data
    return pd.DataFrame(master_data), pd.DataFrame(logs_data)

df_master, df_logs = fetch_financial_matrices(current_month)

if df_master.empty:
    st.warning("Master parameters empty.")
    st.stop()

if df_logs.empty:
    df_logs = pd.DataFrame(columns=['title', 'amount', 'bank_account', 'paid_at', 'billing_month'])

# Data Operations Normalization
df_master['clean_title'] = df_master['title'].apply(lambda x: x.split('|')[0].strip())
paid_titles_list = df_logs['title'].str.strip().tolist() if not df_logs.empty else []

df_pending = df_master[~df_master['clean_title'].isin(paid_titles_list)].copy()

total_outflow = df_master['amount'].sum()
total_actual_paid = df_logs['amount'].sum() if not df_logs.empty else 0
total_remaining_pending = max(0, total_outflow - total_actual_paid)
completion_rate = min(100, int((total_actual_paid / total_outflow) * 100)) if total_outflow > 0 else 0

# 6. Core KPIs (Stacked cleanly for mobile screens)
m1, m2, m3 = st.columns(3)
m1.metric("TOTAL MONTHLY COMMITMENT", f"₹{total_outflow:,}")
m2.metric("CLEARED LOGS (PAID) ✅", f"₹{total_actual_paid:,}", f"{completion_rate}% done")
m3.metric("AWAITING ALLOCATION 🚨", f"₹{total_remaining_pending:,}")

# Progress Metrics Track Bar
st.markdown(f"<p style='font-size:13px; font-weight:600; color:#94A3B8;'>MONTHLY CAPITAL FUNDING RUNWAY PROGRESS: {completion_rate}% DONE</p>", unsafe_allow_html=True)
st.progress(completion_rate / 100)
st.markdown("<br>", unsafe_allow_html=True)

# 7. Charting Grid
st.markdown("### 📊 Capital Structure Diversification")
category_mix = df_master.groupby('category')['amount'].sum().reset_index()
# Streamlit native chart styled with a gradient look inside the CSS theme
st.bar_chart(data=category_mix, x='category', y='amount', color="#06B6D4", use_container_width=True)

# 8. Bank Account Balance Matrices
st.markdown("### 🏦 Liquidity Requirements Matrix")
bank_ledger = []
for bank, group in df_master.groupby('bank_account'):
    target = group['amount'].sum()
    settled = df_logs[df_logs['bank_account'].str.lower() == bank.lower()]['amount'].sum() if not df_logs.empty else 0
    needed = max(0, target - settled)
    bank_ledger.append({
        "Clearing Node": bank,
        "Target Load": f"₹{target:,}",
        "Settled Funds": f"₹{settled:,}",
        "Required Balance": f"₹{needed:,}"
    })
st.table(pd.DataFrame(bank_ledger))

# 9. Time-Series Queues (Pending vs Completed)
st.markdown("### ⏳ Pending Time-Series Queue")
if df_pending.empty:
    st.markdown("<div class='custom-safe-card'>🎉 All banking nodes are completely safe and funded for this month!</div>", unsafe_allow_html=True)
else:
    df_pending_sorted = df_pending.sort_values(by='due_day')
    current_day = datetime.now().day
    for _, row in df_pending_sorted.iterrows():
        is_critical = 0 <= (row['due_day'] - current_day) <= 3
        card_class = "custom-pending-card" if is_critical else "custom-safe-card"
        alert_prefix = "⚠️ CRITICAL WINDOW | " if is_critical else "🕒 PENDING | "
        
        st.markdown(f"""
            <div class="{card_class}">
                <strong>{alert_prefix}Day {row['due_day']} Due</strong><br>
                {row['clean_title']} — <strong>₹{row['amount']:,}</strong> via {row['bank_account']}
            </div>
        """, unsafe_allow_html=True)

# 10. Audit Ledger Logs
st.markdown("### 📜 System Transaction Logs")
if df_logs.empty:
    st.caption("No historical records logged for this cycle.")
else:
    for _, row in df_logs.sort_values(by='paid_at', ascending=False).iterrows():
        st.markdown(f"<p style='font-size:13px; color:#E2E8F0; border-bottom:1px solid rgba(255,255,255,0.02); padding-bottom:4px;'>✔️ {row['paid_at'][:16]} — {row['title']} (₹{row['amount']:,}) parsed to {row['bank_account']}</p>", unsafe_allow_html=True)
