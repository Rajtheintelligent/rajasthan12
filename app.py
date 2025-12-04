import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIG ---
ROSTER_SHEET_NAME = "Roster"
ATTENDANCE_LOG_SHEET_NAME = "FormResponses"

ROSTER_ID_COL = "ID"
LOG_ID_COL = "ID"
TIMESTAMP_COL = "Timestamp"
STATUS_COL = "Attendance Status"

st.set_page_config(
    page_title="Real-Time Attendance Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---- GOOGLE AUTH (Vercel Compatible) ----
def get_gsheet_client():
    """Authenticate using the service account stored in secrets.toml"""
    creds_dict = st.secrets["gcp_sheets"]

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client

# ---- DATA LOADING ----
@st.cache_data(ttl=10)
def load_data():
    try:
        client = get_gsheet_client()

        # Open spreadsheet
        spreadsheet_id = st.secrets["gcp_sheets"]["spreadsheet_id"]
        sheet = client.open_by_key(spreadsheet_id)

        # Load roster sheet
        roster_ws = sheet.worksheet(ROSTER_SHEET_NAME)
        df_roster = pd.DataFrame(roster_ws.get_all_records())
        df_roster[ROSTER_ID_COL] = df_roster[ROSTER_ID_COL].astype(str)
        df_roster = df_roster.set_index(ROSTER_ID_COL)

        # Load attendance logs (only Timestamp + ID)
        log_ws = sheet.worksheet(ATTENDANCE_LOG_SHEET_NAME)
        df_log = pd.DataFrame(log_ws.get_all_records())

        # Convert ID and Timestamp
        if not df_log.empty:
            df_log[LOG_ID_COL] = df_log[LOG_ID_COL].astype(str)
            df_log[TIMESTAMP_COL] = pd.to_datetime(df_log[TIMESTAMP_COL], errors="coerce")

        return df_roster, df_log

    except Exception as e:
        st.error("Error loading Google Sheet data.")
        st.exception(e)
        return pd.DataFrame(), pd.DataFrame()

# ---- UI ----

st.title("🚌 Live Trip Attendance Tracker")

# QR Scanner Button
st.markdown("### Scan Attendance")
st.markdown(
    """
    <a href="https://rajasthan11.vercel.app" target="_blank">
        <button style="padding:10px 20px; font-size:18px; background:#2563eb; color:white; border:none; border-radius:8px;">
            📷 Open QR Scanner
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# Load Data
df_roster, df_log = load_data()

# Manual Refresh Button
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

if df_roster.empty:
    st.warning("No roster data found. Check your Google Sheet.")
    st.stop()

# ---- NEW FEATURE: Teacher selects cutoff ----
st.subheader("📅 Select Cutoff Date & Time")
cutoff_date = st.date_input("Choose Date")
cutoff_time = st.time_input("Choose Time")

cutoff_datetime = datetime.combine(cutoff_date, cutoff_time)

st.info(f"Only QR scans AFTER **{cutoff_datetime}** will be marked PRESENT.")

# ---- FILTER BASED ON CUTOFF ----
if not df_log.empty:
    df_filtered = df_log[df_log[TIMESTAMP_COL] >= cutoff_datetime]
    present_ids = set(df_filtered[LOG_ID_COL].unique())
    last_scan = df_log[TIMESTAMP_COL].max()
else:
    present_ids = set()
    last_scan = "N/A"

# Assign status
df_roster[STATUS_COL] = df_roster.index.map(
    lambda x: "PRESENT" if x in present_ids else "ABSENT"
)

# ---- METRICS ----
total = len(df_roster)
present = len(present_ids)
absent = total - present

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students", total)
col2.metric("Present", present)
col3.metric("Absent", absent)
col4.metric("Last Scan", last_scan if isinstance(last_scan, str) else last_scan.strftime("%Y-%m-%d %I:%M:%S %p"))

st.markdown("---")

# ---- TABS ----
tab1, tab2 = st.tabs([f"✅ Present ({present})", f"❌ Absent ({absent})"])

def style_df(df):
    return df.style.applymap(
        lambda x: "background-color:#d1fae5; color:#065f46; font-weight:bold;"
        if x == "PRESENT"
        else "background-color:#fee2e2; color:#991b1b;",
        subset=[STATUS_COL]
    )

with tab1:
    df_present = df_roster[df_roster[STATUS_COL] == "PRESENT"]
    st.dataframe(
        style_df(df_present.reset_index()),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    df_absent = df_roster[df_roster[STATUS_COL] == "ABSENT"]
    st.dataframe(
        style_df(df_absent.reset_index()),
        use_container_width=True,
        hide_index=True
    )
