import streamlit as st
import pandas as pd
from datetime import datetime

# Configure page layout to wide mode for a premium tech dashboard feel
st.set_page_config(page_title="FinFlow Dashboard", page_icon="💸", layout="wide")

# Custom CSS styling injection to clean up margins and enhance typography metrics
# Custom CSS styling injection to fix text visibility inside metric cards
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3 { font-weight: 700 !important; color: #1E293B; }
    
    /* Force high visibility for Streamlit Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #F8FAFC !important; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #E2E8F0 !important;
    }
    /* Force metric label (title) text color */
    div[data-testid="stMetricLabel"] > div {
        color: #475569 !important;
        font-weight: 600 !important;
    }
    /* Force metric value (big number) text color */
    div[data-testid="stMetricValue"] > div {
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 1. Initialize Supabase Connection
@st.cache_resource
def init_connection():
    from supabase import create_client, Client
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("Authentication Error. Check your GitHub deployment secrets configuration mapping.")
    st.stop()

# 2. Sidebar Navigation and Historical Month Selector Matrix
st.sidebar.title("🎯 Control Center Navigation")
st.sidebar.markdown("---")

# Dynamic generation of accessible historical billing target windows
available_months = ["2026-06", "2026-05", "2026-04", "2026-03", "2026-02", "2026-01"]
selected_month = st.sidebar.selectbox("📅 Select Billing Window Cycle", available_months, index=0)

# Display context parameters
parsed_date = datetime.strptime(selected_month, "%Y-%m")
st.title("💸 FinFlow Executive Control Center")
st.caption(f"Active Monitoring Accounting Window: **{parsed_date.strftime('%B %Y')}**")
st.markdown("---")

# 3. Fetch Real-time Database Records from Supabase Core Ledger Tables
@st.cache_data(ttl=5) # 5-second cash refresh loop keeps the mobile interaction responsive
def fetch_financial_state_matrices(target_month):
    master_data = supabase.table("recurring_debits").select("*").execute().data
    # FIX: Changed .filter("billing_month", "eq", target_month) to .select("*").eq()
    logs_data = supabase.table("debit_logs").select("*").eq("billing_month", target_month).execute().data
    return pd.DataFrame(master_data), pd.DataFrame(logs_data)

df_master, df_logs = fetch_financial_state_matrices(selected_month)

# Gracefully intercept initialization edge cases
if df_master.empty:
    st.warning("Database configuration discrepancy detected: Your `recurring_debits` master map is blank.")
    st.stop()

if df_logs.empty:
    df_logs = pd.DataFrame(columns=['title', 'amount', 'bank_account', 'paid_at', 'billing_month'])

# 4. Cash Aggregation Operations and Mathematical Formulations
# Clean and normalise strings for programmatic execution tracking
df_master['clean_title'] = df_master['title'].apply(lambda x: x.split('|')[0].strip())
paid_titles_list = df_logs['title'].str.strip().tolist() if not df_logs.empty else []

# Segment datasets into paid vs outstanding buckets
df_pending = df_master[~df_master['clean_title'].isin(paid_titles_list)].copy()
df_paid_current = df_master[df_master['clean_title'].isin(paid_titles_list)].copy()

# Compute high-level analytical performance summary indicators
total_outflow_target = df_master['amount'].sum()
total_actual_paid = df_logs['amount'].sum() if not df_logs.empty else 0
total_remaining_pending = max(0, total_outflow_target - total_actual_paid)
funding_completion_percentage = min(100, int((total_actual_paid / total_outflow_target) * 100)) if total_outflow_target > 0 else 0

# 5. Core UI Component Rendering Area
# Card metrics display block
m1, m2, m3 = st.columns(3)
m1.metric("Total Monthly Commitment", f"₹{total_outflow_target:,}")
m2.metric("Cleared Logs (Paid) ✅", f"₹{total_actual_paid:,}", f"{funding_completion_percentage}% of goal")
m3.metric("Awaiting Allocation 🚨", f"₹{total_remaining_pending:,}", delta=f"-₹{total_remaining_pending:,}" if total_remaining_pending > 0 else None, delta_color="inverse")

# Visual progress meter bar layout
st.markdown(f"**Monthly Capital Funding Runway Progress:** {funding_completion_percentage}%")
st.progress(funding_completion_percentage / 100)
st.markdown("---")

# 6. Advanced Charting Layout Workspace Blocks (Two-Column Presentation Grid)
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📊 Capital Structure Diversification")
    # Generate native Streamlit categorical allocation distribution metric graphs
    category_mix = df_master.groupby('category')['amount'].sum().reset_index()
    st.bar_chart(data=category_mix, x='category', y='amount', use_container_width=True)

with chart_col2:
    st.subheader("🏛️ Net Outflow Breakdown per Bank Entity")
    # Visualizing allocation loads across HDFC and Canara Bank
    bank_mix = df_master.groupby('bank_account')['amount'].sum().reset_index()
    st.bar_chart(data=bank_mix, x='bank_account', y='amount', color="#3B82F6", use_container_width=True)

st.markdown("---")

# 7. Cash Allocation Accounting Balance Table Block
st.subheader("🏦 Liquidity Requirements Matrix per Clearing Bank")
bank_allocation_ledger = []

for bank, group in df_master.groupby('bank_account'):
    theoretical_total_target = group['amount'].sum()
    actual_cleared_logs = df_logs[df_logs['bank_account'].str.lower() == bank.lower()]['amount'].sum() if not df_logs.empty else 0
    net_outstanding_balance_required = max(0, theoretical_total_target - actual_cleared_logs)
    
    bank_allocation_ledger.append({
        "Clearing Bank Node": bank,
        "Total Target Debt Load": f"₹{theoretical_total_target:,}",
        "Settled Funds": f"₹{actual_cleared_logs:,}",
        "Mandatory Liquidity Balance Needed": f"₹{net_outstanding_balance_required:,}"
    })

st.table(pd.DataFrame(bank_allocation_ledger))
st.markdown("---")

# 8. Time-Series Timeline Queue and Historical Logs Grid Blocks
queue_col, history_col = st.columns(2)

with queue_col:
    st.subheader("⏳ Pending Time-Series Clearance Queue")
    if df_pending.empty:
        st.success("Operational compliance complete: Liquidity safe across all banking nodes for this cycle!")
    else:
        df_pending_sorted = df_pending.sort_values(by='due_day')
        current_calendar_day = datetime.now().day
        
        for _, row in df_pending_sorted.iterrows():
            # Flag item with high alert styling if due date lands within an active 3-day buffer window
            is_critical = 0 <= (row['due_day'] - current_calendar_day) <= 3 and selected_month == datetime.now().strftime("%Y-%m")
            display_string = f"**Day {row['due_day']} due date**: {row['clean_title']} — **₹{row['amount']:,}** via {row['bank_account']}"
            
            if is_critical:
                st.error(f"⚠️ {display_string} [CRITICAL FUNDING WINDOW RUNNING SHORT]")
            else:
                st.info(display_string)

with history_col:
    st.subheader("📜 System Audit Transaction Logs Ledger")
    if df_logs.empty:
        st.caption("No historical transaction execution records tracked within this structural month parameter context.")
    else:
        df_logs_sorted = df_logs.sort_values(by='paid_at', ascending=False)
        for _, row in df_logs_sorted.iterrows():
            st.caption(f"✔️ **{row['paid_at'][:16]}** — Clr: {row['title']} | Amount: **₹{row['amount']:,}** out of {row['bank_account']}")
