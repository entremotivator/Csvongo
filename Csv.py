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
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.2);
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
                    st.warning(f"Could not read sheet '{sheet_name}': {str(e)}")
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
                analysis["warnings"].append(f"Column '{col}' has >50% null values")
        
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
        header = [str(col) for col in processed_df.columns]
        worksheet.update(f'A1:{gspread.utils.rowcol_to_a1(1, total_cols)}', [header])

        # Upload data in batches
        for i in range(0, total_rows, batch_size):
            batch_df = processed_df.iloc[i:i+batch_size]
            values = batch_df.values.tolist()
            start_row = i + 2 # +1 for 0-index to 1-index, +1 for header row
            end_row = start_row + len(values) - 1
            range_name = f'A{start_row}:{gspread.utils.rowcol_to_a1(end_row, total_cols)}'
            worksheet.update(range_name, values)
            st.session_state.progress_bar.progress((i + len(values)) / total_rows, text=f"Uploading data: {i + len(values)}/{total_rows} rows")
            time.sleep(0.1) # To prevent hitting API limits

        # Apply formatting options
        if options.get("auto_resize"):
            worksheet.freeze(rows=1)
            worksheet.format('A1:ZZZ1', {'textFormat': {'bold': True}})
            worksheet.columns_auto_resize(1, total_cols)
        
        if options.get("freeze_header"):
            worksheet.freeze(rows=1)

        if options.get("add_timestamp"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.update_cell(total_rows + 2, 1, f"Processed on: {timestamp}")

        return spreadsheet.url

    except gspread.exceptions.APIError as e:
        st.error(f"Google Sheets API Error: {e.response['content']}")
        raise
    except Exception as e:
        st.error(f"An unexpected error occurred during upload: {str(e)}")
        raise

def display_file_preview(file_content: bytes, file_type: str):
    """Display a preview of the uploaded file content"""
    st.subheader("File Preview")
    try:
        if file_type == ".csv":
            df_preview = pd.read_csv(io.BytesIO(file_content))
        elif file_type in [".xlsx", ".xls"]:
            df_preview = pd.read_excel(io.BytesIO(file_content))
        else:
            st.warning("Cannot display preview for this file type.")
            return

        st.dataframe(df_preview.head(), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying preview: {e}")

# Main application logic
st.title("🚀 Start Your Upload")

if cred_file:
    # Save credentials to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_cred_file:
        temp_cred_file.write(cred_file.getvalue())
        temp_cred_path = temp_cred_file.name

    gsheet_client = get_gsheet_client(temp_cred_path)

    if gsheet_client:
        st.success("✅ Google Sheets client authenticated successfully!")
        
        uploaded_files = st.file_uploader(
            "Upload your CSV or Excel files",
            type=file_processor.supported_extensions,
            accept_multiple_files=True,
            help="Drag and drop your files here. Supports CSV, XLSX, XLS."
        )

        if uploaded_files:
            st.session_state.progress_bar = st.progress(0, text="Starting file processing...")
            all_processed_urls = []
            total_files = len(uploaded_files)

            for i, uploaded_file in enumerate(uploaded_files):
                st.info(f"Processing file {i+1}/{total_files}: {uploaded_file.name}")
                validation_result = file_processor.validate_file(uploaded_file)

                if not validation_result['is_valid']:
                    st.error(f"❌ Validation failed for {uploaded_file.name}: {', '.join(validation_result['issues'])}")
                    continue
                
                if validation_result['warnings']:
                    for warning in validation_result['warnings']:
                        st.warning(f"⚠️ Warning for {uploaded_file.name}: {warning}")

                file_content = uploaded_file.getvalue()
                file_hash = file_processor.get_file_hash(file_content)
                
                display_file_preview(file_content, validation_result['file_type'])

                try:
                    if validation_result['file_type'] == ".csv":
                        dataframes = file_processor.read_csv_file(uploaded_file)
                    elif validation_result['file_type'] in [".xlsx", ".xls"]:
                        dataframes = file_processor.read_excel_file(uploaded_file)
                    else:
                        st.error(f"Unsupported file type for processing: {validation_result['file_type']}")
                        continue

                    for sheet_name, df in dataframes.items():
                        analysis = file_processor.analyze_dataframe(df, sheet_name)
                        st.write(f"### Analysis for sheet: {sheet_name}")
                        st.json(analysis)

                        if analysis['issues']:
                            st.error(f"Sheet '{sheet_name}' has critical issues: {', '.join(analysis['issues'])}")
                            continue

                        # Determine sheet name based on convention
                        final_sheet_name = sheet_name
                        if st.session_state.get("naming_convention") == "with_timestamp":
                            final_sheet_name = f"{sheet_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        elif st.session_state.get("naming_convention") == "with_hash":
                            final_sheet_name = f"{sheet_name}_{file_hash}"
                        elif st.session_state.get("naming_convention") == "custom_prefix":
                            final_sheet_name = f"{st.session_state.get('custom_prefix', 'Data_')}{sheet_name}"

                        # Collect all options for upload
                        upload_options = {
                            "share_email": st.session_state.get("share_email", DEFAULT_EMAIL),
                            "permission_level": st.session_state.get("permission_level", "writer"),
                            "notify_email": st.session_state.get("notify_email", True),
                            "auto_resize": st.session_state.get("auto_resize", True),
                            "freeze_header": st.session_state.get("freeze_header", True),
                            "add_timestamp": st.session_state.get("add_timestamp", True),
                            "remove_empty_rows": st.session_state.get("remove_empty_rows", True),
                            "remove_empty_cols": st.session_state.get("remove_empty_cols", True),
                            "convert_data_types": st.session_state.get("convert_data_types", False),
                            "batch_size": st.session_state.get("batch_size", 1000)
                        }

                        st.write(f"Attempting to upload sheet '{sheet_name}' to Google Sheets...")
                        sheet_url = upload_dataframe_to_sheets(gsheet_client, df, final_sheet_name, upload_options, DEFAULT_FOLDER_ID)
                        all_processed_urls.append(sheet_url)
                        st.success(f"✅ Successfully uploaded '{sheet_name}' to [Google Sheet]({sheet_url})")

                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                    logger.error(f"Error processing {uploaded_file.name}: {e}", exc_info=True)

            st.session_state.progress_bar.progress(1.0, text="All files processed!")
            st.balloons()

            st.subheader("All Processed Sheets:")
            for url in all_processed_urls:
                st.markdown(f"<a href=\"{url}\" target=\"_blank\" class=\"sheet-link\">Open Sheet</a>", unsafe_allow_html=True)

    # Clean up temporary credentials file
    os.remove(temp_cred_path)

else:
    st.info("Please upload your Google Service Account JSON credentials in the sidebar to get started.")
    st.markdown("""
    <div class="info-box">
        <h3>Getting Started:</h3>
        <ol>
            <li>Upload your Google Service Account JSON file in the sidebar.</li>
            <li>Configure sharing and processing options.</li>
            <li>Upload your CSV or Excel files to convert them to Google Sheets.</li>
        </ol>
        <p>Need help? Refer to the <a href="https://cloud.google.com/docs/authentication/getting-started" target="_blank">Google Cloud documentation</a> for service account setup.</p>
    </div>
    """, unsafe_allow_html=True)


