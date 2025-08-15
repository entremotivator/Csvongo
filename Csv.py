import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import tempfile
import os
import json
from datetime import datetime
import time
import io
from openpyxl import load_workbook
import zipfile
from typing import Dict, List, Any, Optional, Tuple
import logging
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Excel/CSV to Google Sheets Pro", 
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .upload-section {
        background: linear-gradient(145deg, #f0f8ff, #e6f3ff);
        padding: 2rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #b3d9ff;
        color: #2c3e50;
    }
    
    .success-box {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border: 2px solid #28a745;
        color: #155724;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box_shadow: 0 4px 15px rgba(40, 167, 69, 0.2);
    }
    
    .error-box {
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        border: 2px solid #dc3545;
        color: #721c24;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(220, 53, 69, 0.2);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fff3cd, #ffeeba);
        border: 2px solid #ffc107;
        color: #856404;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.2);
    }
    
    .info-box {
        background: linear-gradient(135deg, #d1ecf1, #bee5eb);
        border: 2px solid #17a2b8;
        color: #0c5460;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(23, 162, 184, 0.2);
    }
    
    .feature-card {
        background: linear-gradient(145deg, #f0f8ff, #e6f3ff);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        margin: 1.5rem 0;
        border: 1px solid #e9ecef;
        transition: transform 0.3s ease;
        color: #2c3e50;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(0,0,0,0.15);
    }
    
    .metric-card {
        background: linear-gradient(145deg, #f0f8ff, #e1f4ff);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #e8eaed;
        color: #2c3e50;
    }
    
    .file-preview {
        background: #f0f8ff;
        border: 1px solid #b3d9ff;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
        color: #2c3e50;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-success { background-color: #28a745; }
    .status-error { background-color: #dc3545; }
    .status-warning { background-color: #ffc107; }
    .status-processing { background-color: #17a2b8; animation: pulse 1.5s infinite; }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .progress-container {
        background: #f0f8ff;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #b3d9ff;
        color: #2c3e50;
    }
    
    .sheet-link {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: linear-gradient(135deg, #007bff, #0056b3);
        color: white;
        text-decoration: none;
        border-radius: 8px;
        margin: 0.25rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
    }
    
    .sheet-link:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 123, 255, 0.4);
        text-decoration: none;
        color: white;
    }
    
    .sidebar-section {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #b3d9ff;
        color: #2c3e50;
    }
    
    .primary-button {
        background: linear-gradient(135deg, #007bff, #0056b3) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3) !important;
        transition: all 0.3s ease !important;
        min-height: 60px !important;
        margin: 20px 0 !important;
    }
    
    .primary-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0, 123, 255, 0.4) !important;
        background: linear-gradient(135deg, #0056b3, #004494) !important;
    }
    
    .stButton > button {
        width: 100% !important;
    }
    
    .preview-table {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main header with enhanced design
st.markdown("""
<div class="main-header">
    <h1>📊 Excel & CSV to Google Sheets Pro</h1>
    <p>Advanced file processing with support for CSV, XLSX, and multi-sheet workbooks</p>
    <p style="font-size: 0.9em; opacity: 0.9;">✨ Batch processing • 🔄 Multi-sheet support • 📧 Auto-sharing • 🎨 Custom formatting</p>
</div>
""", unsafe_allow_html=True)

class FileProcessor:
    """Enhanced file processing class with support for multiple formats"""
    
    def __init__(self):
        self.supported_extensions = [".csv", ".xlsx", ".xls"]
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
    def get_file_hash(self, file_content: bytes) -> str:
        """Generate hash for file deduplication"""
        return hashlib.md5(file_content).hexdigest()[:8]
    
    def validate_file(self, uploaded_file) -> Dict[str, Any]:
        """Comprehensive file validation"""
        issues = []
        warnings = []
        
        # Check file size
        if uploaded_file.size > self.max_file_size:
            issues.append(f"File size ({uploaded_file.size / 1024 / 1024:.1f}MB) exceeds limit (50MB)")
        
        # Check file extension
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in self.supported_extensions:
            issues.append(f"Unsupported file format: {file_ext}")
        
        # Check filename
        if len(uploaded_file.name) > 100:
            warnings.append("Filename is very long, consider shortening")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "is_valid": len(issues) == 0,
            "file_type": file_ext,
            "size_mb": uploaded_file.size / 1024 / 1024
        }
    
    def read_csv_file(self, uploaded_file) -> Dict[str, pd.DataFrame]:
        """Read CSV file with enhanced error handling"""
        try:
            # Try different encodings and separators
            encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
            separators = [",", ";", "\t", "|"]
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding=encoding, sep=sep, low_memory=False)
                        if len(df.columns) > 1 and len(df) > 0:
                            return {uploaded_file.name.replace(".csv", ""): df}
                    except:
                        continue
            
            # Fallback: try with default parameters
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            return {uploaded_file.name.replace(".csv", ""): df}
            
        except Exception as e:
            raise Exception(f"Failed to read CSV file: {str(e)}")
    
    def read_excel_file(self, uploaded_file) -> Dict[str, pd.DataFrame]:
        """Read Excel file with multi-sheet support"""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(uploaded_file)
            dataframes = {}
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(uploaded_file, sheet_name=sheet_name, engine="openpyxl")
                    if not df.empty:
                        # Clean sheet name for Google Sheets compatibility
                        clean_name = self.clean_sheet_name(sheet_name)
                        dataframes[clean_name] = df
                except Exception as e:
                    st.warning(f"Could not read sheet \'{sheet_name}\': {str(e)}")
                    continue
            
            if not dataframes:
                raise Exception("No readable sheets found in Excel file")
                
            return dataframes
            
        except Exception as e:
            raise Exception(f"Failed to read Excel file: {str(e)}")
    
    def clean_sheet_name(self, name: str) -> str:
        """Clean sheet name for Google Sheets compatibility"""
        # Remove invalid characters and limit length
        invalid_chars = ['[', ']', ':', '*', '?', '/', '\\']
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Limit length and remove leading/trailing spaces
        name = name.strip()[:100]
        
        # Ensure it's not empty
        if not name:
            name = "Sheet"
            
        return name
    
    def analyze_dataframe(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Comprehensive dataframe analysis"""
        analysis = {
            "name": sheet_name,
            "rows": len(df),
            "columns": len(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum() / 1024 / 1024,  # MB
            "issues": [],
            "warnings": [],
            "data_types": {},
            "null_counts": {},
            "sample_data": df.head(3).to_dict('records') if not df.empty else []
        }
        
        if df.empty:
            analysis["issues"].append("Sheet is empty")
            return analysis
        
        # Analyze columns
        for col in df.columns:
            analysis["data_types"][col] = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            analysis["null_counts"][col] = null_count
            
            if null_count > len(df) * 0.5:
                analysis["warnings"].append(f"Column \'{col}\' has >50% null values")
        
        # Check for issues
        if df.columns.duplicated().any():
            analysis["issues"].append("Duplicate column names found")
        
        if len(df.columns) == 0:
            analysis["issues"].append("No columns found")
        
        if len(df) > 10000:
            analysis["warnings"].append(f"Large dataset ({len(df):,} rows) - processing may be slow")
        
        if any(df.columns.str.len() > 100):
            analysis["warnings"].append("Some column names are very long")
        
        return analysis

# Initialize file processor
file_processor = FileProcessor()

# Sidebar configuration with enhanced design
st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.sidebar.markdown("## 🔐 Authentication")

# Default settings
DEFAULT_EMAIL = "Entremotivator@gmail.com"
DEFAULT_FOLDER_ID = ""  # Can be set to organize sheets in a specific folder

# Credentials upload
cred_file = st.sidebar.file_uploader(
    "Upload Google Service Account JSON",
    type="json",
    help="Download from Google Cloud Console → IAM & Admin → Service Accounts"
)


st.sidebar.markdown('</div>', unsafe_allow_html=True)

if cred_file:
    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.sidebar.markdown("## 📧 Sharing Configuration")
    
    # Email settings
    share_email = st.sidebar.text_input(
        "Share with email:",
        value=DEFAULT_EMAIL,
        help="Email address that will receive access to created sheets"
    )
    
    permission_level = st.sidebar.selectbox(
        "Permission level:",
        ["writer", "reader", "commenter"],
        index=0,
        help="Access level for the shared email"
    )
    
    # Notification settings
    notify_email = st.sidebar.checkbox(
        "Send email notification",
        value=True,
        help="Send email notification when sharing"
    )
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Advanced options
    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.sidebar.markdown("## ⚙️ Processing Options")
    
    # Formatting options
    auto_resize = st.sidebar.checkbox("Auto-resize columns", value=True)
    freeze_header = st.sidebar.checkbox("Freeze header row", value=True)
    add_timestamp = st.sidebar.checkbox("Add processing timestamp", value=True)
    
    # Data processing options
    remove_empty_rows = st.sidebar.checkbox("Remove completely empty rows", value=True)
    remove_empty_cols = st.sidebar.checkbox("Remove completely empty columns", value=True)
    convert_data_types = st.sidebar.checkbox("Optimize data types", value=False, help="Convert columns to appropriate data types")
    
    # Sheet organization
    st.sidebar.markdown("### 📁 Organization")
    create_summary = st.sidebar.checkbox("Create summary sheet", value=True, help="Add a sheet with file processing summary")
    
    # Naming convention
    naming_convention = st.sidebar.selectbox(
        "Sheet naming:",
        ["original", "with_timestamp", "with_hash", "custom_prefix"],
        help="How to name the created Google Sheets"
    )
    
    if naming_convention == "custom_prefix":
        custom_prefix = st.sidebar.text_input("Custom prefix:", value="Data_")
    else:
        custom_prefix = ""
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Processing limits
    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.sidebar.markdown("## 🎛️ Limits & Performance")
    
    max_rows_per_sheet = st.sidebar.number_input(
        "Max rows per sheet:",
        min_value=1000,
        max_value=1000000,
        value=100000,
        step=1000,
        help="Split large datasets into multiple sheets"
    )
    
    batch_size = st.sidebar.slider(
        "Upload batch size:",
        min_value=100,
        max_value=5000,
        value=1000,
        help="Rows to upload in each batch (affects speed vs reliability)"
    )
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Enhanced Google Sheets client with error handling
@st.cache_resource(show_spinner=False)
def get_gsheet_client(cred_path: str) -> Optional[gspread.Client]:
    """Get authorized Google Sheets client with comprehensive error handling"""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(cred_path, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Test the connection
        try:
            client.list_permissions('test')  # This will fail gracefully
        except:
            pass  # Expected to fail, just testing connection
            
        return client
    except Exception as e:
        st.error(f"❌ Authentication failed: {str(e)}")
        return None

def format_dataframe(df: pd.DataFrame, options: Dict[str, Any]) -> pd.DataFrame:
    """Enhanced dataframe formatting and cleaning based on user options"""
    processed_df = df.copy()

    if options.get("remove_empty_rows"):
        processed_df.dropna(how='all', inplace=True)
    if options.get("remove_empty_cols"):
        processed_df.dropna(axis=1, how='all', inplace=True)

    if options.get("convert_data_types"):
        for col in processed_df.columns:
            # Attempt to convert to numeric, then datetime
            processed_df[col] = pd.to_numeric(processed_df[col], errors='ignore')
            if pd.api.types.is_object_dtype(processed_df[col]):
                try:
                    processed_df[col] = pd.to_datetime(processed_df[col], errors='coerce')
                except:
                    pass # Keep as object if not convertible to datetime

    return processed_df

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10), retry=retry_if_exception_type(gspread.exceptions.APIError))
def upload_dataframe_to_sheets(client: gspread.Client, df: pd.DataFrame, sheet_name: str, options: Dict[str, Any], folder_id: str = "") -> str:
    """Uploads a Pandas DataFrame to a new Google Sheet, with advanced features"""
    try:
        # Create a new spreadsheet
        spreadsheet = client.create(sheet_name)
        if folder_id:
            client.drive.authorize()
            client.drive.files.update(fileId=spreadsheet.id, addParents=folder_id, removeParents='root').execute()

        # Share the spreadsheet
        spreadsheet.share(options["share_email"], perm_type='user', role=options["permission_level"], notify=options["notify_email"])

        worksheet = spreadsheet.worksheet("Sheet1") # Default sheet

        # Format dataframe based on options
        processed_df = format_dataframe(df, options)

        # Update all cells in batches
        total_rows = len(processed_df)
        total_cols = len(processed_df.columns)
        batch_size = options.get("batch_size", 1000)

        # Prepare header
        worksheet.update(range_name=f'A1:{gspread.utils.rowcol_to_a1(1, total_cols)}', values=[[str(col) for col in processed_df.columns]])

        # Upload data in batches
        for i in range(0, total_rows, batch_size):
            batch_df = processed_df.iloc[i:i+batch_size]
            values = batch_df.values.tolist()
            start_row = i + 2 # +1 for 0-index to 1-index, +1 for header row
            end_row = start_row + len(values) - 1
            worksheet.update(range_name=f'A{start_row}:{gspread.utils.rowcol_to_a1(end_row, total_cols)}', values=values)
            st.session_state.progress_bar.progress((i + len(values)) / total_rows, text=f"Uploading data: {i + len(values)}/{total_rows} rows")
            time.sleep(0.1) # To prevent hitting API limits

        # Apply formatting options
        if options.get("auto_resize"):
            worksheet.freeze(rows=1)
            worksheet.format('A1:ZZZ1', {'textFormat': {'bold': True}})
            worksheet.columns_auto_resize(0, total_cols - 1)

        if options.get("freeze_header"):
            worksheet.freeze(rows=1)

        if options.get("add_timestamp"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.update_cell(total_rows + 2, 1, f"Processed on: {timestamp}")

        st.success(f"✅ Successfully uploaded '{sheet_name}' to Google Sheet: {spreadsheet.url}")
        logger.info(f"Uploaded '{sheet_name}' to {spreadsheet.url}")
        return spreadsheet.url

    except gspread.exceptions.APIError as e:
        try:
            error_details = e.response.json()
            error_message = error_details.get('error', {}).get('message', str(e))
        except:
            error_message = str(e)
        st.error(f"❌ Failed to upload '{sheet_name}' to Google Sheets: APIError: {error_message}")
        logger.error(f"Error uploading '{sheet_name}': {error_message}")
        raise # Re-raise the exception to trigger retry
    except Exception as e:
        st.error(f"❌ Failed to upload '{sheet_name}' to Google Sheets: {str(e)}")
        logger.error(f"Error uploading '{sheet_name}': {str(e)}")
        return ""

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10), retry=retry_if_exception_type(gspread.exceptions.APIError))
def upload_dataframes_to_single_workbook(client: gspread.Client, dataframes: Dict[str, pd.DataFrame], workbook_name: str, options: Dict[str, Any], folder_id: str = "") -> str:
    """Uploads multiple Pandas DataFrames to a single new Google Sheet workbook, each as a separate worksheet.
    The first DataFrame in the dictionary will be uploaded to the default 'Sheet1' worksheet, which will be renamed.
    Subsequent DataFrames will be added as new worksheets.
    """
    try:
        # Create a new spreadsheet (workbook)
        spreadsheet = client.create(workbook_name)
        if folder_id:
            client.drive.authorize()
            client.drive.files.update(fileId=spreadsheet.id, addParents=folder_id, removeParents='root').execute()

        # Share the spreadsheet
        spreadsheet.share(options["share_email"], perm_type='user', role=options["permission_level"], notify=options["notify_email"])

        first_sheet_name = list(dataframes.keys())[0]
        first_df = dataframes[first_sheet_name]

        # Rename the default 'Sheet1' and upload the first DataFrame
        worksheet = spreadsheet.worksheet("Sheet1")
        worksheet.update_title(first_sheet_name)
        
        # Resize the worksheet to fit the data before updating
        num_rows = len(first_df) + 1  # +1 for header
        num_cols = len(first_df.columns)
        worksheet.resize(rows=num_rows, cols=num_cols)

        processed_df = format_dataframe(first_df, options)
        worksheet.update(values=[processed_df.columns.values.tolist()] + processed_df.values.tolist(), range_name=f'A1:{gspread.utils.rowcol_to_a1(num_rows, num_cols)}')
        
        # Apply formatting options for the first sheet
        if options.get("auto_resize"):
            worksheet.freeze(rows=1)
            worksheet.format('A1:ZZZ1', {'textFormat': {'bold': True}})
            worksheet.columns_auto_resize(0, len(processed_df.columns) - 1)
        if options.get("freeze_header"):
            worksheet.freeze(rows=1)
        if options.get("add_timestamp"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.update_cell(len(processed_df) + 2, 1, f"Processed on: {timestamp}")

        st.session_state.progress_bar.progress(1 / len(dataframes), text=f"Uploading sheet \'{first_sheet_name}\' to Google Sheet")

        # Add and upload subsequent DataFrames as new worksheets
        for i, (sheet_name, df) in enumerate(list(dataframes.items())[1:]):
            new_worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=df.shape[0] + 1, cols=df.shape[1])
            
            # Resize the new worksheet to fit the data before updating
            num_rows = len(df) + 1  # +1 for header
            num_cols = len(df.columns)
            new_worksheet.resize(rows=num_rows, cols=num_cols)

            processed_df = format_dataframe(df, options)
            new_worksheet.update(values=[processed_df.columns.values.tolist()] + processed_df.values.tolist(), range_name=f'A1:{gspread.utils.rowcol_to_a1(num_rows, num_cols)}')

            # Apply formatting options for subsequent sheets
            if options.get("auto_resize"):
                new_worksheet.freeze(rows=1)
                new_worksheet.format('A1:ZZZ1', {'textFormat': {'bold': True}})
                new_worksheet.columns_auto_resize(0, len(processed_df.columns) - 1)
            if options.get("freeze_header"):
                new_worksheet.freeze(rows=1)
            if options.get("add_timestamp"):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_worksheet.update_cell(len(processed_df) + 2, 1, f"Processed on: {timestamp}")
            
            st.session_state.progress_bar.progress((i + 2) / len(dataframes), text=f"Uploading sheet \'{sheet_name}\' to Google Sheet")
            time.sleep(0.1) # To prevent hitting API limits

        st.success(f"✅ Successfully uploaded workbook \'{workbook_name}\' to Google Sheet: {spreadsheet.url}")
        logger.info(f"Uploaded workbook \'{workbook_name}\' to {spreadsheet.url}")
        return spreadsheet.url

    except gspread.exceptions.APIError as e:
        try:
            error_details = e.response.json()
            error_message = error_details.get('error', {}).get('message', str(e))
        except:
            error_message = str(e)
        st.error(f"❌ Failed to upload workbook \'{workbook_name}\' to Google Sheets: APIError: {error_message}")
        logger.error(f"Error uploading workbook \'{workbook_name}\' to Google Sheets: {error_message}")
        raise # Re-raise the exception to trigger retry
    except Exception as e:
        st.error(f"❌ Failed to upload workbook \'{workbook_name}\' to Google Sheets: {str(e)}")
        logger.error(f"Error uploading workbook \'{workbook_name}\' to Google Sheets: {str(e)}")
        return ""


# Main application logic
def main():
    if "progress_bar" not in st.session_state:
        st.session_state.progress_bar = None

    st.markdown("<div class=\"upload-section\">", unsafe_allow_html=True)
    st.markdown("<h2>⬆️ Upload Your File</h2>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Choose an Excel (.xlsx, .xls) or CSV (.csv) file",
        type=file_processor.supported_extensions,
        accept_multiple_files=False,
        help="Select a file to convert and upload to Google Sheets."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file is not None:
        file_validation = file_processor.validate_file(uploaded_file)

        if not file_validation["is_valid"]:
            st.markdown(f"<div class=\"error-box\"><h3>File Validation Errors:</h3><ul>{''.join([f'<li>{issue}</li>' for issue in file_validation['issues']])}</ul></div>", unsafe_allow_html=True)
            return

        if file_validation["warnings"]:
            st.markdown(f"<div class=\"warning-box\"><h3>File Validation Warnings:</h3><ul>{''.join([f'<li>{warning}</li>' for warning in file_validation['warnings']])}</ul></div>", unsafe_allow_html=True)

        st.markdown(f"<div class=\"info-box\"><b>File Info:</b> Name: {uploaded_file.name}, Type: {file_validation['file_type']}, Size: {file_validation['size_mb']:.2f} MB</div>", unsafe_allow_html=True)

        if cred_file:
            # Save credentials to a temporary file
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_cred_file:
                temp_cred_file.write(cred_file.getvalue().decode("utf-8"))
                temp_cred_path = temp_cred_file.name

            client = get_gsheet_client(temp_cred_path)

            if client:
                st.markdown("<div class=\"progress-container\">", unsafe_allow_html=True)
                st.session_state.progress_bar = st.progress(0, text="Starting upload...")
                st.markdown("</div>", unsafe_allow_html=True)

                try:
                    dataframes = {}
                    if file_validation["file_type"] == ".csv":
                        dataframes = file_processor.read_csv_file(uploaded_file)
                    elif file_validation["file_type"] in [".xlsx", ".xls"]:
                        dataframes = file_processor.read_excel_file(uploaded_file)

                    if dataframes:
                        # Determine workbook name
                        base_name = os.path.splitext(uploaded_file.name)[0]
                        workbook_name = base_name
                        if naming_convention == "with_timestamp":
                            workbook_name = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        elif naming_convention == "with_hash":
                            workbook_name = f"{base_name}_{file_processor.get_file_hash(uploaded_file.getvalue())}"
                        elif naming_convention == "custom_prefix":
                            workbook_name = f"{custom_prefix}{base_name}"

                        # Upload all dataframes to a single Google Sheet workbook
                        uploaded_url = upload_dataframes_to_single_workbook(client, dataframes, workbook_name, {
                            "share_email": share_email,
                            "permission_level": permission_level,
                            "notify_email": notify_email,
                            "auto_resize": auto_resize,
                            "freeze_header": freeze_header,
                            "add_timestamp": add_timestamp,
                            "remove_empty_rows": remove_empty_rows,
                            "remove_empty_cols": remove_empty_cols,
                            "convert_data_types": convert_data_types,
                            "batch_size": batch_size
                        }, DEFAULT_FOLDER_ID)

                        if uploaded_url:
                            st.markdown(f"<div class=\"success-box\"><h3>Upload Complete!</h3><p>Your workbook has been successfully uploaded to Google Sheets.</p><p><a href=\"{uploaded_url}\" target=\"_blank\" class=\"sheet-link\">Open Google Sheet</a></p></div>", unsafe_allow_html=True)

                            # Display analysis for each sheet
                            st.markdown("<h2>📊 Data Analysis Summary</h2>", unsafe_allow_html=True)
                            for sheet_name, df in dataframes.items():
                                analysis = file_processor.analyze_dataframe(df, sheet_name)
                                st.markdown(f"<div class=\"info-box\"><h4>Sheet: {analysis['name']}</h4>", unsafe_allow_html=True)
                                st.write(f"Rows: {analysis['rows']:,}, Columns: {analysis['columns']:,}")
                                if analysis["issues"]:
                                    st.markdown(f"<p style=\"color:red;\">Issues: {''.join(analysis['issues'])}</p>", unsafe_allow_html=True)
                                if analysis["warnings"]:
                                    st.markdown(f"<p style=\"color:orange;\">Warnings: {''.join(analysis['warnings'])}</p>", unsafe_allow_html=True)
                                st.markdown("</div>", unsafe_allow_html=True)
                                
                                # Display sample data
                                if not df.empty:
                                    st.markdown(f"<h5>Sample Data for \'{sheet_name}\':</h5>", unsafe_allow_html=True)
                                    st.markdown("<div class=\"preview-table\">", unsafe_allow_html=True)
                                    st.dataframe(df.head())
                                    st.markdown("</div>", unsafe_allow_html=True)

                    else:
                        st.markdown("<div class=\"error-box\">No dataframes were read from the uploaded file.</div>", unsafe_allow_html=True)

                except Exception as e:
                    st.markdown(f"<div class=\"error-box\">An error occurred during processing: {str(e)}</div>", unsafe_allow_html=True)
                finally:
                    # Clean up temporary credential file
                    if os.path.exists(temp_cred_path):
                        os.remove(temp_cred_path)
            else:
                st.markdown("<div class=\"error-box\">Google Sheets client could not be initialized. Please check your credentials.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class=\"warning-box\">Please upload your Google Service Account JSON credentials to proceed.</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

