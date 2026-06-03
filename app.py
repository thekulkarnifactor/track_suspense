import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Finances", page_icon="💰", layout="centered")

# 1. Initialize Supabase Connection using Streamlit Secrets
@st.cache_resource
def init_connection():
    from supabase import create_client, Client
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("Could not connect to database. Check your Secrets configuration.")
    st.stop()

st.title("📊 Auto-Debit Control Center")

# Get current month parameters
current_month = datetime.now().strftime("%Y-%m")
st.caption(f"Tracking Window: **{datetime.now().strftime('%B %Y')}**")

# 2. Fetch Data from Supabase
@st.cache_data(ttl=10) # Cache data for 10 seconds to keep app snappy
def load_data():
    master = supabase.table("recurring_debits").select("*").execute().data
    logs = supabase.table("debit_logs").filter("billing_month", "eq", current_month).execute().data
    return pd.DataFrame(master), pd.DataFrame(logs)

df_master, df_logs = load_data()

# Handle empty state dataframes gracefully
if df_master.empty:
    st.warning("No recurring rules found. Seed your master database table first.")
    st.stop()

if df_logs.empty:
    df_logs = pd.DataFrame(columns=['title', 'amount', 'bank_account', 'paid_at'])

# 3. Core Data Processing Logic
paid_titles = df_logs['title'].tolist() if not df_logs.empty else []

# Filter master list into Paid vs Pending categories
df_pending = df_master[~df_master['title'].isin(paid_titles)].copy()
df_paid_current = df_master[df_master['title'].isin(paid_titles)].copy()

total_outflow = df_master['amount'].sum()
total_paid = df_logs['amount'].sum() if not df_logs.empty else 0
total_pending = total_outflow - total_paid

# 4. KPI Summary Panel Block
col1, col2, col3 = st.columns(3)
col1.metric("Total Bill Commit", f"₹{total_outflow:,}")
col2.metric("Funded (Paid) ✅", f"₹{total_paid:,}", delta=f"{int((total_paid/total_outflow)*100)}% done" if total_outflow > 0 else None)
col3.metric("Awaiting Cash 🚨", f"₹{total_pending:,}", delta=f"-₹{total_pending:,}" if total_pending > 0 else None, delta_color="inverse")

st.divider()

# 5. Bank Account Cash Allocation Breakdown
st.subheader("🏦 Necessary Cash Allocation by Bank")
bank_summary = []

# Group and calculate targets per bank account
for bank, group in df_master.groupby('bank_account'):
    bank_master_total = group['amount'].sum()
    bank_paid = df_logs[df_logs['bank_account'] == bank]['amount'].sum() if not df_logs.empty else 0
    bank_pending = bank_master_total - bank_paid
    bank_summary.append({
        "Bank Account": bank,
        "Total Target": f"₹{bank_master_total:,}",
        "Cleared (Paid)": f"₹{bank_paid:,}",
        "Required Balance (Pending)": f"₹{bank_pending:,}"
    })

st.table(pd.DataFrame(bank_summary))

# 6. Immediate Action Items
st.subheader("🚨 Action Items Needed Soon")
if df_pending.empty:
    st.success("All bank accounts are completely safe and funded for this month!")
else:
    # Sort pending items chronologically by due day
    df_pending_sorted = df_pending.sort_values(by='due_day')
    for _, row in df_pending_sorted.iterrows():
        # High alert if due day is within next 3 days
        current_day = datetime.now().day
        is_urgent = 0 <= (row['due_day'] - current_day) <= 3
        
        item_text = f"**Due on Day {row['due_day']}**: {row['title']} | **₹{row['amount']:,}** via {row['bank_account']}"
        if is_urgent:
            st.error(f"⚠️ {item_text} (CRITICAL WINDOW)")
        else:
            st.info(item_text)

# 7. Completed Logs Ledger
st.subheader("📜 Historical Monthly Clearance Ledger")
if df_logs.empty:
    st.caption("No payments logged yet for this billing cycle.")
else:
    for _, row in df_logs.sort_values(by='paid_at', ascending=False).iterrows():
        st.text(f"✔️ {row['paid_at'][:16]} — {row['title']} (₹{row['amount']:,}) from {row['bank_account']} recorded.")