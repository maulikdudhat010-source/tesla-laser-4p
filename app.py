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
    pdf_canvas = SimpleDocTemplate(byte_stream, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=30, bottomMargin=30)
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
# 6. SIDEBAR NAVIGATION & RATE LOCK PANEL
# ==========================================
st.sidebar.markdown("<h2 style='color:#61afef; text-align: center; margin-bottom:0;'>💎 Tesla Laser Pro</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-size:11px; color:#ff9900;'>Industrial 4P Engine Panel</p>", unsafe_allow_html=True)
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

with st.sidebar.expander("⚙️ Configure Fixed Rates", expanded=True):
    # Piece Rates
    st.markdown("**1. Piece (PC) Mode Rates**")
    locked_op_pc = st.number_input("Operator Rate (PC):", min_value=0.0, value=st.session_state.locked_op_rate_pc, step=0.5, key="sb_op_pc")
    locked_party_pc = st.number_input("Party Rate (PC):", min_value=0.0, value=st.session_state.locked_party_rate_pc, step=0.5, key="sb_party_pc")
    
    st.markdown("---")
    # Carat Rates
    st.markdown("**2. Carat Mode Rates**")
    locked_op_20 = st.number_input("+20 Up Operator Rate:", min_value=0.0, value=st.session_state.locked_op_rate_20_up, step=0.5, key="sb_op_20")
    locked_op_1 = st.number_input("+1 Operator Rate:", min_value=0.0, value=st.session_state.locked_op_rate_1_up, step=0.5, key="sb_op_1")
    locked_party_carat = st.number_input("Party Consolidated Rate:", min_value=0.0, value=st.session_state.locked_party_rate_carat, step=0.5, key="sb_party_carat")
    
    st.markdown("---")
    # Choki Rates
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
# 7. SECTION 1: OFFICE EXPENSE ACCOUNTING
# ==========================================
if app_route == "(1) Office Expense Master":
    st.header("🏢 Office Records & Accounting Ledger")
    
    is_editing_office = (st.session_state.edit_section == "Office" and st.session_state.edit_id is not None)
    edit_office_row = st.session_state.edit_data if is_editing_office else {}
    
    col_income, col_expense = st.columns(2)
    
    with col_income:
        st.subheader("💰 Cash Inward (Paisa Aaya)")
        native_contact_picker_js("off_in")
        with st.form("office_income_capture_form", clear_on_submit=True):
            in_date = st.date_input("Date:", value=datetime.strptime(edit_office_row["Date"], "%Y-%m-%d").date() if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else datetime.today().date())
            in_name = st.text_input("Source Name / Party:", value=edit_office_row.get("Name", "") if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else "")
            
            in_amount = st.number_input("Collected Amount (₹):", min_value=0.0, step=50.0, value=float(edit_office_row.get("Amount")) if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else None, placeholder="Type amount directly...")
            in_phone = st.text_input("WhatsApp Number (10 Digits):", value=str(edit_office_row.get("Phone", "")) if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else "")
            in_remark = st.text_area("Entry Remarks / Context:", value=edit_office_row.get("Remark", "") if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else "")
            
            sub_label = "Update Cash Inward" if is_editing_office else "Save Cash Inward"
            if st.form_submit_button(sub_label):
                clear_all_messages()
                if not in_name or in_amount is None:
                    st.error("Nam aur Amount bharna mandatory hai!")
                else:
                    new_log = {"Date": str(in_date), "Type": "Income (Aaya)", "Name": in_name.strip(), "Amount": float(in_amount), "Phone": str(in_phone).strip(), "Remark": in_remark.strip()}
                    if is_editing_office:
                        df_office.iloc[st.session_state.edit_id] = new_log
                        cancel_edit()
                        st.session_state.msg_off_inc = "✔ Entry Updated Successfully!"
                    else:
                        df_office = pd.concat([df_office, pd.DataFrame([new_log])], ignore_index=True)
                        st.session_state.msg_off_inc = "✔ Income Entry Tracked Successfully!"
                    save_data(df_office, OFFICE_FILE)
                    st.rerun()
            
            if is_editing_office and st.form_submit_button("Cancel Edit"):
                cancel_edit()
                st.rerun()
            
            if st.session_state.msg_off_inc:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_off_inc}</div>', unsafe_allow_html=True)

    with col_expense:
        st.subheader("💸 Cash Outward (Paisa Gaya)")
        native_contact_picker_js("off_exp")
        with st.form("office_expense_capture_form", clear_on_submit=True):
            out_date = st.date_input("Date:", value=datetime.strptime(edit_office_row["Date"], "%Y-%m-%d").date() if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else datetime.today().date())
            out_name = st.text_input("Recipient / Vendor Name:", value=edit_office_row.get("Name", "") if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else "")
            
            out_amount = st.number_input("Paid Amount (₹):", min_value=0.0, step=50.0, value=float(edit_office_row.get("Amount")) if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else None, placeholder="Type amount directly...")
            out_phone = st.text_input("WhatsApp Number:", value=str(edit_office_row.get("Phone", "")) if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else "")
            out_remark = st.text_area("Purpose / Remark:", value=edit_office_row.get("Remark", "") if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else "")
            
            sub_label_exp = "Update Cash Outward" if is_editing_office else "Save Cash Outward"
            if st.form_submit_button(sub_label_exp):
                clear_all_messages()
                if not out_name or out_amount is None:
                    st.error("Nam aur Amount fields blank nahi chod sakte!")
                else:
                    new_log = {"Date": str(out_date), "Type": "Expense (Gaya)", "Name": out_name.strip(), "Amount": float(out_amount), "Phone": str(out_phone).strip(), "Remark": out_remark.strip()}
                    if is_editing_office:
                        df_office.iloc[st.session_state.edit_id] = new_log
                        cancel_edit()
                        st.session_state.msg_off_exp = "✔ Entry Updated Successfully!"
                    else:
                        df_office = pd.concat([df_office, pd.DataFrame([new_log])], ignore_index=True)
                        st.session_state.msg_off_exp = "✔ Expense Entry Tracked Successfully!"
                    save_data(df_office, OFFICE_FILE)
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
    
    col_hm_inc, col_hm_exp = st.columns(2)
    
    with col_hm_inc:
        st.subheader("💰 Inward Streams (Ghar me Paisa Aaya)")
        with st.form("home_income_form", clear_on_submit=True):
            h_in_date = st.date_input("Date:", value=datetime.strptime(edit_home_row["Date"], "%Y-%m-%d").date() if (is_editing_home and edit_home_row.get("Type") == "Income (Aaya)") else datetime.today().date())
            h_in_name = st.text_input("Source Name:", value=edit_home_row.get("Name", "") if (is_editing_home and edit_home_row.get("Type") == "Income (Aaya)") else "")
            
            h_in_amount = st.number_input("Amount (₹):", min_value=0.0, step=100.0, value=float(edit_home_row.get("Amount")) if (is_editing_home and edit_home_row.get("Type") == "Income (Aaya)") else None, placeholder="Type amount directly...")
            h_in_phone = st.text_input("Phone Reference:", value=str(edit_home_row.get("Phone", "")) if (is_editing_home and edit_home_row.get("Type") == "Income (Aaya)") else "")
            h_in_remark = st.text_area("Notes:", value=edit_home_row.get("Remark", "") if (is_editing_home and edit_home_row.get("Type") == "Income (Aaya)") else "")
            
            sub_label_hi = "Update Home Inward" if is_editing_home else "Commit Home Inward Record"
            if st.form_submit_button(sub_label_hi):
                clear_all_messages()
                if not h_in_name or h_in_amount is None:
                    st.error("Mandatory entries complete karein!")
                else:
                    new_record = {"Date": str(h_in_date), "Type": "Income (Aaya)", "Name": h_in_name.strip(), "Amount": float(h_in_amount), "Phone": str(h_in_phone).strip(), "Remark": h_in_remark.strip()}
                    if is_editing_home:
                        df_home.iloc[st.session_state.edit_id] = new_record
                        cancel_edit()
                        st.session_state.msg_hm_inc = "✔ Entry Updated Successfully!"
                    else:
                        df_home = pd.concat([df_home, pd.DataFrame([new_record])], ignore_index=True)
                        st.session_state.msg_hm_inc = "✔ Home Income Logged Successfully!"
                    save_data(df_home, HOME_FILE)
                    st.rerun()
            
            if is_editing_home and st.form_submit_button("Cancel Edit"):
                cancel_edit()
                st.rerun()
            
            if st.session_state.msg_hm_inc:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_hm_inc}</div>', unsafe_allow_html=True)

    with col_hm_exp:
        st.subheader("💸 Household Expenses (Kharcha)")
        with st.form("home_expense_form", clear_on_submit=True):
            h_out_date = st.date_input("Date:", value=datetime.strptime(edit_home_row["Date"], "%Y-%m-%d").date() if (is_editing_home and edit_home_row.get("Type") == "Expense (Gaya)") else datetime.today().date())
            h_out_name = st.text_input("Expense Title / Context:", value=edit_home_row.get("Name", "") if (is_editing_home and edit_home_row.get("Type") == "Expense (Gaya)") else "")
            
            h_out_amount = st.number_input("Spent Amount (₹):", min_value=0.0, step=50.0, value=float(edit_home_row.get("Amount")) if (is_editing_home and edit_home_row.get("Type") == "Expense (Gaya)") else None, placeholder="Type amount directly...")
            h_out_phone = st.text_input("Phone:", value=str(edit_home_row.get("Phone", "")) if (is_editing_home and edit_home_row.get("Type") == "Expense (Gaya)") else "")
            h_out_remark = st.text_area("Detail Description:", value=edit_home_row.get("Remark", "") if (is_editing_home and edit_home_row.get("Type") == "Expense (Gaya)") else "")
            
            sub_label_he = "Update Home Expense" if is_editing_home else "Commit Home Outward Record"
            if st.form_submit_button(sub_label_he):
                clear_all_messages()
                if not h_out_name or h_out_amount is None:
                    st.error("Data inputs verified empty!")
                else:
                    new_record = {"Date": str(h_out_date), "Type": "Expense (Gaya)", "Name": h_out_name.strip(), "Amount": float(h_out_amount), "Phone": str(h_out_phone).strip(), "Remark": h_out_remark.strip()}
                    if is_editing_home:
                        df_home.iloc[st.session_state.edit_id] = new_record
                        cancel_edit()
                        st.session_state.msg_hm_exp = "✔ Entry Updated Successfully!"
                    else:
                        df_home = pd.concat([df_home, pd.DataFrame([new_record])], ignore_index=True)
                        st.session_state.msg_hm_exp = "✔ Home Expense Logged Successfully!"
                    save_data(df_home, HOME_FILE)
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
    
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.markdown("### 🛠 Operator Registration Node")
        with st.form("master_operator_management_form", clear_on_submit=True):
            input_op_name = st.text_input("Enter New Operator Name:")
            execution_method = st.selectbox("Action Vector:", ["Register/Add", "Unregister/Remove"])
            
            if st.form_submit_button("Commit Master Action"):
                clear_all_messages()
                cleaned_name = input_op_name.strip()
                if cleaned_name:
                    if execution_method == "Register/Add":
                        if not ((df_master['Type'] == 'Operator') & (df_master['Name'] == cleaned_name)).any():
                            df_master = pd.concat([df_master, pd.DataFrame([{"Type": "Operator", "Name": cleaned_name}])], ignore_index=True)
                            save_data(df_master, OP_PARTY_MASTER_FILE)
                            st.rerun()
                    else:
                        df_master = df_master[~((df_master['Type'] == 'Operator') & (df_master['Name'] == cleaned_name))]
                        save_data(df_master, OP_PARTY_MASTER_FILE)
                        st.rerun()
                        
    with m_col2:
        st.markdown("### 🏢 Client Party Registration Node")
        with st.form("master_party_management_form", clear_on_submit=True):
            input_pt_name = st.text_input("Enter New Business Party Name:")
            execution_method_pt = st.selectbox("Action Vector:", ["Register/Add", "Unregister/Remove"])
            
            if st.form_submit_button("Commit Party Action"):
                clear_all_messages()
                cleaned_pt_name = input_pt_name.strip()
                if cleaned_pt_name:
                    if execution_method_pt == "Register/Add":
                        if not ((df_master['Type'] == 'Party') & (df_master['Name'] == cleaned_pt_name)).any():
                            df_master = pd.concat([df_master, pd.DataFrame([{"Type": "Party", "Name": cleaned_pt_name}])], ignore_index=True)
                            save_data(df_master, OP_PARTY_MASTER_FILE)
                            st.rerun()
                    else:
                        df_master = df_master[~((df_master['Type'] == 'Party') & (df_master['Name'] == cleaned_pt_name))]
                        save_data(df_master, OP_PARTY_MASTER_FILE)
                        st.rerun()
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
    pdf_canvas = SimpleDocTemplate(byte_stream, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=30, bottomMargin=30)
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
# 6. SIDEBAR NAVIGATION & RATE LOCK PANEL
# ==========================================
st.sidebar.markdown("<h2 style='color:#61afef; text-align: center; margin-bottom:0;'>💎 Tesla Laser Pro</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-size:11px; color:#ff9900;'>Industrial 4P Engine Panel</p>", unsafe_allow_html=True)
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

with st.sidebar.expander("⚙️ Configure Fixed Rates", expanded=True):
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
# 7. SECTION 1: OFFICE EXPENSE ACCOUNTING
# ==========================================
if app_route == "(1) Office Expense Master":
    st.header("🏢 Office Records & Accounting Ledger")
    
    is_editing_office = (st.session_state.edit_section == "Office" and st.session_state.edit_id is not None)
    edit_office_row = st.session_state.edit_data if is_editing_office else {}
    
    col_income, col_expense = st.columns(2)
    
    with col_income:
        st.subheader("💰 Cash Inward (Paisa Aaya)")
        native_contact_picker_js("off_in")
        with st.form("office_income_capture_form", clear_on_submit=True):
            in_date = st.date_input("Date:", value=datetime.strptime(edit_office_row["Date"], "%Y-%m-%d").date() if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else datetime.today().date())
            in_name = st.text_input("Source Name / Party:", value=edit_office_row.get("Name", "") if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else "")
            
            in_amount = st.number_input("Collected Amount (₹):", min_value=0.0, step=50.0, value=float(edit_office_row.get("Amount")) if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else None, placeholder="Type amount directly...")
            in_phone = st.text_input("WhatsApp Number (10 Digits):", value=str(edit_office_row.get("Phone", "")) if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else "")
            in_remark = st.text_area("Entry Remarks / Context:", value=edit_office_row.get("Remark", "") if (is_editing_office and edit_office_row.get("Type") == "Income (Aaya)") else "")
            
            sub_label = "Update Cash Inward" if is_editing_office else "Save Cash Inward"
            if st.form_submit_button(sub_label):
                clear_all_messages()
                if not in_name or in_amount is None:
                    st.error("Nam aur Amount bharna mandatory hai!")
                else:
                    new_log = {"Date": str(in_date), "Type": "Income (Aaya)", "Name": in_name.strip(), "Amount": float(in_amount), "Phone": str(in_phone).strip(), "Remark": in_remark.strip()}
                    if is_editing_office:
                        df_office.iloc[st.session_state.edit_id] = new_log
                        cancel_edit()
                        st.session_state.msg_off_inc = "✔ Entry Updated Successfully!"
                    else:
                        df_office = pd.concat([df_office, pd.DataFrame([new_log])], ignore_index=True)
                        st.session_state.msg_off_inc = "✔ Income Entry Tracked Successfully!"
                    save_data(df_office, OFFICE_FILE)
                    st.rerun()
            
            if is_editing_office and st.form_submit_button("Cancel Edit"):
                cancel_edit()
                st.rerun()
            
            if st.session_state.msg_off_inc:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_off_inc}</div>', unsafe_allow_html=True)

    with col_expense:
        st.subheader("💸 Cash Outward (Paisa Gaya)")
        native_contact_picker_js("off_exp")
        with st.form("office_expense_capture_form", clear_on_submit=True):
            out_date = st.date_input("Date:", value=datetime.strptime(edit_office_row["Date"], "%Y-%m-%d").date() if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else datetime.today().date())
            out_name = st.text_input("Recipient / Vendor Name:", value=edit_office_row.get("Name", "") if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else "")
            
            out_amount = st.number_input("Paid Amount (₹):", min_value=0.0, step=50.0, value=float(edit_office_row.get("Amount")) if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else None, placeholder="Type amount directly...")
            out_phone = st.text_input("WhatsApp Number:", value=str(edit_office_row.get("Phone", "")) if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else "")
            out_remark = st.text_area("Purpose / Remark:", value=edit_office_row.get("Remark", "") if (is_editing_office and edit_office_row.get("Type") == "Expense (Gaya)") else "")
            
            sub_label_exp = "Update Cash Outward" if is_editing_office else "Save Cash Outward"
            if st.form_submit_button(sub_label_exp):
                clear_all_messages()
                if not out_name or out_amount is None:
                    st.error("Nam aur Amount fields blank nahi chod sakte!")
                else:
                    new_log = {"Date": str(out_date), "Type": "Expense (Gaya)", "Name": out_name.strip(), "Amount": float(out_amount), "Phone": str(out_phone).strip(), "Remark": out_remark.strip()}
                    if is_editing_office:
                        df_office.iloc[st.session_state.edit_id] = new_log
                        cancel_edit()
                        st.session_state.msg_off_exp = "✔ Entry Updated Successfully!"
                    else:
                        df_office = pd.concat([df_office, pd.DataFrame([new_log])], ignore_index=True)
                        st.session_state.msg_off_exp = "✔ Expense Entry Tracked Successfully!"
                    save_data(df_office, OFFICE_FILE)
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

