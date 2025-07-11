import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import tempfile
import os

st.set_page_config(page_title="CSV to Google Sheets", layout="wide")
st.title("📤 Upload Multiple CSVs to Google Sheets")

# --- Sidebar for Google Credentials ---
st.sidebar.header("🔐 Google Sheets Credentials")
cred_file = st.sidebar.file_uploader("Upload your `credentials.json`", type="json")

# Function to get authorized Google Sheets client
@st.cache_resource(show_spinner=False)
def get_gsheet_client(cred_path):
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(cred_path, scopes=scopes)
    return gspread.authorize(creds)

# If credentials uploaded
if cred_file is not None:
    # Save credentials to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(cred_file.read())
        cred_path = tmp.name

    client = get_gsheet_client(cred_path)

    # Upload CSV files
    uploaded_files = st.file_uploader("📎 Upload one or more CSV files", type=["csv"], accept_multiple_files=True)

    if uploaded_files:
        sheet_names = {}
        st.markdown("### 📝 Name your Google Sheets")

        for i, uploaded_file in enumerate(uploaded_files):
            default_name = uploaded_file.name.replace(".csv", "").replace(" ", "_")
            sheet_input = st.text_input(f"Name for file {i+1} ({uploaded_file.name}):", value=default_name)
            sheet_names[uploaded_file.name] = sheet_input

        if st.button("🚀 Send All to Google Sheets"):
            sheet_links = []

            for uploaded_file in uploaded_files:
                try:
                    df = pd.read_csv(uploaded_file)
                    sheet_name = sheet_names.get(uploaded_file.name, uploaded_file.name.replace(".csv", ""))

                    # Create a new sheet
                    sh = client.create(sheet_name)
                    worksheet = sh.get_worksheet(0)

                    # Upload data
                    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

                    # Shareable link
                    sheet_url = f"https://docs.google.com/spreadsheets/d/{sh.id}"
                    sheet_links.append((sheet_name, sheet_url))

                except Exception as e:
                    st.error(f"❌ Error with {uploaded_file.name}: {e}")

            if sheet_links:
                st.success("✅ Upload successful!")
                st.markdown("### 🔗 Your Google Sheet Links")
                for name, url in sheet_links:
                    st.markdown(f"- **{name}** → [Open Sheet]({url})")

    else:
        st.info("Upload at least one CSV file above to proceed.")

else:
    st.warning("⚠️ Please upload your Google credentials JSON file in the sidebar to continue.")
