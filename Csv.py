import streamlit as st
import pandas as pd
import numpy as np
import json
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Excel to Google Sheets", layout="wide")
st.title("📄 Excel to Google Sheets Uploader (Full Workbook)")

# ---- Function to clean DataFrame ----
def clean_for_gsheets(df):
    """Replace NaN/None with empty string & ensure all data is string type."""
    df = df.replace({np.nan: "", None: ""})
    df = df.astype(str)
    return df

# ---- File uploader ----
uploaded_file = st.file_uploader("Upload Excel Workbook", type=["xlsx"])

if uploaded_file:
    try:
        # Read Excel file
        xls = pd.ExcelFile(uploaded_file)
        st.success(f"✅ Found {len(xls.sheet_names)} sheets: {', '.join(xls.sheet_names)}")

        # Preview first sheet
        first_df = pd.read_excel(xls, sheet_name=xls.sheet_names[0], dtype=str).fillna("")
        st.info("📊 Preview of first sheet:")
        st.dataframe(first_df)

        # ---- Google Sheets Auth ----
        st.subheader("🔑 Google Sheets Authentication")
        service_account_file = st.file_uploader("Upload Google Service Account JSON", type=["json"])

        if service_account_file:
            creds_dict = json.load(service_account_file)
            creds = Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"  # Needed to create new sheets
                ]
            )
            client = gspread.authorize(creds)

            # Spreadsheet name input
            sheet_name = st.text_input("Google Spreadsheet Name:", value="My Uploaded Workbook")

            if st.button("🚀 Upload Workbook to Google Sheets"):
                try:
                    # Open or create spreadsheet
                    try:
                        spreadsheet = client.open(sheet_name)
                        st.info("Opened existing Google Sheet.")
                    except gspread.SpreadsheetNotFound:
                        spreadsheet = client.create(sheet_name)
                        st.info("Created new Google Sheet.")

                    # Auto-share with entremotivator@gmail.com
                    spreadsheet.share('entremotivator@gmail.com', perm_type='user', role='writer')
                    st.success("📨 Shared spreadsheet with entremotivator@gmail.com")

                    # Loop through all Excel sheets
                    for sheet in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name=sheet, dtype=str).fillna("")
                        df = clean_for_gsheets(df)

                        # Create or overwrite worksheet
                        try:
                            worksheet = spreadsheet.worksheet(sheet)
                            worksheet.clear()
                            st.info(f"Cleared existing sheet: {sheet}")
                        except gspread.WorksheetNotFound:
                            worksheet = spreadsheet.add_worksheet(
                                title=sheet,
                                rows=str(len(df)+10),
                                cols=str(len(df.columns)+5)
                            )
                            st.info(f"Created new sheet: {sheet}")

                        # Update worksheet with new data
                        worksheet.update([df.columns.values.tolist()] + df.values.tolist())

                    # Display spreadsheet link
                    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
                    st.success(f"✅ Entire workbook uploaded successfully! [Open Spreadsheet]({spreadsheet_url})")
                    
                except Exception as e:
                    st.error(f"❌ Failed to upload: {e}")

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
else:
    st.info("📥 Please upload an Excel file to begin.")
