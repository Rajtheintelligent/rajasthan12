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

        # Open spreadsheet using sheet ID (same block!)
        spreadsheet_id = st.secrets["gcp_sheets"]["spreadsheet_id"]
        sheet = client.open_by_key(spreadsheet_id)

        # Load roster sheet
        roster_ws = sheet.worksheet(ROSTER_SHEET_NAME)
        df_roster = pd.DataFrame(roster_ws.get_all_records())
        df_roster[ROSTER_ID_COL] = df_roster[ROSTER_ID_COL].astype(str)
        df_roster = df_roster.set_index(ROSTER_ID_COL)

        # Load attendance logs sheet
        log_ws = sheet.worksheet(ATTENDANCE_LOG_SHEET_NAME)
        df_log = pd.DataFrame(log_ws.get_all_records())
        df_log[LOG_ID_COL] = df_log[LOG_ID_COL].astype(str)

        # Present IDs
        present_ids = set(df_log[LOG_ID_COL].unique())

        # Status column
        df_roster[STATUS_COL] = df_roster.index.map(
            lambda x: "PRESENT" if x in present_ids else "ABSENT"
        )

        # Last timestamp
        df_log[TIMESTAMP_COL] = pd.to_datetime(
            df_log[TIMESTAMP_COL], errors="coerce"
        )
        last_time = df_log[TIMESTAMP_COL].max()
        last_time = (
            "N/A" if pd.isna(last_time)
            else last_time.strftime("%Y-%m-%d %I:%M:%S %p")
        )

        return df_roster, last_time, present_ids

    except Exception as e:
        st.error("Error loading Google Sheet data.")
        st.exception(e)
        return pd.DataFrame(), "N/A", set()

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
df_attendance, last_update, present_ids = load_data()

# Manual Refresh Button
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

if df_attendance.empty:
    st.warning("No roster data found. Check your Google Sheet.")
    st.stop()

# Metrics
total = len(df_attendance)
present = len(present_ids)
absent = total - present

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Students", total)
c2.metric("Present", present)
c3.metric("Absent", absent)
c4.metric("Last Scan", last_update)

st.markdown("---")

# Tabs for Present & Absent
tab1, tab2 = st.tabs([f"✅ Present ({present})", f"❌ Absent ({absent})"])

def style_df(df):
    return df.style.applymap(
        lambda x: "background-color:#d1fae5; color:#065f46; font-weight:bold;"
        if x == "PRESENT"
        else "background-color:#fee2e2; color:#991b1b;",
        subset=[STATUS_COL]
    )

with tab1:
    df_present = df_attendance[df_attendance[STATUS_COL] == "PRESENT"]
    st.dataframe(
        style_df(df_present.reset_index()),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    df_absent = df_attendance[df_attendance[STATUS_COL] == "ABSENT"]
    st.dataframe(
        style_df(df_absent.reset_index()),
        use_container_width=True,
        hide_index=True
    )
