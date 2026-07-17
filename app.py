import streamlit as st
import pandas as pd
from datetime import datetime
import os
import urllib.parse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="Tesla Laser 4P Management Pro", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    
    .stApp {
        background-color: #111418 !important;
        color: #ffffff !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #0b0d10 !important;
        border-right: 3px solid #61afef !important;
    }
    
    div[data-testid="stForm"], .stAlert {
        background-color: #1c2026 !important;
        border: 2px solid #2d333f !important;
        border-radius: 8px !important;
        padding: 20px !important;
    }
    
    label, p, span, .stMetric div {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    h1, h2, h3, h4 {
        color: #61afef !important;
        font-weight: 800 !important;
    }
    
    input, select, textarea, div[data-baseweb="input"] input, div[data-baseweb="select"] {
        background-color: #111418 !important;
        color: #ffffff !important;
        border: 2px solid #3e4452 !important;
        font-size: 14px !important;
    }
    
    input:focus, select:focus, textarea:focus {
        border-color: #61afef !important;
    }

    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }
    
    button, 
    .stButton > button, 
    [data-testid="stFormSubmitButton"] button, 
    [data-testid="stFormSubmitButton"] > button {
        background-color: #2c313c !important;
        color: #ffffff !important;
        border: 2px solid #61afef !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 8px 16px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        display: inline-block;
        width: auto;
    }
    
    button:hover, 
    .stButton > button:hover, 
    [data-testid="stFormSubmitButton"] button:hover {
        background-color: #ff9900 !important;
        color: #000000 !important;
        border-color: #ffaa00 !important;
        cursor: pointer;
    }
    
    .inline-success {
        background-color: #1b2e1e !important;
        color: #7cfc00 !important;
        padding: 12px !important;
        border-radius: 6px;
        border: 2px solid #98c379 !important;
        margin-top: 15px !important;
        font-weight: bold !important;
        text-align: center !important;
        font-size: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. LOCAL DATA FILE WIRING
# ==========================================
OFFICE_FILE = "office_expenses.csv"
HOME_FILE = "home_expenses.csv"
OP_PARTY_MASTER_FILE = "op_party_master.csv"
DAILY_WORK_FILE = "daily_work_entries.csv"
OP_UPAD_FILE = "operator_upad_entries.csv"

# ==========================================
# 3. INTERACTIVE SESSION CONTROLLERS & EDIT STATE
# ==========================================
for key in ['msg_off_inc', 'msg_off_exp', 'msg_hm_inc', 'msg_hm_exp', 'msg_work', 'msg_upad']:
    if key not in st.session_state: 
        st.session_state[key] = ""

if 'sel_op' not in st.session_state: st.session_state.sel_op = ""
if 'sel_pt' not in st.session_state: st.session_state.sel_pt = ""
if 'sel_wt' not in st.session_state: st.session_state.sel_wt = "PC"
if 'sel_u_op' not in st.session_state: st.session_state.sel_u_op = ""
if 'sel_pm' not in st.session_state: st.session_state.sel_pm = "Cash"

# Advanced Edit Systems State
if 'edit_id' not in st.session_state: st.session_state.edit_id = None
if 'edit_section' not in st.session_state: st.session_state.edit_section = ""
if 'edit_data' not in st.session_state: st.session_state.edit_data = {}

# RATE LOCK SYSTEM INITIALIZATION
if 'locked_op_rate_pc' not in st.session_state: st.session_state.locked_op_rate_pc = 0.0
if 'locked_party_rate_pc' not in st.session_state: st.session_state.locked_party_rate_pc = 0.0

if 'locked_op_rate_20_up' not in st.session_state: st.session_state.locked_op_rate_20_up = 0.0
if 'locked_op_rate_1_up' not in st.session_state: st.session_state.locked_op_rate_1_up = 0.0
if 'locked_party_rate_carat' not in st.session_state: st.session_state.locked_party_rate_carat = 0.0

if 'locked_op_rate_choki' not in st.session_state: st.session_state.locked_op_rate_choki = 0.0
if 'locked_party_rate_choki' not in st.session_state: st.session_state.locked_party_rate_choki = 0.0

def clear_all_messages():
    st.session_state.msg_off_inc = ""
    st.session_state.msg_off_exp = ""
    st.session_state.msg_hm_inc = ""
    st.session_state.msg_hm_exp = ""
    st.session_state.msg_work = ""
    st.session_state.msg_upad = ""

def cancel_edit():
    st.session_state.edit_id = None
    st.session_state.edit_section = ""
    st.session_state.edit_data = {}

# Dynamic keys setup for resetting form values
if 'form_reset_token' not in st.session_state:
    st.session_state.form_reset_token = 0

def trigger_form_reset():
    st.session_state.form_reset_token += 1

def force_global_reset():
    st.query_params.clear()
    
    keys_to_keep = [
        "logged_in", 
        "user_role", 
        "username", 
        "fix_value",      
        "fixed_rates",     
        "operator_options" 
    ]
    
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep: 
            del st.session_state[key]
            
    st.rerun()
    
    if "menu" in st.session_state:
        st.session_state["menu"] = "Dashboard"
        
    st.query_params.clear()
    
    st.rerun()

# ==========================================
# 4. STORAGE DATA HANDLING SYSTEM
# ==========================================
def load_data(file_path, base_columns):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            for col in base_columns:
                if col not in df.columns:
                    df[col] = 0.0 if col in ["Amount", "Pcs", "Pcs_20_Up", "Pcs_1_Up", "Carat_20_Up", "Carat_1_Up", "Choki"] else ""
            return df
        except:
            return pd.DataFrame(columns=base_columns)
    return pd.DataFrame(columns=base_columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# Load Master Data
df_master = load_data(OP_PARTY_MASTER_FILE, ["Type", "Name"])
df_office = load_data(OFFICE_FILE, ["Date", "Type", "Name", "Amount", "Phone", "Remark"])
df_home = load_data(HOME_FILE, ["Date", "Type", "Name", "Amount", "Phone", "Remark"])

work_columns_template = [
    "Date", "Operator", "Party", "Work Type", "Pcs", 
    "Pcs_20_Up", "Pcs_1_Up", "Carat_20_Up", "Carat_1_Up", "Choki", 
    "Op_Rate_20_Up", "Op_Rate_1_Up",
    "Operator Rate", "Party Rate", "Operator Amount", "Party Amount"
]
df_work = load_data(DAILY_WORK_FILE, work_columns_template)
df_upad = load_data(OP_UPAD_FILE, ["Date", "Operator", "Amount", "Payment Mode", "Remark"])

# Sanitize Types & Floating values
numerical_fields = ["Pcs", "Pcs_20_Up", "Pcs_1_Up", "Carat_20_Up", "Carat_1_Up", "Choki", "Op_Rate_20_Up", "Op_Rate_1_Up", "Operator Rate", "Party Rate", "Operator Amount", "Party Amount"]
for column_name in numerical_fields:
    if column_name in df_work.columns:
        df_work[column_name] = pd.to_numeric(df_work[column_name], errors='coerce').fillna(0.0)
df_office["Amount"] = pd.to_numeric(df_office["Amount"], errors='coerce').fillna(0.0)
df_home["Amount"] = pd.to_numeric(df_home["Amount"], errors='coerce').fillna(0.0)
df_upad["Amount"] = pd.to_numeric(df_upad["Amount"], errors='coerce').fillna(0.0)

# ==========================================
# 5. TECHNICAL UTILITIES ENGINE
# ==========================================
def build_whatsapp_url(phone_num, body_text):
    if not phone_num:
        return ""
    clean_phone = "".join(filter(str.isdigit, str(phone_num)))
    if len(clean_phone) == 10:
        clean_phone = "91" + clean_phone
    return f"https://wa.me/{clean_phone}?text={urllib.parse.quote(body_text)}"

def generate_pdf_document(dataframe_source, document_heading):
    byte_stream = io.BytesIO()
    pdf_canvas = SimpleDocTemplate(byte_stream, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=30, margin_bottom=30)
    story_flow = []
    
    style_sheet = getSampleStyleSheet()
    header_style = ParagraphStyle('HeadStyle', parent=style_sheet['Heading1'], fontName='Helvetica-Bold', fontSize=15, textColor=colors.HexColor('#61afef'), spaceAfter=12, alignment=1)
    cell_data_style = ParagraphStyle('CellData', parent=style_sheet['Normal'], fontName='Helvetica', fontSize=8, spaceAfter=2)
    th_style = ParagraphStyle('TableHead', parent=style_sheet['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)
    
    story_flow.append(Paragraph(document_heading, header_style))
    story_flow.append(Spacer(1, 10))
    
    headers = dataframe_source.columns.tolist()
    matrix_data = [[Paragraph(str(h), th_style) for h in headers]]
    
    for _, row in dataframe_source.iterrows():
        matrix_data.append([Paragraph(str(row[col]), cell_data_style) for col in headers])
        
    render_table = Table(matrix_data, repeatRows=1)
    render_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1c2026')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#3e4452')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    
    story_flow.append(render_table)
    pdf_canvas.build(story_flow)
    byte_stream.seek(0)
    return byte_stream

def native_contact_picker_js(identifier_tag):
    script_block = f"""
    <div style="font-family: sans-serif; margin-bottom: 4px;">
        <button id="btn_{identifier_tag}" style="background-color: #21252b; color: #61afef; border: 1px solid #61afef; padding: 6px 10px; font-weight: bold; border-radius: 4px; cursor: pointer; width: 100%;">
            📇 Phonebook Select
        </button>
        <p id="lbl_{identifier_tag}" style="font-size: 11px; color: #ff9900; margin-top: 4px; text-align:center; font-weight: bold;"></p>
    </div>
    <script>
        document.getElementById('btn_{identifier_tag}').addEventListener('click', async () => {{
            const outputLabel = document.getElementById('lbl_{identifier_tag}');
            if (!('contacts' in navigator)) {{
                outputLabel.innerText = "Direct type number niche box me karein."; return;
            }}
            try {{
                const selected = await navigator.contacts.select(['tel'], {{ multiple: false }});
                if (selected.length > 0 && selected[0].tel.length > 0) {{
                    outputLabel.innerText = "Copy this number: " + selected[0].tel[0].replace(/[^\\d]/g, '');
                }}
            }} catch (e) {{ }}
        }});
    </script>
    """
    components.html(script_block, height=45)

# ==========================================
# 6. SIDEBAR NAVIGATION SYSTEM
# ==========================================
st.sidebar.markdown("<h2 style='color:#61afef; text-align: center; margin-bottom:0;'>💎 Tesla Laser Pro</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-size:11px; color:#ff9900;'>Industrial 4P Engine Panel</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

if st.sidebar.button("🏠 Back to Main Dashboard", key="global_dashboard_reset_trigger", use_container_width=True):
    force_global_reset()

st.sidebar.markdown("---")
app_route = st.sidebar.radio(
    "Navigation System Menu:",
    ["(1) Office Expense Master", "(2) Home Expense Master", "(3) Operator Ledger & Production Desk"],
    on_change=clear_all_messages
)

if app_route == "(1) Office Expense Master":
    st.sidebar.markdown("<div style='background-color:#1c2026; padding:10px; border-radius:5px; border-left:4px solid #ff9900; text-align:center; font-weight:bold;'>📍 Location: Office Desk Active</div>", unsafe_allow_html=True)
elif app_route == "(2) Home Expense Master":
    st.sidebar.markdown("<div style='background-color:#1c2026; padding:10px; border-radius:5px; border-left:4px solid #7cfc00; text-align:center; font-weight:bold;'>📍 Location: Home Desk Active</div>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<div style='background-color:#1c2026; padding:10px; border-radius:5px; border-left:4px solid #61afef; text-align:center; font-weight:bold;'>📍 Location: Diamond Production Active</div>", unsafe_allow_html=True)

# SIDEBAR: DEFAULT LOCKED RATES PANEL
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#ff9900; text-align:center; margin-bottom:10px;'>🔒 Set & Lock Default Rates</h3>", unsafe_allow_html=True)

with st.sidebar.expander("⚙️ Configure Fixed Rates", expanded=False):
    st.markdown("**1. Piece (PC) Mode Rates**")
    locked_op_pc = st.number_input("Operator Rate (PC):", min_value=0.0, value=st.session_state.locked_op_rate_pc, step=0.5, key="sb_op_pc")
    locked_party_pc = st.number_input("Party Rate (PC):", min_value=0.0, value=st.session_state.locked_party_rate_pc, step=0.5, key="sb_party_pc")
    
    st.markdown("---")
    st.markdown("**2. Carat Mode Rates**")
    locked_op_20 = st.number_input("+20 Up Operator Rate:", min_value=0.0, value=st.session_state.locked_op_rate_20_up, step=0.5, key="sb_op_20")
    locked_op_1 = st.number_input("+1 Operator Rate:", min_value=0.0, value=st.session_state.locked_op_rate_1_up, step=0.5, key="sb_op_1")
    locked_party_carat = st.number_input("Party Consolidated Rate:", min_value=0.0, value=st.session_state.locked_party_rate_carat, step=0.5, key="sb_party_carat")
    
    st.markdown("---")
    st.markdown("**3. Choki Mode Rates**")
    locked_op_choki = st.number_input("Operator Rate (Choki):", min_value=0.0, value=st.session_state.locked_op_rate_choki, step=0.5, key="sb_op_choki")
    locked_party_choki = st.number_input("Party Rate (Choki):", min_value=0.0, value=st.session_state.locked_party_rate_choki, step=0.5, key="sb_party_choki")
    
    if st.button("🔒 Save & Lock All Rates", use_container_width=True):
        st.session_state.locked_op_rate_pc = locked_op_pc
        st.session_state.locked_party_rate_pc = locked_party_pc
        st.session_state.locked_op_rate_20_up = locked_op_20
        st.session_state.locked_op_rate_1_up = locked_op_1
        st.session_state.locked_party_rate_carat = locked_party_carat
        st.session_state.locked_op_rate_choki = locked_op_choki
        st.session_state.locked_party_rate_choki = locked_party_choki
        st.toast("✅ Sabhi Rates Lock Kar Diye Gaye Hain!", icon="🔑")

# ==========================================
# MAIN DASHBOARD QUICK TOP LINK
# ==========================================
top_nav_col1, top_nav_col2 = st.columns([8, 2])
with top_nav_col2:
    if st.button("🏠 Main Dashboard Screen", key="top_dashboard_universal_home_btn", use_container_width=True):
        force_global_reset()

# ==========================================
# 7. SECTION 1: OFFICE EXPENSE ACCOUNTING
# ==========================================
if app_route == "(1) Office Expense Master":
    st.header("🏢 Office Records & Accounting Ledger")
    
    is_editing_office = (st.session_state.edit_section == "Office" and st.session_state.edit_id is not None)
    edit_office_row = st.session_state.edit_data if is_editing_office else {}
    Token = st.session_state.form_reset_token
    
    col_income, col_expense = st.columns(2)
    
    with col_income:
        st.subheader("💰 Cash Inward (Paisa Aaya)")
        native_contact_picker_js("off_in")
        with st.form("office_income_capture_form"):
            in_date = st.date_input("Date:", value=datetime.strptime(edit_office_row["Date"], "%Y-%m-%d").date() if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else datetime.today().date(), key=f"off_in_date_{Token}")
            in_name = st.text_input("Source Name / Party:", value=edit_office_row.get("Name", "") if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else "", key=f"off_in_name_{Token}")
            
            in_amount = st.number_input("Collected Amount (₹):", min_value=0.0, step=50.0, value=float(edit_office_row.get("Amount")) if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else None, placeholder="Type amount directly...", key=f"off_in_amt_{Token}")
            in_phone = st.text_input("WhatsApp Number (10 Digits):", value=str(edit_office_row.get("Phone", "")) if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else "", key=f"off_in_ph_{Token}")
            remark_default = edit_office_row.get("Remark", "") if (is_editing_office and edit_office_row) else ""
            in_remark = st.text_area("Entry Remarks / Context:", value=remark_default)           
            sub_label = "Update Cash Inward" if is_editing_office else "Save Cash Inward"
            if st.form_submit_button(sub_label):
                clear_all_messages()
                if not in_name or in_amount is None:
                    st.error("Nam aur Amount bharna mandatory hai!")
                else:
                    new_log = {"Date": str(in_date), "Type": "Income (Aaya)", "Name": in_name.strip(), "Amount": float(in_amount), "Phone": str(in_phone).strip(), "Remark": in_remark.strip()}
                    if is_editing_office and edit_office_row.get("Type") == "Income (Aaya)":
                        df_office.iloc[st.session_state.edit_id] = new_log
                        cancel_edit()
                        st.session_state.msg_off_inc = "✔ Entry Updated Successfully!"
                    else:
                        df_office = pd.concat([df_office, pd.DataFrame([new_log])], ignore_index=True)
                        st.session_state.msg_off_inc = "✔ Income Entry Tracked Successfully!"
                    save_data(df_office, OFFICE_FILE)
                    trigger_form_reset()
                    st.rerun()
            
            if is_editing_office and st.form_submit_button("Cancel Edit", key="cancel_in_edit"):
                cancel_edit()
                trigger_form_reset()
                st.rerun()
            
            if st.session_state.msg_off_inc:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_off_inc}</div>', unsafe_allow_html=True)

    with col_expense:
        st.subheader("💸 Cash Outward (Paisa Gaya)")
        native_contact_picker_js("off_exp")
        with st.form("office_expense_capture_form"):
            out_date = st.date_input("Date:", value=datetime.strptime(edit_office_row["Date"], "%Y-%m-%d").date() if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else datetime.today().date(), key=f"off_exp_date_{Token}")
            out_name = st.text_input("Recipient / Vendor Name:", value=edit_office_row.get("Name", "") if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else "", key=f"off_exp_name_{Token}")
            
            out_amount = st.number_input("Paid Amount (₹):", min_value=0.0, step=50.0, value=float(edit_office_row.get("Amount")) if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else None, placeholder="Type amount directly...", key=f"off_exp_amt_{Token}")
            out_phone = st.text_input("WhatsApp Number:", value=str(edit_office_row.get("Phone", "")) if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else "", key=f"off_exp_ph_{Token}")
            
            default_remark = edit_office_row.get("Remark", "") if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else ""
            out_remark = st.text_area("Purpose / Remark:", value=default_remark, key=f"off_exp_rem_{Token}")
            
            sub_label_exp = "Update Cash Outward" if is_editing_office else "Save Cash Outward"
            if st.form_submit_button(sub_label_exp):
                clear_all_messages()
                if not out_name or out_amount is None:
                    st.error("Nam aur Amount fields blank nahi chod sakte!")
                else:
                    new_log = {
                        "Date": str(out_date), 
                        "Type": "Expense (Gaya)", 
                        "Name": out_name.strip(), 
                        "Amount": float(out_amount),
                        "Phone": str(out_phone).strip(),
                        "Remark": out_remark.strip()
                    }
                    if is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)":
                        df_office.iloc[st.session_state.edit_id] = new_log
                        cancel_edit()
                        st.session_state.msg_off_exp = "✓ Entry Updated Successfully!"
                    else:
                        df_office = pd.concat([df_office, pd.DataFrame([new_log])], ignore_index=True)
                        st.session_state.msg_off_exp = "✔ Expense Entry Tracked Successfully!"
                    save_data(df_office, OFFICE_FILE)
                    trigger_form_reset()
                    st.rerun()
            
            if is_editing_office and st.form_submit_button("Cancel Edit", key="cancel_out_edit"):
                cancel_edit()
                trigger_form_reset()
                st.rerun()

            if st.session_state.msg_off_exp:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_off_exp}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Filtered Statements Log Sheet")
    
    if not df_office.empty:
        df_office_show = df_office.copy()
        
        for idx, row in df_office_show.iterrows():
            with st.container():
                r_col1, r_col2, r_col3, r_col4, r_col5, r_col6, r_col7 = st.columns([1.5, 2.5, 1.5, 2.5, 1.5, 1.0, 1.0])
                
                r_col1.markdown(f"🗓 `{row['Date']}`")
                badge = f"🟢 <span style='color:#7cfc00;'>{row['Type']}</span>" if "Income" in row['Type'] else f"🔴 <span style='color:#ff5555;'>{row['Type']}</span>"
                r_col2.markdown(f"{badge} **{row['Name']}**", unsafe_allow_html=True)
                r_col3.markdown(f"💰 **₹{row['Amount']:.2f}**")
                r_col4.markdown(f"📝 <span style='color:#a6b2c6;'>{row['Remark']}</span>", unsafe_allow_html=True)
                
                wa_msg_body = f"Tesla Laser Office Log:\nDate: {row['Date']}\nType: {row['Type']}\nParty: {row['Name']}\nAmount: ₹{row['Amount']}\nRemark: {row['Remark']}"
                wa_endpoint = build_whatsapp_url(row['Phone'], wa_msg_body)
                if row['Phone'] and str(row['Phone']).strip() != "":
                    r_col5.markdown(f"<a href='{wa_endpoint}' target='_blank'><button style='background-color:#25D366; color:white; border:none; border-radius:4px; font-weight:bold; padding:2px 8px; width:100%;'>💬 Send WA</button></a>", unsafe_allow_html=True)
                else:
                    r_col5.markdown("<span style='color:grey; font-size:12px;'>No Phone</span>", unsafe_allow_html=True)
                
                if r_col6.button("✏️ Edit", key=f"edit_off_row_{idx}"):
                    st.session_state.edit_id = idx
                    st.session_state.edit_section = "Office"
                    st.session_state.edit_data = row.to_dict()
                    st.rerun()
                
                if r_col7.button("❌ Delete", key=f"del_off_row_{idx}"):
                    clear_all_messages()
                    df_office = df_office.drop(idx).reset_index(drop=True)
                    save_data(df_office, OFFICE_FILE)
                    st.rerun()
                st.markdown("<hr style='margin:4px 0; border-color:#21252b;' />", unsafe_allow_html=True)
        
        st.markdown("#### Document Export Actions")
        pdf_blob = generate_pdf_document(df_office, "Tesla Laser Office Transaction Statement")
        st.download_button("📥 Download Office Statement PDF", data=pdf_blob, file_name=f"Office_Report_{datetime.today().date()}.pdf", mime="application/pdf")
    else:
        st.warning("Abhi tak data storage me koi transactions record nahi kiye gaye hain.")

# ==========================================
# 8. SECTION 2: HOME EXPENSE ACCOUNTING
# ==========================================
elif app_route == "(2) Home Expense Master":
    st.header("🏡 Home Personal Accounting Desk")
    
    is_editing_home = (st.session_state.edit_section == "Home" and st.session_state.edit_id is not None)
    edit_home_row = st.session_state.edit_data if is_editing_home else {}
    Token = st.session_state.form_reset_token
    
    col_hm_inc, col_hm_exp = st.columns(2)
    
    with col_hm_inc:
        st.subheader("💰 Inward Streams (Ghar me Paisa Aaya)")
        with st.form("home_income_form"):
            h_in_date = st.date_input("Date:", value=datetime.strptime(edit_home_row["Date"], "%Y-%m-%d").date() if (is_editing_home and edit_home_row.get("Type") == "Income (Aaya)") else datetime.today().date(), key=f"hm_in_date_{Token}")
            h_in_name = st.text_input("Source Name:", value=edit_home_row.get("Name", "") if (is_editing_home and edit_home_row.get("Type") == "Income (Aaya)") else "", key=f"hm_in_name_{Token}")
            
            h_in_amount = st.number_input("Amount (₹):", min_value=0.0, step=100.0, value=float(edit_home_row.get("Amount")) if (is_editing_home and edit_home_row.get("Type") == "Income (Aaya)") else None, placeholder="Type amount directly...", key=f"hm_in_amt_{Token}")
            h_in_phone = st.text_input("Phone Reference:", value=str(edit_home_row.get("Phone", "")) if (is_editing_home and edit_home_row.get("Type") == "Income (Aaya)") else "", key=f"hm_in_ph_{Token}")
            h_in_remark = st.text_area("Notes:", value=edit_home_row.get("Remark", "") if (is_editing_home and edit_home_row.get("Type") == "Income (Aaya)") else "", key=f"hm_in_rem_{Token}")
            
            sub_label_hi = "Update Home Inward" if is_editing_home else "Commit Home Inward Record"
            if st.form_submit_button(sub_label_hi):
                clear_all_messages()
                if not h_in_name or h_in_amount is None:
                    st.error("Mandatory entries complete karein!")
                else:
                    new_record = {"Date": str(h_in_date), "Type": "Income (Aaya)", "Name": h_in_name.strip(), "Amount": float(h_in_amount), "Phone": str(h_in_phone).strip(), "Remark": h_in_remark.strip()}
                    if is_editing_home and edit_home_row.get("Type") == "Income (Aaya)":
                        df_home.iloc[st.session_state.edit_id] = new_record
                        cancel_edit()
                        st.session_state.msg_hm_inc = "✔ Entry Updated Successfully!"
                    else:
                        df_home = pd.concat([df_home, pd.DataFrame([new_record])], ignore_index=True)
                        st.session_state.msg_hm_inc = "✔ Home Income Logged Successfully!"
                    save_data(df_home, HOME_FILE)
                    trigger_form_reset()
                    st.rerun()
            
            if is_editing_home and st.form_submit_button("Cancel Edit", key="cancel_hm_in_edit"):
                cancel_edit()
                trigger_form_reset()
                st.rerun()
            
            if st.session_state.msg_hm_inc:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_hm_inc}</div>', unsafe_allow_html=True)

    with col_hm_exp:
        st.subheader("💸 Household Expenses (Kharcha)")
        with st.form("home_expense_form"):
            h_out_date = st.date_input("Date:", value=datetime.strptime(edit_home_row["Date"], "%Y-%m-%d").date() if (is_editing_home and edit_home_row.get("Type") == "Expense (Gaya)") else datetime.today().date(), key=f"hm_exp_date_{Token}")
            h_out_name = st.text_input("Expense Title / Context:", value=edit_home_row.get("Name", "") if (is_editing_home and edit_home_row.get("Type") == "Expense (Gaya)") else "", key=f"hm_exp_name_{Token}")
            
            h_out_amount = st.number_input("Spent Amount (₹):", min_value=0.0, step=50.0, value=float(edit_home_row.get("Amount")) if (is_editing_home and edit_home_row.get("Type") == "Expense (Gaya)") else None, placeholder="Type amount directly...", key=f"hm_exp_amt_{Token}")
            h_out_phone = st.text_input("Phone:", value=str(edit_home_row.get("Phone", "")) if (is_editing_home and edit_home_row.get("Type") == "Expense (Gaya)") else "", key=f"hm_exp_ph_{Token}")
            h_out_remark = st.text_area("Detail Description:", value=edit_home_row.get("Remark", "") if (is_editing_home and edit_home_row.get("Type") == "Expense (Gaya)") else "", key=f"hm_exp_rem_{Token}")
            
            sub_label_he = "Update Home Expense" if is_editing_home else "Commit Home Outward Record"
            if st.form_submit_button(sub_label_he):
                clear_all_messages()
                if not h_out_name or h_out_amount is None:
                    st.error("Data inputs verified empty!")
                else:
                    new_record = {"Date": str(h_out_date), "Type": "Expense (Gaya)", "Name": h_out_name.strip(), "Amount": float(h_out_amount), "Phone": str(h_out_phone).strip(), "Remark": h_out_remark.strip()}
                    if is_editing_home and edit_home_row.get("Type") == "Expense (Gaya)":
                        df_home.iloc[st.session_state.edit_id] = new_record
                        cancel_edit()
                        st.session_state.msg_hm_exp = "✔ Entry Updated Successfully!"
                    else:
                        df_home = pd.concat([df_home, pd.DataFrame([new_record])], ignore_index=True)
                        st.session_state.msg_hm_exp = "✔ Home Expense Logged Successfully!"
                    save_data(df_home, HOME_FILE)
                    trigger_form_reset()
                    st.rerun()
            
            if is_editing_home and st.form_submit_button("Cancel Edit", key="cancel_hm_exp_edit"):
                cancel_edit()
                trigger_form_reset()
                st.rerun()

            if st.session_state.msg_hm_exp:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_hm_exp}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Domestic Ledger History View")
    
    if not df_home.empty:
        df_home_show = df_home.copy()
        
        for idx, row in df_home_show.iterrows():
            with st.container():
                hr_c1, hr_c2, hr_c3, hr_c4, hr_c5, hr_c6 = st.columns([1.5, 3.0, 1.5, 3.0, 1.0, 1.0])
                hr_c1.write(f"📅 `{row['Date']}`")
                label_color = "#7cfc00" if "Income" in row['Type'] else "#ff5555"
                hr_c2.markdown(f"<span style='color:{label_color}; font-weight:bold;'>[{row['Type']}]</span> {row['Name']}", unsafe_allow_html=True)
                hr_c3.markdown(f"₹ **{row['Amount']:.2f}**")
                hr_c4.markdown(f"<span style='color:#8a93a5;'>{row['Remark']}</span>", unsafe_allow_html=True)
                
                if hr_c5.button("✏️ Edit", key=f"edit_hm_row_{idx}"):
                    st.session_state.edit_id = idx
                    st.session_state.edit_section = "Home"
                    st.session_state.edit_data = row.to_dict()
                    st.rerun()
                
                if hr_c6.button("❌ Delete", key=f"del_hm_row_{idx}"):
                    clear_all_messages()
                    df_home = df_home.drop(idx).reset_index(drop=True)
                    save_data(df_home, HOME_FILE)
                    st.rerun()
                st.markdown("<hr style='margin:3px 0; border-color:#21252b;' />", unsafe_allow_html=True)
        
        pdf_blob_h = generate_pdf_document(df_home, "Home Personal Ledger Report")
        st.download_button("📥 Download Home Statements PDF", data=pdf_blob_h, file_name="Home_Ledger_Statements.pdf", mime="application/pdf")

# ==========================================
# 9. SECTION 3: OPERATOR & PARTY DIAMOND DESK
# ==========================================
else:
    st.header("👷 Diamond Laser 4P Production Terminal")
    
    operator_options = df_master[df_master["Type"] == "Operator"]["Name"].tolist()
    party_options = df_master[df_master["Type"] == "Party"]["Name"].tolist()
    Token = st.session_state.form_reset_token
    
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.markdown("### 🛠 Operator Registration Node")
        with st.form("master_operator_management_form"):
            input_op_name = st.text_input("Enter New Operator Name:", key=f"m_op_name_{Token}")
            execution_method = st.selectbox("Action Vector:", ["Register/Add", "Unregister/Remove"], key=f"m_op_act_{Token}")
            
            if st.form_submit_button("Commit Master Action"):
                clear_all_messages()
                cleaned_name = input_op_name.strip()
                if cleaned_name:
                    if execution_method == "Register/Add":
                        if not ((df_master['Type'] == 'Operator') & (df_master['Name'] == cleaned_name)).any():
                            df_master = pd.concat([df_master, pd.DataFrame([{"Type": "Operator", "Name": cleaned_name}])], ignore_index=True)
                            save_data(df_master, OP_PARTY_MASTER_FILE)
                            trigger_form_reset()
                            st.rerun()
                    else:
                        df_master = df_master[~((df_master['Type'] == 'Operator') & (df_master['Name'] == cleaned_name))]
                        save_data(df_master, OP_PARTY_MASTER_FILE)
                        trigger_form_reset()
                        st.rerun()
                        
    with m_col2:
        st.markdown("### 🏢 Client Party Registration Node")
        with st.form("master_party_management_form"):
            input_pt_name = st.text_input("Enter New Business Party Name:", key=f"m_pt_name_{Token}")
            execution_method_pt = st.selectbox("Action Vector:", ["Register/Add", "Unregister/Remove"], key=f"m_pt_act_{Token}")
            
            if st.form_submit_button("Commit Client Action"):
                clear_all_messages()
                cleaned_pt_name = input_pt_name.strip()
                if cleaned_pt_name:
                    if execution_method_pt == "Register/Add":
                        if not ((df_master['Type'] == 'Party') & (df_master['Name'] == cleaned_pt_name)).any():
                            df_master = pd.concat([df_master, pd.DataFrame([{"Type": "Party", "Name": cleaned_pt_name}])], ignore_index=True)
                            save_data(df_master, OP_PARTY_MASTER_FILE)
                            trigger_form_reset()
                            st.rerun()
                    else:
                        df_master = df_master[~((df_master['Type'] == 'Party') & (df_master['Name'] == cleaned_pt_name))]
                        save_data(df_master, OP_PARTY_MASTER_FILE)
                        trigger_form_reset()
                        st.rerun()

    st.markdown("---")
    
    is_editing_work = (st.session_state.edit_section == "Work" and st.session_state.edit_id is not None)
    edit_work_row = st.session_state.edit_data if is_editing_work else {}
    
    is_editing_upad = (st.session_state.edit_section == "Upad" and st.session_state.edit_id is not None)
    edit_upad_row = st.session_state.edit_data if is_editing_upad else {}
    
    input_column, upad_column = st.columns(2)
    
    with input_column:
        st.markdown("### 📝 Daily Diamond Production Log")
        
        if is_editing_work:
            st.session_state.sel_op = edit_work_row.get("Operator", "")
            st.session_state.sel_wt = edit_work_row.get("Work Type", "PC")
        
        st.markdown("<p style='margin-bottom:2px; color:#ff9900;'>Select Working Operator:</p>", unsafe_allow_html=True)
        if operator_options:
            op_grid_cols = st.columns(max(len(operator_options), 1))
            for index_op, op_title in enumerate(operator_options):
                is_selected = st.session_state.sel_op == op_title
                button_label = f"⭐ {op_title}" if is_selected else str(op_title)
                
                if op_grid_cols[index_op].button(button_label, key=f"grid_op_select_{op_title}"):
                    st.session_state.sel_op = op_title
                    clear_all_messages()
                    st.rerun()
        else:
            st.error("Upar master register me operator add karein pehle!")
            
        st.markdown("<p style='margin-top:8px; margin-bottom:2px; color:#61afef;'>Select Active Work Parameters Class:</p>", unsafe_allow_html=True)
        wt_c1, wt_c2, wt_c3 = st.columns(3)
        
        lbl_pc = "🔴 PIECE (PC) ACTIVE" if st.session_state.sel_wt == "PC" else "Piece (PC)"
        if wt_c1.button(lbl_pc, key="btn_wt_pc_select"):
            st.session_state.sel_wt = "PC"
            clear_all_messages()
            st.rerun()
            
        lbl_ct = "🟢 CARAT ACTIVE" if st.session_state.sel_wt == "Carat" else "Carat"
        if wt_c2.button(lbl_ct, key="btn_wt_ct_select"):
            st.session_state.sel_wt = "Carat"
            clear_all_messages()
            st.rerun()
            
        lbl_ck = "🔵 CHOKI ACTIVE" if st.session_state.sel_wt == "Choki" else "Choki"
        if wt_c3.button(lbl_ck, key="btn_wt_ck_select"):
            st.session_state.sel_wt = "Choki"
            clear_all_messages()
            st.rerun()

        st.info(f"⚡ Current Configuration -> Operator: **{st.session_state.sel_op}** | Batch Profile Mode: **{st.session_state.sel_wt}**")
        
        with st.form("production_main_data_capture_form"):
            prod_date = st.date_input("Processing Entry Date:", value=datetime.strptime(edit_work_row["Date"], "%Y-%m-%d").date() if is_editing_work else datetime.today().date(), key=f"prod_date_{Token}")
            
            default_party_idx = 0
            if is_editing_work and edit_work_row.get("Party") in party_options:
                default_party_idx = party_options.index(edit_work_row.get("Party"))
            prod_party = st.selectbox("Select Target Client Party Account:", party_options, index=default_party_idx, key=f"prod_party_{Token}")
            
            pcs_count = 0
            pcs_20_up = 0
            pcs_1_up = 0
            carat_20_weight = 0.0
            carat_1_weight = 0.0
            choki_count = 0
            
            generic_op_rate = 0.0
            unified_party_rate = 0.0
            op_rate_20_up = 0.0
            op_rate_1_up = 0.0

            if st.session_state.sel_wt == "PC":
                pcs_count = st.number_input("Total Processed PC Count:", min_value=0, value=int(edit_work_row.get("Pcs")) if is_editing_work else None, placeholder="Type count...", step=1, key=f"prod_pcs_{Token}")
                
                default_op_rate_pc = float(edit_work_row.get("Operator Rate", st.session_state.locked_op_rate_pc)) if is_editing_work else st.session_state.locked_op_rate_pc
                default_party_rate_pc = float(edit_work_row.get("Party Rate", st.session_state.locked_party_rate_pc)) if is_editing_work else st.session_state.locked_party_rate_pc
                
                generic_op_rate = st.number_input("Operator Component Rate (per PC):", min_value=0.0, value=default_op_rate_pc, step=0.1, key=f"prod_op_rate_pc_{Token}")
                unified_party_rate = st.number_input("Party Billing Rate (per PC):", min_value=0.0, value=default_party_rate_pc, step=0.1, key=f"prod_pt_rate_pc_{Token}")
                
            elif st.session_state.sel_wt == "Carat":
                st.markdown("<p style='color:#ff9900; font-weight:bold; margin-bottom: 2px;'>Carat Metrics & Separated PC Boxes:</p>", unsafe_allow_html=True)
                
                pc_col1, pc_col2 = st.columns(2)
                with pc_col1:
                    pcs_20_up = st.number_input("+20 Up Pcs Count:", min_value=0, value=int(edit_work_row.get("Pcs_20_Up")) if is_editing_work else None, placeholder="Type count...", step=1, key=f"prod_pcs20_{Token}")
                with pc_col2:
                    pcs_1_up = st.number_input("+1 Carat Pcs Count:", min_value=0, value=int(edit_work_row.get("Pcs_1_Up")) if is_editing_work else None, placeholder="Type count...", step=1, key=f"prod_pcs1_{Token}")
                
                wt_col1, wt_col2 = st.columns(2)
                with wt_col1:
                    carat_20_weight = st.number_input("+20 Up Raw Carat Weight Value:", min_value=0.0, value=float(edit_work_row.get("Carat_20_Up")) if is_editing_work else None, step=0.01, format="%.2f", placeholder="Type weight...", key=f"prod_carat20_{Token}")
                    default_op_rate_20_up = float(edit_work_row.get("Op_Rate_20_Up", st.session_state.locked_op_rate_20_up)) if is_editing_work else st.session_state.locked_op_rate_20_up
                    op_rate_20_up = st.number_input("+20 Up Operator Pay Rate:", min_value=0.0, value=default_op_rate_20_up, step=0.1, key=f"prod_op_rate20_{Token}")
                with wt_col2:
                    carat_1_weight = st.number_input("+1 Carat Raw Weight Value:", min_value=0.0, value=float(edit_work_row.get("Carat_1_Up")) if is_editing_work else None, step=0.01, format="%.2f", placeholder="Type weight...", key=f"prod_carat1_{Token}")
                    default_op_rate_1_up = float(edit_work_row.get("Op_Rate_1_Up", st.session_state.locked_op_rate_1_up)) if is_editing_work else st.session_state.locked_op_rate_1_up
                    op_rate_1_up = st.number_input("+1 Carat Operator Pay Rate:", min_value=0.0, value=default_op_rate_1_up, step=0.1, key=f"prod_op_rate1_{Token}")
                    
                st.markdown("<p style='color:#7cfc00; font-weight:bold; margin-bottom: 2px;'>Collective Consolidated Party Evaluation:</p>", unsafe_allow_html=True)
                default_party_rate_carat = float(edit_work_row.get("Party Rate", st.session_state.locked_party_rate_carat)) if is_editing_work else st.session_state.locked_party_rate_carat
                unified_party_rate = st.number_input("Consolidated Party Carat Standard Rate:", min_value=0.0, value=default_party_rate_carat, step=0.1, key=f"prod_pt_rate_carat_{Token}")
                
            else:
                choki_count = st.number_input("Total Handled Choki Units:", min_value=0, value=int(edit_work_row.get("Choki")) if is_editing_work else None, placeholder="Type count...", step=1, key=f"prod_choki_{Token}")
                
                default_op_rate_choki = float(edit_work_row.get("Operator Rate", st.session_state.locked_op_rate_choki)) if is_editing_work else st.session_state.locked_op_rate_choki
                default_party_rate_choki = float(edit_work_row.get("Party Rate", st.session_state.locked_party_rate_choki)) if is_editing_work else st.session_state.locked_party_rate_choki
                
                generic_op_rate = st.number_input("Operator Pay Scale (per Choki):", min_value=0.0, value=default_op_rate_choki, step=0.1, key=f"prod_op_rate_choki_{Token}")
                unified_party_rate = st.number_input("Party Collection Scale (per Choki):", min_value=0.0, value=default_party_rate_choki, step=0.1, key=f"prod_pt_rate_choki_{Token}")
                
            btn_label_prod = "Update Production Entry" if is_editing_work else "Commit Production Entry to Records"
            if st.form_submit_button(btn_label_prod):
                clear_all_messages()
                if not st.session_state.sel_op or not prod_party:
                    st.error("Operator aur Party selection absolute mandatory hai!")
                else:
                    safe_pcs_count = pcs_count if pcs_count is not None else 0
                    safe_pcs_20_up = pcs_20_up if pcs_20_up is not None else 0
                    safe_pcs_1_up = pcs_1_up if pcs_1_up is not None else 0
                    safe_carat_20_weight = carat_20_weight if carat_20_weight is not None else 0.0
                    safe_carat_1_weight = carat_1_weight if carat_1_weight is not None else 0.0
                    safe_choki_count = choki_count if choki_count is not None else 0
                    
                    if st.session_state.sel_wt == "PC":
                        calculated_op_amount = float(safe_pcs_count * (generic_op_rate if generic_op_rate else 0.0))
                        calculated_party_amount = float(safe_pcs_count * (unified_party_rate if unified_party_rate else 0.0))
                        final_op_rate_logged = generic_op_rate if generic_op_rate else 0.0
                    elif st.session_state.sel_wt == "Carat":
                        calculated_op_amount = float((safe_carat_20_weight * op_rate_20_up) + (safe_carat_1_weight * op_rate_1_up))
                        calculated_party_amount = float((safe_carat_20_weight + safe_carat_1_weight) * (unified_party_rate if unified_party_rate else 0.0))
                        final_op_rate_logged = 0.0
                        safe_pcs_count = safe_pcs_20_up + safe_pcs_1_up
                    else:
                        calculated_op_amount = float(safe_choki_count * (generic_op_rate if generic_op_rate else 0.0))
                        calculated_party_amount = float(safe_choki_count * (unified_party_rate if unified_party_rate else 0.0))
                        final_op_rate_logged = generic_op_rate if generic_op_rate else 0.0
                        safe_pcs_count = safe_choki_count
                        
                    new_production_row = {
                        "Date": str(prod_date), "Operator": st.session_state.sel_op, "Party": prod_party,
                        "Work Type": st.session_state.sel_wt, "Pcs": int(safe_pcs_count),
                        "Pcs_20_Up": int(safe_pcs_20_up), "Pcs_1_Up": int(safe_pcs_1_up),
                        "Carat_20_Up": float(safe_carat_20_weight), "Carat_1_Up": float(safe_carat_1_weight), "Choki": int(safe_choki_count),
                        "Op_Rate_20_Up": float(op_rate_20_up) if st.session_state.sel_wt == "Carat" else 0.0, 
                        "Op_Rate_1_Up": float(op_rate_1_up) if st.session_state.sel_wt == "Carat" else 0.0, 
                        "Operator Rate": float(final_op_rate_logged), "Party Rate": float(unified_party_rate if unified_party_rate else 0.0),
                        "Operator Amount": float(calculated_op_amount), "Party Amount": float(calculated_party_amount)
                    }
                    if is_editing_work:
                        df_work.iloc[st.session_state.edit_id] = new_production_row
                        cancel_edit()
                        st.session_state.msg_work = "✔ Production Log Entry Updated!"
                    else:
                        df_work = pd.concat([df_work, pd.DataFrame([new_production_row])], ignore_index=True)
                        st.session_state.msg_work = "✔ Daily Production Entry Tracked!"
                    save_data(df_work, DAILY_WORK_FILE)
                    trigger_form_reset()
                    st.rerun()
            
            if is_editing_work and st.form_submit_button("Cancel Edit Mode", key="cancel_prod_edit"):
                cancel_edit()
                trigger_form_reset()
                st.rerun()
            
            if st.session_state.msg_work:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_work}</div>', unsafe_allow_html=True)

    with upad_column:
        st.markdown("### 💸 Operator Salary Advances Framework (Upad)")
        
        if is_editing_upad:
            st.session_state.sel_u_op = edit_upad_row.get("Operator", "")
            st.session_state.sel_pm = edit_upad_row.get("Payment Mode", "Cash")
        
        st.markdown("<p style='margin-bottom:2px; color:#ff9900;'>Select Upad Operator Target:</p>", unsafe_allow_html=True)
        if operator_options:
            upad_ops_grid = st.columns(max(len(operator_options), 1))
            for idx_uo, uo_title in enumerate(operator_options):
                lbl_u_state = f"✨ {uo_title}" if st.session_state.sel_u_op == uo_title else str(uo_title)
                if upad_ops_grid[idx_uo].button(lbl_u_state, key=f"grid_upad_op_{uo_title}"):
                    st.session_state.sel_u_op = uo_title
                    clear_all_messages()
                    st.rerun()
                    
        st.markdown("<p style='margin-top:8px; margin-bottom:2px; color:#7cfc00;'>Payment Method Selection:</p>", unsafe_allow_html=True)
        pm_c1, pm_c2 = st.columns(2)
        
        lbl_cash = "💵 CASH TRANSIT ACTIVE" if st.session_state.sel_pm == "Cash" else "Cash"
        if pm_c1.button(lbl_cash, key="btn_pm_cash_select"):
            st.session_state.sel_pm = "Cash"
            clear_all_messages()
            st.rerun()
            
        lbl_gpay = "📱 GPAY DIGITAL ACTIVE" if st.session_state.sel_pm == "GPay" else "GPay"
        if pm_c2.button(lbl_gpay, key="btn_pm_gpay_select"):
            st.session_state.sel_pm = "GPay"
            clear_all_messages()
            st.rerun()
            
        with st.form("upad_data_capture_form"):
            upad_date = st.date_input("Advance Disbursal Date:", value=datetime.strptime(edit_upad_row["Date"], "%Y-%m-%d").date() if is_editing_upad else datetime.today().date(), key=f"upad_date_{Token}")
            upad_amount = st.number_input("Disbursed Amount (₹):", min_value=0.0, step=100.0, value=float(edit_upad_row.get("Amount")) if is_editing_upad else None, placeholder="Type Upad amount...", key=f"upad_amt_{Token}")
            upad_remark = st.text_area("Reference Note:", value=edit_upad_row.get("Remark", "") if is_editing_upad else "", key=f"upad_rem_{Token}")
            
            btn_label_upad = "Update Advance Entry" if is_editing_upad else "Log Operator Advance Transaction"
            if st.form_submit_button(btn_label_upad):
                clear_all_messages()
                if not st.session_state.sel_u_op or upad_amount is None:
                    st.error("Operator Name reference details or Amount are blank!")
                else:
                    new_upad_row = {"Date": str(upad_date), "Operator": st.session_state.sel_u_op, "Amount": float(upad_amount), "Payment Mode": st.session_state.sel_pm, "Remark": upad_remark.strip()}
                    if is_editing_upad:
                        df_upad.iloc[st.session_state.edit_id] = new_upad_row
                        cancel_edit()
                        st.session_state.msg_upad = "✔ Advance Upad Record Updated!"
                    else:
                        df_upad = pd.concat([df_upad, pd.DataFrame([new_upad_row])], ignore_index=True)
                        st.session_state.msg_upad = "✔ Advance Upad Record Registered!"
                    save_data(df_upad, OP_UPAD_FILE)
                    trigger_form_reset()
                    st.rerun()
                    
            if is_editing_upad and st.form_submit_button("Cancel Upad Edit", key="cancel_upad_edit_btn"):
                cancel_edit()
                trigger_form_reset()
                st.rerun()
                    
            if st.session_state.msg_upad:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_upad}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 Live Enterprise Business Statements & Auditing Logs")
    
    selected_view_ledger = st.radio(
        "Choose Target Balance View Node Sheet:",
        ["Operator Complete Accounting View", "Client Party Outstanding Receivables Balances", "Raw Industrial Processing Logs Summary"]
    )
    
    # ==========================================
    # OPERATOR COMPLETE ACCOUNTING VIEW
    # ==========================================
    if selected_view_ledger == "Operator Complete Accounting View" and (not df_work.empty or not df_upad.empty):
        unique_active_ops = sorted(list(set(df_work["Operator"].unique()).union(set(df_upad["Operator"].unique()))))
        if unique_active_ops:
            filter_operator_target = st.selectbox("Select Target Auditing Operator:", unique_active_ops)
            
            st.markdown(f"#### Production Ledger Book: {filter_operator_target}")
            op_production_subset = df_work[df_work["Operator"] == filter_operator_target].copy().reset_index(drop=True)
            
            if not op_production_subset.empty:
                for target_idx, table_row in op_production_subset.iterrows():
                    with st.container():
                        cx1, cx2, cx3, cx4, cx5, cx6 = st.columns([1.5, 3.5, 2.0, 1.2, 0.9, 0.9])
                        cx1.write(f"📅 `{table_row['Date']}`")
                        
                        pcs_info = f"**Total PC:** {int(table_row['Pcs'])}"
                        if table_row['Work Type'] == "Carat":
                            pcs_info = f"**+20 PC:** {int(table_row.get('Pcs_20_Up', 0))} | **+1 PC:** {int(table_row.get('Pcs_1_Up', 0))}"
                            
                        cx2.write(f"**Party:** {table_row['Party']} | **Type:** {table_row['Work Type']} | {pcs_info}")
                        cx3.markdown(f"Op Earning: **₹{table_row['Operator Amount']:.2f}**")
                        
                        wa_txt = f"Work Receipt ({filter_operator_target}):\nDate: {table_row['Date']}\nType: {table_row['Work Type']}\nPcs: {table_row['Pcs']}\nEarnings: ₹{table_row['Operator Amount']}"
                        cx4.markdown(f"<a href='https://wa.me/?text={urllib.parse.quote(wa_txt)}' target='_blank'><button style='background-color:#25D366; border:none; color:white; border-radius:4px; width:100%;'>💬 WA</button></a>", unsafe_allow_html=True)
                        
                        if cx5.button("✏️ Edit", key=f"edit_op_work_row_{target_idx}"):
                            actual_df_idx = df_work[(df_work["Operator"] == filter_operator_target)].index[target_idx]
                            st.session_state.edit_id = actual_df_idx
                            st.session_state.edit_section = "Work"
                            st.session_state.edit_data = table_row.to_dict()
                            st.rerun()
                            
                        if cx6.button("❌ Delete", key=f"del_op_work_row_{target_idx}"):
                            clear_all_messages()
                            actual_df_idx = df_work[(df_work["Operator"] == filter_operator_target)].index[target_idx]
                            df_work = df_work.drop(actual_df_idx).reset_index(drop=True)
                            save_data(df_work, DAILY_WORK_FILE)
                            st.rerun()
                        st.markdown("<hr style='margin:2px 0; border-color:#21252b;' />", unsafe_allow_html=True)
            
            st.markdown(f"#### Balance Advance Draws History: {filter_operator_target}")
            op_upad_subset = df_upad[df_upad["Operator"] == filter_operator_target].copy().reset_index(drop=True)
            if not op_upad_subset.empty:
                for target_u_idx, u_row in op_upad_subset.iterrows():
                    with st.container():
                        ux1, ux2, ux3, ux4, ux5 = st.columns([1.5, 3.5, 2.0, 1.0, 1.0])
                        ux1.write(f"📅 `{u_row['Date']}`")
                        ux2.write(f"**Mode:** {u_row['Payment Mode']} | **Note:** {u_row['Remark']}")
                        ux3.markdown(f"Draw Amount: <span style='color:#ff5555; font-weight:bold;'>₹{u_row['Amount']:.2f}</span>", unsafe_allow_html=True)
                        
                        if ux4.button("✏️ Edit", key=f"edit_op_upad_row_{target_u_idx}"):
                            actual_df_u_idx = df_upad[(df_upad["Operator"] == filter_operator_target)].index[target_u_idx]
                            st.session_state.edit_id = actual_df_u_idx
                            st.session_state.edit_section = "Upad"
                            st.session_state.edit_data = u_row.to_dict()
                            st.rerun()
                            
                        if ux5.button("❌ Delete", key=f"del_op_upad_row_{target_u_idx}"):
                            clear_all_messages()
                            actual_df_u_idx = df_upad[(df_upad["Operator"] == filter_operator_target)].index[target_u_idx]
                            df_upad = df_upad.drop(actual_df_u_idx).reset_index(drop=True)
                            save_data(df_upad, OP_UPAD_FILE)
                            st.rerun()
                        st.markdown("<hr style='margin:2px 0; border-color:#21252b;' />", unsafe_allow_html=True)
                        
            gross_op_credits = op_production_subset["Operator Amount"].sum() if not op_production_subset.empty else 0.0
            gross_op_debits = op_upad_subset["Amount"].sum() if not op_upad_subset.empty else 0.0
            net_payable_salary = gross_op_credits - gross_op_debits
            
            st.markdown("---")
            st.markdown(f"### 📈 Accounting Bottom Summary for {filter_operator_target}")
            stat_c1, stat_c2, stat_c3 = st.columns(3)
            stat_c1.metric("Gross Production Value (Earnings)", f"₹{gross_op_credits:.2f}")
            stat_c2.metric("Total Advance Drawn Matrix (Upad)", f"₹{gross_op_debits:.2f}")
            stat_c3.metric("Net Salary Outstanding Payable Balance", f"₹{net_payable_salary:.2f}")
            
            if not op_production_subset.empty:
                st.markdown("**Production Breakdown Summary By Category:**")
                summary_table = op_production_subset.groupby("Work Type").agg(
                    Total_Pcs=("Pcs", "sum"),
                    Total_Carat_20=("Carat_20_Up", "sum"),
                    Total_Carat_1=("Carat_1_Up", "sum"),
                    Total_Earnings=("Operator Amount", "sum")
                ).reset_index()
                st.table(summary_table)
                
                pdf_op_blob = generate_pdf_document(op_production_subset[["Date", "Party", "Work Type", "Pcs", "Pcs_20_Up", "Pcs_1_Up", "Carat_20_Up", "Carat_1_Up", "Operator Amount"]], f"Production Statement For {filter_operator_target}")
                st.download_button(f"📥 Download {filter_operator_target} PDF Statement", data=pdf_op_blob, file_name=f"{filter_operator_target}_Invoice.pdf", mime="application/pdf")

    elif selected_view_ledger == "Client Party Outstanding Receivables Balances" and not df_work.empty:
        distinct_parties_logged = sorted(df_work["Party"].unique())
        if distinct_parties_logged:
            filter_party_target = st.selectbox("Select Target Client Billing Account:", distinct_parties_logged)
            party_billings_subset = df_work[df_work["Party"] == filter_party_target].copy().reset_index(drop=True)
            
            for party_idx, p_row in party_billings_subset.iterrows():
                with st.container():
                    px1, px2, px3, px4, px5, px6 = st.columns([1.5, 3.5, 2.0, 1.2, 0.9, 0.9])
                    px1.write(f"📅 `{p_row['Date']}`")
                    
                    pcs_info = f"**Pcs:** {p_row['Pcs']}"
                    if p_row['Work Type'] == "Carat":
                        pcs_info = f"**+20 PC:** {int(p_row.get('Pcs_20_Up', 0))} | **+1 PC:** {int(p_row.get('Pcs_1_Up', 0))}"
                        
                    px2.write(f"**Operator:** {p_row['Operator']} | **Profile Matrix Type:** {p_row['Work Type']} | {pcs_info}")
                    px3.markdown(f"Receivable Amt: **₹{p_row['Party Amount']:.2f}**")
                    
                    wa_party_msg = f"Invoice Statement Alert ({filter_party_target}):\nDate: {p_row['Date']}\nProduction Class Type: {p_row['Work Type']}\nCalculated Total Receivable: ₹{p_row['Party Amount']}"
                    px4.markdown(f"<a href='https://wa.me/?text={urllib.parse.quote(wa_party_msg)}' target='_blank'><button style='background-color:#25D366; border:none; color:white; border-radius:4px; width:100%;'>💬 WA</button></a>", unsafe_allow_html=True)
                    
                    if px5.button("✏️ Edit", key=f"edit_party_work_row_{party_idx}"):
                        actual_df_p_idx = df_work[(df_work["Party"] == filter_party_target)].index[party_idx]
                        st.session_state.edit_id = actual_df_p_idx
                        st.session_state.edit_section = "Work"
                        st.session_state.edit_data = p_row.to_dict()
                        st.rerun()
                        
                    if px6.button("❌ Delete Log Record", key=f"del_party_work_row_{party_idx}"):
                        clear_all_messages()
                        actual_df_p_idx = df_work[(df_work["Party"] == filter_party_target)].index[party_idx]
                        df_work = df_work.drop(actual_df_p_idx).reset_index(drop=True)
                        save_data(df_work, DAILY_WORK_FILE)
                        st.rerun()
                    st.markdown("<hr style='margin:2px 0; border-color:#21252b;' />", unsafe_allow_html=True)
            
            st.markdown("---")
            st.metric("Total Consolidated Account Receivables Outstanding Balance", f"₹{party_billings_subset['Party Amount'].sum():.2f}")
            
            pdf_pt_blob = generate_pdf_document(party_billings_subset[["Date", "Operator", "Work Type", "Pcs", "Pcs_20_Up", "Pcs_1_Up", "Carat_20_Up", "Carat_1_Up", "Party Rate", "Party Amount"]], f"Account Ledger Statement For {filter_party_target}")
            st.download_button(f"📥 Download {filter_party_target} Statement PDF Invoice", data=pdf_pt_blob, file_name=f"Party_{filter_party_target}_Ledger.pdf", mime="application/pdf")

    # ==========================================
    # RAW INDUSTRIAL PROCESSING LOGS SUMMARY (SMART FILTER + AUTO SUM)
    # ==========================================
    else:
        st.markdown("#### Complete Global Audit Raw Matrix Logs")
        
        search_query = st.text_input("🔍 Live Smart Search Filter (Mahesh, Party Name, Work Type ya Date likhein):", placeholder="Type anything to filter instantly...")
        
        if not df_work.empty:
            df_work_show = df_work.sort_values(by="Date", ascending=False).reset_index(drop=True)
            
            if search_query.strip():
                q = search_query.strip().lower()
                mask = (
                    df_work_show["Operator"].astype(str).str.lower().str.contains(q) |
                    df_work_show["Party"].astype(str).str.lower().str.contains(q) |
                    df_work_show["Work Type"].astype(str).str.lower().str.contains(q) |
                    df_work_show["Date"].astype(str).str.lower().str.contains(q)
                )
                df_work_filtered = df_work_show[mask].reset_index(drop=True)
            else:
                df_work_filtered = df_work_show.copy()
            
            total_filtered_pcs = df_work_filtered["Pcs"].sum()
            total_filtered_carat20 = df_work_filtered["Carat_20_Up"].sum()
            total_filtered_carat1 = df_work_filtered["Carat_1_Up"].sum()
            total_filtered_op_amt = df_work_filtered["Operator Amount"].sum()
            total_filtered_pt_amt = df_work_filtered["Party Amount"].sum()
            
            st.markdown("### 📊 Dynamic Aggregated Sum Panel (Filtered Live)")
            sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
            sum_col1.metric("Filtered Total Pieces (Pcs)", f"{int(total_filtered_pcs)} Pcs")
            sum_col2.metric("Filtered Carat Weight (+20 / +1)", f"{total_filtered_carat20:.2f} ct / {total_filtered_carat1:.2f} ct")
            sum_col3.metric("Filtered Operator Total Pay", f"₹{total_filtered_op_amt:.2f}")
            sum_col4.metric("Filtered Party Billing Total", f"₹{total_filtered_pt_amt:.2f}")
            st.markdown("---")
            
            display_work_df = df_work_filtered.copy()
            display_work_df.index = display_work_df.index + 1
            st.dataframe(display_work_df, use_container_width=True)
            
            if df_work_filtered.empty:
                st.warning("⚠️ Diye gaye keyword ke match hota hua koi record nahi mila!")
        else:
            st.info("No diamond processing transactions stored inside daily registry.")
