import pandas as pd
import numpy as np

def clean_for_gsheets(df):
    # Replace NaN/None with empty string
    df = df.replace({np.nan: "", None: ""})
    # Convert everything to string to avoid float NaN issues
    df = df.astype(str)
    return df

# Example inside your Streamlit app
uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])

if uploaded_file:
    # Read all sheets as strings
    xls = pd.ExcelFile(uploaded_file)
    cleaned_sheets = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, dtype=str)
        df = df.fillna("")  # Ensure no NaN
        cleaned_sheets[sheet] = df

    # Example: uploading first sheet to Google Sheets
    import gspread
    from google.oauth2.service_account import Credentials

    # Authenticate
    creds = Credentials.from_service_account_file("service_account.json", scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)

    spreadsheet = client.open("My Google Sheet")
    worksheet = spreadsheet.sheet1

    # Update with cleaned data
    worksheet.update([cleaned_sheets[xls.sheet_names[0]].columns.values.tolist()] +
                     cleaned_sheets[xls.sheet_names[0]].values.tolist())
