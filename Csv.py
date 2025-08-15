import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Excel to Google Sheets", layout="wide")
st.title("📄 Excel to Google Sheets Uploader (No NaN Errors)")

# ---- Function to clean DataFrame ----
def clean_for_gsheets(df):
    """Replace NaN/None with empty string & ensure all data is string type."""
    df = df.replace({np.nan: "", None: ""})
    df = df.astype(str)
    return df

# ---- File uploader ----
uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])

if uploaded_file:
    try:
        # Read Excel file
        xls = pd.ExcelFile(uploaded_file)
        st.success(f"✅ Found {len(xls.sheet_names)} sheets: {', '.join(xls.sheet_names)}")

        cleaned_sheets = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, dtype=str)
            df = df.fillna("")  # Remove NaN
            df = clean_for_gsheets(df)
            cleaned_sheets[sheet] = df

        st.info("📊 Preview of first sheet:")
        st.dataframe(cleaned_sheets[xls.sheet_names[0]])

        # ---- Google Sheets Upload ----
        st.subheader("🔑 Google Sheets Authentication")
        service_account_file = st.file_uploader("Upload Google Service Account JSON", type=["json"])
        
        if service_account_file is not None:
            # Authenticate with Google Sheets
            creds = Credentials.from_service_account_info(
                pd.read_json(service_account_file).to_dict(),
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            client = gspread.authorize(creds)

            # Select Spreadsheet
            sheet_name = st.text_input("Google Spreadsheet Name:", value="My Google Sheet")
            if st.button("🚀 Upload to Google Sheets"):
                try:
                    spreadsheet = client.open(sheet_name)
                    worksheet = spreadsheet.sheet1

                    # Upload first sheet only (could be extended to all)
                    worksheet.update(
                        [cleaned_sheets[xls.sheet_names[0]].columns.values.tolist()] +
                        cleaned_sheets[xls.sheet_names[0]].values.tolist()
                    )
                    st.success("✅ Data uploaded successfully without NaN errors!")
                except Exception as e:
                    st.error(f"❌ Failed to upload: {e}")

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
else:
    st.info("📥 Please upload an Excel file to begin.")
