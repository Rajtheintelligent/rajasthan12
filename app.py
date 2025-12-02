import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIG ---
ROSTER_SHEET_NAME = "Roster"
ATTENDANCE_LOG_SHEET_NAME = "Form Responses 1"

ROSTER_ID_COL = "Student ID"
LOG_ID_COL = "ID"
TIMESTAMP_COL = "Timestamp"
STATUS_COL = "Attendance Status"

# --- Page Layout ---
st.set_page_config(
    page_title="Real-Time Attendance Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🚌 Live Trip Attendance Tracker")

# --- QR Scanner Button ---
st.markdown("### 📷 Scan Attendance")
st.markdown(
    """
    <a href="https://rajasthan11.vercel.app" target="_blank">
        <button style="
            background-color:#4CAF50; 
            color:white; 
            padding: 10px 20px; 
            border:none; 
            border-radius:8px;
            cursor:pointer;
            font-size:16px;">
            Open QR Scanner
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# --- Data Loading Function ---
@st.cache_data(ttl=10)
def load_and_process_data():
    try:
        conn = st.connection("gcp_sheets", type=GSheetsConnection)

        # Roster
        df_roster = conn.read(worksheet=ROSTER_SHEET_NAME, ttl=5).dropna(subset=[ROSTER_ID_COL])
        df_roster[ROSTER_ID_COL] = df_roster[ROSTER_ID_COL].astype(str)
        df_roster = df_roster.set_index(ROSTER_ID_COL)

        # Log
        df_log = conn.read(worksheet=ATTENDANCE_LOG_SHEET_NAME, ttl=5).dropna(subset=[LOG_ID_COL])
        df_log[LOG_ID_COL] = df_log[LOG_ID_COL].astype(str)

        present_ids = set(df_log[LOG_ID_COL].unique())

        df_roster[STATUS_COL] = df_roster.index.to_series().apply(
            lambda sid: "PRESENT" if sid in present_ids else "ABSENT"
        )

        # Last scan time
        try:
            df_log[TIMESTAMP_COL] = pd.to_datetime(df_log[TIMESTAMP_COL], errors='coerce')
            last_update = df_log[TIMESTAMP_COL].max()
            last_update = (
                last_update.strftime("%Y-%m-%d %I:%M:%S %p")
                if not pd.isna(last_update)
                else "No scans yet"
            )
        except:
            last_update = "Error reading time"

        return df_roster, last_update, present_ids

    except Exception as e:
        st.error("Error loading Google Sheet. Check Sheet tab names and columns.")
        st.exception(e)
        return pd.DataFrame(), "Failed", set()

# --- Load Data ---
df_attendance, last_update, present_ids = load_and_process_data()

# Manual refresh button
if st.button("🔄 Manual Refresh Data"):
    st.cache_data.clear()
    st.success("Refreshing now...")

st.markdown("---")

# --- Display Data ---
if not df_attendance.empty:

    total = len(df_attendance)
    present = len(present_ids)
    absent = total - present

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", total)
    col2.metric("✅ PRESENT", present)
    col3.metric("❌ ABSENT", absent)
    col4.metric("Last Scan Time", last_update)

    st.markdown("---")

    # Tabs
    tab1, tab2 = st.tabs([
        f"✅ PRESENT ({present})",
        f"❌ ABSENT ({absent})"
    ])

    def style_df(df):
        return df.style.applymap(
            lambda x: (
                'background-color: #d1fae5; color:#065f46; font-weight:bold;'
                if x == 'PRESENT'
                else 'background-color: #fee2e2; color:#991b1b;'
            ),
            subset=[STATUS_COL]
        )

    # PRESENT TAB
    with tab1:
        df_p = df_attendance[df_attendance[STATUS_COL] == "PRESENT"]
        st.dataframe(
            style_df(df_p.reset_index()),
            use_container_width=True,
            hide_index=True
        )

    # ABSENT TAB
    with tab2:
        df_a = df_attendance[df_attendance[STATUS_COL] == "ABSENT"]
        st.dataframe(
            style_df(df_a.reset_index()),
            use_container_width=True,
            hide_index=True
        )

else:
    st.warning("Roster not found or could not load.")
