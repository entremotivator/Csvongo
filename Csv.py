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
        self.supported_extensions = ['.csv', '.xlsx', '.xls']
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
            'issues': issues,
            'warnings': warnings,
            'is_valid': len(issues) == 0,
            'file_type': file_ext,
            'size_mb': uploaded_file.size / 1024 / 1024
        }
    
    def read_csv_file(self, uploaded_file) -> Dict[str, pd.DataFrame]:
        """Read CSV file with enhanced error handling"""
        try:
            # Try different encodings and separators
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            separators = [',', ';', '\t', '|']
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding=encoding, sep=sep, low_memory=False)
                        if len(df.columns) > 1 and len(df) > 0:
                            return {uploaded_file.name.replace('.csv', ''): df}
                    except:
                        continue
            
            # Fallback: try with default parameters
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            return {uploaded_file.name.replace('.csv', ''): df}
            
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
                    df = pd.read_excel(uploaded_file, sheet_name=sheet_name, engine='openpyxl')
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
            'name': sheet_name,
            'rows': len(df),
            'columns': len(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum() / 1024 / 1024,  # MB
            'issues': [],
            'warnings': [],
            'data_types': {},
            'null_counts': {},
            'sample_data': df.head(3).to_dict('records') if not df.empty else []
        }
        
        if df.empty:
            analysis['issues'].append("Sheet is empty")
            return analysis
        
        # Analyze columns
        for col in df.columns:
            analysis['data_types'][col] = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            analysis['null_counts'][col] = null_count
            
            if null_count > len(df) * 0.5:
                analysis['warnings'].append(f"Column '{col}' has >50% null values")
        
        # Check for issues
        if df.columns.duplicated().any():
            analysis['issues'].append("Duplicate column names found")
        
        if len(df.columns) == 0:
            analysis['issues'].append("No columns found")
        
        if len(df) > 10000:
            analysis['warnings'].append(f"Large dataset ({len(df):,} rows) - processing may be slow")
        
        if any(df.columns.str.len() > 100):
            analysis['warnings'].append("Some column names are very long")
        
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
    """Enhanced dataframe formatting with multiple options"""
    df_formatted = df.copy()
    
    # Remove empty rows/columns if requested
    if options.get('remove_empty_rows', False):
        df_formatted = df_formatted.dropna(how='all')
    
    if options.get('remove_empty_cols', False):
        df_formatted = df_formatted.dropna(axis=1, how='all')
    
    # Add timestamp if requested
    if options.get('add_timestamp', False):
        df_formatted['Processing_Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df_formatted['Processing_User'] = options.get('user_email', 'Unknown')
    
    # Clean column names
    df_formatted.columns = [
        str(col).strip().replace('\n', ' ').replace('\r', '').replace('\t', ' ')[:100]
        for col in df_formatted.columns
    ]
    
    # Handle duplicate column names
    cols = df_formatted.columns.tolist()
    seen = {}
    for i, col in enumerate(cols):
        if col in seen:
            seen[col] += 1
            cols[i] = f"{col}_{seen[col]}"
        else:
            seen[col] = 0
    df_formatted.columns = cols
    
    # Convert data types if requested
    if options.get('convert_data_types', False):
        for col in df_formatted.columns:
            # Skip timestamp columns
            if 'timestamp' in col.lower():
                continue
                
            # Try to convert to numeric
            try:
                df_formatted[col] = pd.to_numeric(df_formatted[col], errors='ignore')
            except:
                pass
    
    # Ensure all data is string for Google Sheets compatibility
    for col in df_formatted.columns:
        df_formatted[col] = df_formatted[col].astype(str)
    
    return df_formatted

def split_large_dataframe(df: pd.DataFrame, max_rows: int, base_name: str) -> List[Tuple[pd.DataFrame, str]]:
    """Split large dataframes into smaller chunks"""
    if len(df) <= max_rows:
        return [(df, base_name)]
    
    chunks = []
    num_chunks = (len(df) - 1) // max_rows + 1
    
    for i in range(num_chunks):
        start_idx = i * max_rows
        end_idx = min((i + 1) * max_rows, len(df))
        chunk_df = df.iloc[start_idx:end_idx].copy()
        chunk_name = f"{base_name}_Part_{i+1}_of_{num_chunks}"
        chunks.append((chunk_df, chunk_name))
    
    return chunks

def create_summary_sheet_data(file_results: List[Dict], processing_options: Dict) -> pd.DataFrame:
    """Create comprehensive summary sheet"""
    summary_data = []
    
    for result in file_results:
        summary_data.append({
            'Original_File': result.get('original_filename', 'Unknown'),
            'File_Type': result.get('file_type', 'Unknown'),
            'File_Size_MB': result.get('file_size_mb', 0),
            'Sheets_Created': len(result.get('created_sheets', [])),
            'Total_Rows_Processed': result.get('total_rows', 0),
            'Total_Columns': result.get('total_columns', 0),
            'Processing_Status': 'Success' if result.get('success', False) else 'Failed',
            'Error_Message': result.get('error', ''),
            'Processing_Time_Seconds': result.get('processing_time', 0),
            'Created_Sheets': ', '.join([s['name'] for s in result.get('created_sheets', [])]),
            'Processing_DateTime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Processing_Options': str(processing_options)
        })
    
    return pd.DataFrame(summary_data)

def upload_to_google_sheets(client: gspread.Client, df: pd.DataFrame, sheet_name: str, 
                          options: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced Google Sheets upload with batch processing and error recovery"""
    try:
        start_time = time.time()
        
        # Create spreadsheet
        spreadsheet = client.create(sheet_name)
        worksheet = spreadsheet.get_worksheet(0)
        
        # Prepare data
        headers = df.columns.tolist()
        data_rows = df.values.tolist()
        all_data = [headers] + data_rows
        
        # Batch upload for large datasets
        batch_size = options.get('batch_size', 1000)
        total_rows = len(all_data)
        
        if total_rows <= batch_size:
            # Single upload for small datasets
            worksheet.update(all_data)
        else:
            # Batch upload for large datasets
            for i in range(0, total_rows, batch_size):
                batch_data = all_data[i:i + batch_size]
                start_row = i + 1
                
                try:
                    # Update in batches
                    range_name = f'A{start_row}:{gspread.utils.rowcol_to_a1(start_row + len(batch_data) - 1, len(headers))}'
                    worksheet.update(range_name, batch_data)
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as batch_error:
                    st.warning(f"Batch upload error at row {start_row}: {str(batch_error)}")
                    continue
        
        # Apply formatting
        if options.get('freeze_header', True):
            worksheet.freeze(rows=1)
        
        if options.get('auto_resize', True):
            worksheet.columns_auto_resize(0, len(headers))
        
        # Apply conditional formatting for better readability
        try:
            # Add alternating row colors
            worksheet.format('A1:ZZ1', {
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                'textFormat': {'bold': True}
            })
        except:
            pass  # Formatting is optional
        
        # Share the spreadsheet
        share_status = "Not shared"
        if options.get('share_email'):
            try:
                spreadsheet.share(
                    options['share_email'], 
                    perm_type='user', 
                    role=options.get('permission_level', 'writer'),
                    notify=options.get('notify_email', True)
                )
                share_status = f"Shared with {options['share_email']} ({options.get('permission_level', 'writer')})"
            except Exception as share_error:
                share_status = f"Share failed: {str(share_error)}"
        
        processing_time = time.time() - start_time
        
        return {
            'success': True,
            'spreadsheet_id': spreadsheet.id,
            'url': f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}",
            'name': sheet_name,
            'rows_uploaded': total_rows - 1,  # Exclude header
            'columns_uploaded': len(headers),
            'share_status': share_status,
            'processing_time': processing_time
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'name': sheet_name
        }

def generate_sheet_name(original_name: str, naming_convention: str, custom_prefix: str = "") -> str:
    """Generate sheet name based on naming convention"""
    base_name = os.path.splitext(original_name)[0]
    
    if naming_convention == "with_timestamp":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}"
    elif naming_convention == "with_hash":
        hash_suffix = hashlib.md5(original_name.encode()).hexdigest()[:8]
        return f"{base_name}_{hash_suffix}"
    elif naming_convention == "custom_prefix":
        return f"{custom_prefix}{base_name}"
    else:
        return base_name

# Main application logic
if cred_file is not None:
    # Validate and load credentials
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(cred_file.read())
        cred_path = tmp.name
    
    try:
        with open(cred_path, 'r') as f:
            cred_data = json.load(f)
        
        st.sidebar.success("✅ Credentials validated")
        st.sidebar.info(f"**Service Account:** {cred_data.get('client_email', 'Unknown')[:30]}...")
        
        # Get Google Sheets client
        client = get_gsheet_client(cred_path)
        
        if client is None:
            st.error("Failed to initialize Google Sheets client")
            st.stop()
            
    except Exception as e:
        st.sidebar.error(f"❌ Invalid credentials: {str(e)}")
        st.stop()
    
    # Enhanced file upload section
    st.markdown("""
    <div class="feature-card">
        <h3>📁 Upload Your Files</h3>
        <p>Support for multiple file formats with advanced processing capabilities:</p>
        <ul>
            <li><strong>CSV files</strong> - Single sheet with intelligent parsing</li>
            <li><strong>Excel files (.xlsx/.xls)</strong> - Multi-sheet support with individual processing</li>
            <li><strong>Batch processing</strong> - Upload multiple files simultaneously</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Choose files to process",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        help="Select CSV or Excel files. Multiple files can be processed simultaneously."
    )
    
    if uploaded_files:
        st.markdown("---")
        
        # File validation and preview
        st.markdown("### 📋 File Analysis & Preview")
        
        valid_files = []
        invalid_files = []
        file_data = {}
        
        # Process each uploaded file
        for uploaded_file in uploaded_files:
            validation = file_processor.validate_file(uploaded_file)
            
            if validation['is_valid']:
                valid_files.append(uploaded_file)
                
                try:
                    # Read file based on type
                    if validation['file_type'] == '.csv':
                        sheets = file_processor.read_csv_file(uploaded_file)
                    else:
                        sheets = file_processor.read_excel_file(uploaded_file)
                    
                    # Analyze each sheet
                    sheet_analyses = {}
                    for sheet_name, df in sheets.items():
                        sheet_analyses[sheet_name] = file_processor.analyze_dataframe(df, sheet_name)
                    
                    file_data[uploaded_file.name] = {
                        'validation': validation,
                        'sheets': sheets,
                        'analyses': sheet_analyses
                    }
                    
                except Exception as e:
                    invalid_files.append({
                        'file': uploaded_file,
                        'error': str(e)
                    })
                    
            else:
                invalid_files.append({
                    'file': uploaded_file,
                    'validation': validation
                })
        
        # Display file summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h4>📁 Total Files</h4>
                <h2>{len(uploaded_files)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h4>✅ Valid Files</h4>
                <h2 style="color: #28a745;">{len(valid_files)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_sheets = sum(len(data['sheets']) for data in file_data.values())
            st.markdown(f"""
            <div class="metric-card">
                <h4>📄 Total Sheets</h4>
                <h2 style="color: #17a2b8;">{total_sheets}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_rows = sum(
                sum(len(df) for df in data['sheets'].values()) 
                for data in file_data.values()
            )
            st.markdown(f"""
            <div class="metric-card">
                <h4>📊 Total Rows</h4>
                <h2 style="color: #6f42c1;">{total_rows:,}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Show invalid files if any
        if invalid_files:
            st.markdown("""
            <div class="error-box">
                <h4>❌ Files with Issues</h4>
            </div>
            """, unsafe_allow_html=True)
            
            for invalid in invalid_files:
                if 'validation' in invalid:
                    issues = invalid['validation']['issues']
                    st.error(f"**{invalid['file'].name}**: {', '.join(issues)}")
                else:
                    st.error(f"**{invalid['file'].name}**: {invalid['error']}")
        
        # Display detailed analysis for valid files
        if valid_files:
            st.markdown("### 📊 Detailed File Analysis")
            
            # Create tabs for each file
            if len(valid_files) == 1:
                # Single file - no tabs needed
                file_name = valid_files[0].name
                data = file_data[file_name]
                display_file_analysis(file_name, data)
            else:
                # Multiple files - use tabs
                tab_names = [f"📄 {f.name[:20]}{'...' if len(f.name) > 20 else ''}" for f in valid_files]
                tabs = st.tabs(tab_names)
                
                for i, tab in enumerate(tabs):
                    with tab:
                        file_name = valid_files[i].name
                        data = file_data[file_name]
                        display_file_analysis(file_name, data)
            
            # Process to Google Sheets button
            st.markdown("---")
            st.markdown("### 🚀 Process Files")
            
            # Collect processing options
            processing_options = {
                'share_email': share_email,
                'permission_level': permission_level,
                'notify_email': notify_email,
                'auto_resize': auto_resize,
                'freeze_header': freeze_header,
                'add_timestamp': add_timestamp,
                'remove_empty_rows': remove_empty_rows,
                'remove_empty_cols': remove_empty_cols,
                'convert_data_types': convert_data_types,
                'create_summary': create_summary,
                'naming_convention': naming_convention,
                'custom_prefix': custom_prefix,
                'max_rows_per_sheet': max_rows_per_sheet,
                'batch_size': batch_size,
                'user_email': cred_data.get('client_email', 'Unknown')
            }
            
            # Summary of what will be processed
            st.markdown("""
            <div class="info-box">
                <h4>📋 Processing Summary</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Files to process:** {len(valid_files)}")
                st.write(f"**Total sheets:** {total_sheets}")
                st.write(f"**Total rows:** {total_rows:,}")
                st.write(f"**Share with:** {share_email or 'No sharing'}")
            
            with col2:
                st.write(f"**Auto-resize columns:** {'Yes' if auto_resize else 'No'}")
                st.write(f"**Freeze headers:** {'Yes' if freeze_header else 'No'}")
                st.write(f"**Add timestamps:** {'Yes' if add_timestamp else 'No'}")
                st.write(f"**Create summary:** {'Yes' if create_summary else 'No'}")
            
            # Main processing button
            if st.button("🚀 Process All Files to Google Sheets", type="primary", use_container_width=True):
                process_files_to_sheets(client, file_data, processing_options)

def display_file_analysis(file_name: str, data: Dict[str, Any]):
    """Display detailed analysis for a single file"""
    validation = data['validation']
    sheets = data['sheets']
    analyses = data['analyses']
    
    # File information
    st.markdown(f"""
    <div class="file-preview">
        <h4>📄 {file_name}</h4>
        <p><strong>Type:</strong> {validation['file_type'].upper()}</p>
        <p><strong>Size:</strong> {validation['size_mb']:.2f} MB</p>
        <p><strong>Sheets:</strong> {len(sheets)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show warnings if any
    if any(analysis['warnings'] for analysis in analyses.values()):
        warnings = []
        for analysis in analyses.values():
            warnings.extend(analysis['warnings'])
        
        st.markdown("""
        <div class="warning-box">
            <h5>⚠️ Warnings</h5>
        </div>
        """, unsafe_allow_html=True)
        
        for warning in warnings:
            st.warning(warning)
    
    # Display each sheet
    for sheet_name, df in sheets.items():
        analysis = analyses[sheet_name]
        
        with st.expander(f"📊 {sheet_name} ({analysis['rows']:,} rows × {analysis['columns']} columns)", expanded=True):
            # Sheet statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", f"{analysis['rows']:,}")
            with col2:
                st.metric("Columns", analysis['columns'])
            with col3:
                st.metric("Memory", f"{analysis['memory_usage']:.1f} MB")
            
            # Show issues if any
            if analysis['issues']:
                for issue in analysis['issues']:
                    st.error(f"❌ {issue}")
            
            # Data preview
            st.subheader("📋 Data Preview")
            if not df.empty:
                # Show first few rows
                st.dataframe(
                    df.head(10), 
                    use_container_width=True,
                    height=300
                )
                
                # Column information
                if st.checkbox(f"Show column details for {sheet_name}", key=f"col_details_{file_name}_{sheet_name}"):
                    col_info = []
                    for col in df.columns:
                        col_info.append({
                            'Column': col,
                            'Data Type': analysis['data_types'][col],
                            'Non-Null Count': len(df) - analysis['null_counts'][col],
                            'Null Count': analysis['null_counts'][col],
                            'Null %': f"{(analysis['null_counts'][col] / len(df) * 100):.1f}%"
                        })
                    
                    st.dataframe(pd.DataFrame(col_info), use_container_width=True)
            else:
                st.warning("This sheet is empty")

def process_files_to_sheets(client: gspread.Client, file_data: Dict[str, Any], options: Dict[str, Any]):
    """Process all files to Google Sheets with progress tracking"""
    
    # Initialize progress tracking
    progress_container = st.container()
    
    with progress_container:
        st.markdown("""
        <div class="progress-container">
            <h4>🔄 Processing Files to Google Sheets</h4>
        </div>
        """, unsafe_allow_html=True)
    
    # Create progress bars
    overall_progress = st.progress(0)
    status_text = st.empty()
    
    # Results tracking
    all_results = []
    successful_uploads = []
    failed_uploads = []
    
    total_files = len(file_data)
    processed_files = 0
    
    # Process each file
    for file_name, data in file_data.items():
        status_text.text(f"Processing {file_name}...")
        
        sheets = data['sheets']
        file_results = {
            'original_filename': file_name,
            'file_type': data['validation']['file_type'],
            'file_size_mb': data['validation']['size_mb'],
            'total_rows': sum(len(df) for df in sheets.values()),
            'total_columns': sum(len(df.columns) for df in sheets.values()),
            'created_sheets': [],
            'success': True,
            'error': '',
            'processing_time': 0
        }
        
        start_time = time.time()
        
        try:
            # Process each sheet in the file
            for sheet_name, df in sheets.items():
                # Format the dataframe
                formatted_df = format_dataframe(df, options)
                
                # Generate sheet name
                full_sheet_name = generate_sheet_name(
                    f"{file_name}_{sheet_name}", 
                    options['naming_convention'], 
                    options['custom_prefix']
                )
                
                # Split large sheets if necessary
                sheet_chunks = split_large_dataframe(
                    formatted_df, 
                    options['max_rows_per_sheet'], 
                    full_sheet_name
                )
                
                # Upload each chunk
                for chunk_df, chunk_name in sheet_chunks:
                    upload_result = upload_to_google_sheets(
                        client, 
                        chunk_df, 
                        chunk_name, 
                        options
                    )
                    
                    if upload_result['success']:
                        file_results['created_sheets'].append(upload_result)
                        successful_uploads.append(upload_result)
                    else:
                        failed_uploads.append(upload_result)
                        file_results['success'] = False
                        file_results['error'] = upload_result['error']
        
        except Exception as e:
            file_results['success'] = False
            file_results['error'] = str(e)
        
        file_results['processing_time'] = time.time() - start_time
        all_results.append(file_results)
        
        # Update progress
        processed_files += 1
        overall_progress.progress(processed_files / total_files)
    
    # Create summary sheet if requested
    if options['create_summary'] and all_results:
        status_text.text("Creating summary sheet...")
        
        try:
            summary_df = create_summary_sheet_data(all_results, options)
            summary_name = generate_sheet_name(
                "Processing_Summary", 
                options['naming_convention'], 
                "Summary_"
            )
            
            summary_result = upload_to_google_sheets(
                client, 
                summary_df, 
                summary_name, 
                options
            )
            
            if summary_result['success']:
                successful_uploads.append(summary_result)
        except Exception as e:
            st.warning(f"Failed to create summary sheet: {str(e)}")
    
    # Display results
    status_text.text("Processing complete!")
    overall_progress.progress(1.0)
    
    # Results summary
    st.markdown("### 📊 Processing Results")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Successful Uploads", len(successful_uploads))
    with col2:
        st.metric("❌ Failed Uploads", len(failed_uploads))
    with col3:
        total_time = sum(result['processing_time'] for result in all_results)
        st.metric("⏱️ Total Time", f"{total_time:.1f}s")
    
    # Display successful uploads
    if successful_uploads:
        st.markdown("""
        <div class="success-box">
            <h4>✅ Successfully Created Google Sheets</h4>
        </div>
        """, unsafe_allow_html=True)
        
        for result in successful_uploads:
            st.markdown(f"""
            <div class="file-preview">
                <h5>📊 {result['name']}</h5>
                <p><strong>Rows:</strong> {result['rows_uploaded']:,} | <strong>Columns:</strong> {result['columns_uploaded']}</p>
                <p><strong>Processing Time:</strong> {result['processing_time']:.1f}s</p>
                <p><strong>Share Status:</strong> {result['share_status']}</p>
                <a href="{result['url']}" target="_blank" class="sheet-link">🔗 Open in Google Sheets</a>
            </div>
            """, unsafe_allow_html=True)
    
    # Display failed uploads
    if failed_uploads:
        st.markdown("""
        <div class="error-box">
            <h4>❌ Failed Uploads</h4>
        </div>
        """, unsafe_allow_html=True)
        
        for result in failed_uploads:
            st.error(f"**{result['name']}**: {result['error']}")
    
    # Cleanup temporary file
    try:
        os.unlink(cred_path)
    except:
        pass

# Show instructions when no credentials are uploaded
else:
    # Show instructions when no credentials are uploaded
    st.markdown("""
    <div class="info-box">
        <h3>🔐 Getting Started</h3>
        <p>To use this application, you need to upload a Google Service Account JSON file:</p>
        <ol>
            <li>Go to <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a></li>
            <li>Create or select a project</li>
            <li>Enable the Google Sheets API and Google Drive API</li>
            <li>Go to IAM & Admin → Service Accounts</li>
            <li>Create a service account or use an existing one</li>
            <li>Generate a JSON key for the service account</li>
            <li>Upload the JSON file using the sidebar</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h3>✨ Features</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
            <div>
                <h5>📊 File Support</h5>
                <ul>
                    <li>CSV files with intelligent parsing</li>
                    <li>Excel files (.xlsx, .xls)</li>
                    <li>Multi-sheet Excel workbooks</li>
                    <li>Batch processing</li>
                </ul>
            </div>
            <div>
                <h5>🎨 Processing Options</h5>
                <ul>
                    <li>Auto-resize columns</li>
                    <li>Freeze header rows</li>
                    <li>Remove empty rows/columns</li>
                    <li>Add processing timestamps</li>
                </ul>
            </div>
            <div>
                <h5>📧 Sharing & Organization</h5>
                <ul>
                    <li>Auto-share with specified emails</li>
                    <li>Custom naming conventions</li>
                    <li>Processing summary sheets</li>
                    <li>Configurable permissions</li>
                </ul>
            </div>
            <div>
                <h5>⚡ Performance</h5>
                <ul>
                    <li>Large file support (up to 50MB)</li>
                    <li>Batch upload for speed</li>
                    <li>Progress tracking</li>
                    <li>Error recovery</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
