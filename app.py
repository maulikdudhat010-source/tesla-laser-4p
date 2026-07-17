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

# High-Contrast Active Navigation & Status Highlights Styling
st.markdown("""
    <style>
    /* Streamlit Defaults Cleaning */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    
    /* Global Visual Base */
    .stApp {
        background-color: #111418 !important;
        color: #ffffff !important;
    }
    
    /* Left Sidebar Indicator */
    section[data-testid="stSidebar"] {
        background-color: #0b0d10 !important;
        border-right: 3px solid #61afef !important;
    }
    
    /* Input Container Styling */
    div[data-testid="stForm"], .stAlert {
        background-color: #1c2026 !important;
        border: 2px solid #2d333f !important;
        border-radius: 8px !important;
        padding: 20px !important;
    }
    
    /* High Visibility Typography */
    label, p, span, .stMetric div {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    h1, h2, h3, h4 {
        color: #61afef !important;
        font-weight: 800 !important;
    }
    
    /* Form Input Fields Border Color Controls */
    input, select, textarea, div[data-baseweb="input"] input, div[data-baseweb="select"] {
        background-color: #111418 !important;
        color: #ffffff !important;
        border: 2px solid #3e4452 !important;
        font-size: 14px !important;
    }
    
    input:focus, select:focus, textarea:focus {
        border-color: #61afef !important;
    }
    
    /* ACTIVE STATE HIGHLIGHTS (Dynamic Colors based on state selection) */
    .active-btn-pc {
        background-color: #d19a66 !important;
        color: #000000 !important;
        font-weight: bold !important;
    }
    
    /* Main Action Form Buttons */
    button[kind="primary"], div.stButton > button:first-child {
        background-color: #4a75a0 !important;
        color: #ffffff !important;
        border: 2px solid #61afef !important;
        font-weight: bold !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    
    button[kind="primary"]:hover, div.stButton > button:first-child:hover {
        background-color: #ff9900 !important;
        color: #000000 !important;
        border-color: #ffaa00 !important;
        cursor: pointer;
    }
    
    /* Row Interactive Operations Styling */
    .action-btn {
        padding: 2px 5px !important;
        font-size: 12px !important;
    }
    
    /* Clear Visible Notification Blocks */
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
# 3. INTERACTIVE SESSION CONTROLLERS
# ==========================================
# Message logs initialization
for key in ['msg_off_inc', 'msg_off_exp', 'msg_hm_inc', 'msg_hm_exp', 'msg_work', 'msg_upad']:
    if key not in st.session_state: 
        st.session_state[key] = ""

# Active State Selection Trackers
if 'sel_op' not in st.session_state: st.session_state.sel_op = ""
if 'sel_pt' not in st.session_state: st.session_state.sel_pt = ""
if 'sel_wt' not in st.session_state: st.session_state.sel_wt = "PC"
if 'sel_u_op' not in st.session_state: st.session_state.sel_u_op = ""
if 'sel_pm' not in st.session_state: st.session_state.sel_pm = "Cash"

# Edit System Variables
if 'edit_id' not in st.session_state: st.session_state.edit_id = None
if 'edit_section' not in st.session_state: st.session_state.edit_section = ""

# Auto Clear Callback Function
def clear_all_messages():
    st.session_state.msg_off_inc = ""
    st.session_state.msg_off_exp = ""
    st.session_state.msg_hm_inc = ""
    st.session_state.msg_hm_exp = ""
    st.session_state.msg_work = ""
    st.session_state.msg_upad = ""

# ==========================================
# 4. STORAGE DATA HANDLING SYSTEM
# ==========================================
def load_data(file_path, base_columns):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            # Synchronize schema matches
            for col in base_columns:
                if col not in df.columns:
                    df[col] = 0.0 if col in ["Amount", "Pcs", "Carat_20_Up", "Carat_1_Up", "Choki"] else ""
            return df
        except:
            return pd.DataFrame(columns=base_columns)
    return pd.DataFrame(columns=base_columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# Master Data Schema Mappings
df_master = load_data(OP_PARTY_MASTER_FILE, ["Type", "Name"])
df_office = load_data(OFFICE_FILE, ["Date", "Type", "Name", "Amount", "Phone", "Remark"])
df_home = load_data(HOME_FILE, ["Date", "Type", "Name", "Amount", "Phone", "Remark"])

work_columns_template = [
    "Date", "Operator", "Party", "Work Type", "Pcs", 
    "Carat_20_Up", "Carat_1_Up", "Choki", 
    "Op_Rate_20_Up", "Op_Rate_1_Up",
    "Operator Rate", "Party Rate", "Operator Amount", "Party Amount"
]
df_work = load_data(DAILY_WORK_FILE, work_columns_template)
df_upad = load_data(OP_UPAD_FILE, ["Date", "Operator", "Amount", "Payment Mode", "Remark"])

# Sanitize Types & Floating values
numerical_fields = ["Pcs", "Carat_20_Up", "Carat_1_Up", "Choki", "Op_Rate_20_Up", "Op_Rate_1_Up", "Operator Rate", "Party Rate", "Operator Amount", "Party Amount"]
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
# 6. SIDEBAR SYSTEM NAVIGATION INTERFACE
# ==========================================
st.sidebar.markdown("<h2 style='color:#61afef; text-align: center; margin-bottom:0;'>💎 Tesla Laser Pro</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-size:11px; color:#ff9900;'>Industrial 4P Engine Panel</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

app_route = st.sidebar.radio(
    "Navigation System Menu:",
    ["(1) Office Expense Master", "(2) Home Expense Master", "(3) Operator Ledger & Production Desk"],
    on_change=clear_all_messages
)

# Active Route Marker UI Injection
if app_route == "(1) Office Expense Master":
    st.sidebar.markdown("<div style='background-color:#1c2026; padding:10px; border-radius:5px; border-left:4px solid #ff9900; text-align:center; font-weight:bold;'>📍 Location: Office Desk Active</div>", unsafe_allow_html=True)
elif app_route == "(2) Home Expense Master":
    st.sidebar.markdown("<div style='background-color:#1c2026; padding:10px; border-radius:5px; border-left:4px solid #7cfc00; text-align:center; font-weight:bold;'>📍 Location: Home Desk Active</div>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<div style='background-color:#1c2026; padding:10px; border-radius:5px; border-left:4px solid #61afef; text-align:center; font-weight:bold;'>📍 Location: Diamond Production Active</div>", unsafe_allow_html=True)

# ==========================================
# 7. SECTION 1: OFFICE EXPENSE ACCOUNTING
# ==========================================
if app_route == "(1) Office Expense Master":
    st.header("🏢 Office Records & Accounting Ledger")
    
    # Handle Form State Initialization for edits
    if st.session_state.edit_section != "Office":
        edit_row = {"Date": datetime.today().date(), "Type": "Income (Aaya)", "Name": "", "Amount": 0.0, "Phone": "", "Remark": ""}
    
    col_income, col_expense = st.columns(2)
    
    with col_income:
        st.subheader("💰 Cash Inward (Paisa Aaya)")
        native_contact_picker_js("off_in")
        with st.form("office_income_capture_form"):
            in_date = st.date_input("Date:", key="oi_f_date")
            in_name = st.text_input("Source Name / Party:", value="" if st.session_state.edit_section != "Office" else edit_row["Name"], on_change=clear_all_messages)
            in_amount = st.number_input("Collected Amount (₹):", min_value=0.0, step=50.0, value=None)
            in_phone = st.text_input("WhatsApp Number (10 Digits):")
            in_remark = st.text_area("Entry Remarks / Context:")
            
            if st.form_submit_button("Save Cash Inward"):
                if not in_name or in_amount is None:
                    st.error("Nam aur Amount bharna mandatory hai!")
                else:
                    new_log = {"Date": str(in_date), "Type": "Income (Aaya)", "Name": in_name.strip(), "Amount": float(in_amount), "Phone": in_phone.strip(), "Remark": in_remark.strip()}
                    df_office = pd.concat([df_office, pd.DataFrame([new_log])], ignore_index=True)
                    save_data(df_office, OFFICE_FILE)
                    st.session_state.msg_off_inc = "✔ Income Entry Tracked Successfully!"
                    st.rerun()
            
            if st.session_state.msg_off_inc:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_off_inc}</div>', unsafe_allow_html=True)

    with col_expense:
        st.subheader("💸 Cash Outward (Paisa Gaya)")
        native_contact_picker_js("off_exp")
        with st.form("office_expense_capture_form"):
            out_date = st.date_input("Date:", key="oe_f_date")
            out_name = st.text_input("Recipient / Vendor Name:", on_change=clear_all_messages)
            out_amount = st.number_input("Paid Amount (₹):", min_value=0.0, step=50.0, value=None)
            out_phone = st.text_input("WhatsApp Number:")
            out_remark = st.text_area("Purpose / Remark:")
            
            if st.form_submit_button("Save Cash Outward"):
                if not out_name or out_amount is None:
                    st.error("Nam aur Amount fields blank nahi chod sakte!")
                else:
                    new_log = {"Date": str(out_date), "Type": "Expense (Gaya)", "Name": out_name.strip(), "Amount": float(out_amount), "Phone": out_phone.strip(), "Remark": out_remark.strip()}
                    df_office = pd.concat([df_office, pd.DataFrame([new_log])], ignore_index=True)
                    save_data(df_office, OFFICE_FILE)
                    st.session_state.msg_off_exp = "✔ Expense Entry Tracked Successfully!"
                    st.rerun()
            
            if st.session_state.msg_off_exp:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_off_exp}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Filtered Statements Log Sheet")
    
    if not df_office.empty:
        df_office = df_office.sort_values(by="Date", ascending=False).reset_index(drop=True)
        
        # Build manual interactive rows for advanced actions
        for idx, row in df_office.iterrows():
            with st.container():
                r_col1, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns([1.5, 2.5, 1.5, 2.5, 1.5, 1.5])
                
                # Designations
                r_col1.markdown(f"🗓 `{row['Date']}`")
                badge = f"🟢 <span style='color:#7cfc00;'>{row['Type']}</span>" if "Income" in row['Type'] else f"🔴 <span style='color:#ff5555;'>{row['Type']}</span>"
                r_col2.markdown(f"{badge} **{row['Name']}**", unsafe_allow_html=True)
                r_col3.markdown(f"💰 **₹{row['Amount']:.2f}**")
                r_col4.markdown(f"📝 <span style='color:#a6b2c6;'>{row['Remark']}</span>", unsafe_allow_html=True)
                
                # WhatsApp Action Link Execution
                wa_msg_body = f"Tesla Laser Office Log:\nDate: {row['Date']}\nType: {row['Type']}\nParty: {row['Name']}\nAmount: ₹{row['Amount']}\nRemark: {row['Remark']}"
                wa_endpoint = build_whatsapp_url(row['Phone'], wa_msg_body)
                if row['Phone']:
                    r_col5.markdown(f"<a href='{wa_endpoint}' target='_blank'><button style='background-color:#25D366; color:white; border:none; border-radius:4px; font-weight:bold; padding:2px 8px;'>💬 Send WA</button></a>", unsafe_allow_html=True)
                else:
                    r_col5.markdown("<span style='color:grey; font-size:12px;'>No Phone</span>", unsafe_allow_html=True)
                
                if r_col6.button("❌ Delete", key=f"del_off_row_{idx}"):
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
    col_hm_inc, col_hm_exp = st.columns(2)
    
    with col_hm_inc:
        st.subheader("💰 Inward Streams (Ghar me Paisa Aaya)")
        with st.form("home_income_form"):
            h_in_date = st.date_input("Date:", key="hi_f_date")
            h_in_name = st.text_input("Source Name:", on_change=clear_all_messages)
            h_in_amount = st.number_input("Amount (₹):", min_value=0.0, step=100.0, value=None)
            h_in_phone = st.text_input("Phone Reference:")
            h_in_remark = st.text_area("Notes:")
            
            if st.form_submit_button("Commit Home Inward Record"):
                if not h_in_name or h_in_amount is None:
                    st.error("Mandatory entries complete karein!")
                else:
                    new_record = {"Date": str(h_in_date), "Type": "Income (Aaya)", "Name": h_in_name.strip(), "Amount": float(h_in_amount), "Phone": h_in_phone.strip(), "Remark": h_in_remark.strip()}
                    df_home = pd.concat([df_home, pd.DataFrame([new_record])], ignore_index=True)
                    save_data(df_home, HOME_FILE)
                    st.session_state.msg_hm_inc = "✔ Home Income Logged Successfully!"
                    st.rerun()
            
            if st.session_state.msg_hm_inc:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_hm_inc}</div>', unsafe_allow_html=True)

    with col_hm_exp:
        st.subheader("💸 Household Expenses (Kharcha)")
        with st.form("home_expense_form"):
            h_out_date = st.date_input("Date:", key="he_f_date")
            h_out_name = st.text_input("Expense Title / Context:", on_change=clear_all_messages)
            h_out_amount = st.number_input("Spent Amount (₹):", min_value=0.0, step=50.0, value=None)
            h_out_phone = st.text_input("Phone:")
            h_out_remark = st.text_area("Detail Description:")
            
            if st.form_submit_button("Commit Home Outward Record"):
                if not h_out_name or h_out_amount is None:
                    st.error("Data inputs verified empty!")
                else:
                    new_record = {"Date": str(h_out_date), "Type": "Expense (Gaya)", "Name": h_out_name.strip(), "Amount": float(h_out_amount), "Phone": h_out_phone.strip(), "Remark": h_out_remark.strip()}
                    df_home = pd.concat([df_home, pd.DataFrame([new_record])], ignore_index=True)
                    save_data(df_home, HOME_FILE)
                    st.session_state.msg_hm_exp = "✔ Home Expense Logged Successfully!"
                    st.rerun()
            
            if st.session_state.msg_hm_exp:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_hm_exp}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Domestic Ledger History View")
    
    if not df_home.empty:
        df_home = df_home.sort_values(by="Date", ascending=False).reset_index(drop=True)
        
        for idx, row in df_home.iterrows():
            with st.container():
                hr_c1, hr_c2, hr_c3, hr_c4, hr_c5 = st.columns([2, 3, 2, 3, 2])
                hr_c1.write(f"📅 `{row['Date']}`")
                label_color = "#7cfc00" if "Income" in row['Type'] else "#ff5555"
                hr_c2.markdown(f"<span style='color:{label_color}; font-weight:bold;'>[{row['Type']}]</span> {row['Name']}", unsafe_allow_html=True)
                hr_c3.markdown(f"₹ **{row['Amount']:.2f}**")
                hr_c4.markdown(f"<span style='color:#8a93a5;'>{row['Remark']}</span>", unsafe_allow_html=True)
                
                if hr_c5.button("❌ Delete", key=f"del_hm_row_{idx}"):
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
    
    # Extract dynamic listings
    operator_options = df_master[df_master["Type"] == "Operator"]["Name"].tolist()
    party_options = df_master[df_master["Type"] == "Party"]["Name"].tolist()
    
    # Master Setup Core Layout
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.markdown("### 🛠 Operator Registration Node")
        with st.form("master_operator_management_form"):
            input_op_name = st.text_input("Enter New Operator Name:")
            execution_method = st.selectbox("Action Vector:", ["Register/Add", "Unregister/Remove"])
            
            if st.form_submit_button("Commit Master Action"):
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
        with st.form("master_party_management_form"):
            input_pt_name = st.text_input("Enter New Business Party Name:")
            execution_method_pt = st.selectbox("Action Vector:", ["Register/Add", "Unregister/Remove"])
            
            if st.form_submit_button("Commit Client Action"):
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

    st.markdown("---")
    
    # Dynamic Dashboard Control Columns
    input_column, upad_column = st.columns(2)
    
    with input_column:
        st.markdown("### 📝 Daily Diamond Production Log")
        
        # 1. Operator Selection Layout Grid with Active Highlight
        st.markdown("<p style='margin-bottom:2px; color:#ff9900;'>Select Working Operator:</p>", unsafe_allow_html=True)
        if operator_options:
            op_grid_cols = st.columns(max(len(operator_options), 1))
            for index_op, op_title in enumerate(operator_options):
                is_selected = st.session_state.sel_op == op_title
                button_label = f"⭐ {op_title}" if is_selected else str(op_title)
                
                # Active Dynamic Visual Border injection logic via click triggers
                if op_grid_cols[index_op].button(button_label, key=f"grid_op_select_{op_title}"):
                    st.session_state.sel_op = op_title
                    clear_all_messages()
                    st.rerun()
        else:
            st.error("Upar master register me operator add karein pehle!")
            
        # 2. Category selection panel with Active Highlight
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
        
        # Main Entry Capture Submission Form
        with st.form("production_main_data_capture_form"):
            prod_date = st.date_input("Processing Entry Date:", key="prod_f_date")
            prod_party = st.selectbox("Select Target Client Party Account:", party_options)
            
            # Setup localized fields defaults
            pcs_count = 0
            carat_20_weight = 0.0
            carat_1_weight = 0.0
            choki_count = 0
            
            op_rate_20_up, op_rate_1_up, generic_op_rate, unified_party_rate = 0.0, 0.0, None, None
            
            # Conditional Rendering Logic for fields
            if st.session_state.sel_wt == "PC":
                pcs_count = st.number_input("Total Processed PC Count:", min_value=0, value=0, step=1)
                generic_op_rate = st.number_input("Operator Component Rate (per PC):", min_value=0.0, value=None, placeholder="Rate dalein...")
                unified_party_rate = st.number_input("Party Billing Rate (per PC):", min_value=0.0, value=None, placeholder="Rate dalein...")
                
            elif st.session_state.sel_wt == "Carat":
                # Carat includes inner Pcs Count matrix requested by user
                st.markdown("<p style='color:#ff9900; font-weight:bold; margin-bottom: 2px;'>Carat Metrics & Integrated Pcs Box:</p>", unsafe_allow_html=True)
                pcs_count = st.number_input("Total Number of Pcs Inside Carat Batch:", min_value=0, value=0, step=1)
                
                wt_col1, wt_col2 = st.columns(2)
                with wt_col1:
                    carat_20_weight = st.number_input("+20 Up Raw Carat Weight Value:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
                    op_rate_20_up = st.number_input("+20 Up Operator Pay Rate:", min_value=0.0, value=0.0, step=0.1)
                with wt_col2:
                    carat_1_weight = st.number_input("+1 Carat Raw Weight Value:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
                    op_rate_1_up = st.number_input("+1 Carat Operator Pay Rate:", min_value=0.0, value=0.0, step=0.1)
                    
                st.markdown("<p style='color:#7cfc00; font-weight:bold; margin-bottom: 2px;'>Collective Consolidated Party Evaluation:</p>", unsafe_allow_html=True)
                unified_party_rate = st.number_input("Consolidated Party Carat Standard Rate:", min_value=0.0, value=None, placeholder="Total single rate...")
                
            else:
                choki_count = st.number_input("Total Handled Choki Units:", min_value=0, value=0, step=1)
                generic_op_rate = st.number_input("Operator Pay Scale (per Choki):", min_value=0.0, value=None, placeholder="Rate...")
                unified_party_rate = st.number_input("Party Collection Scale (per Choki):", min_value=0.0, value=None, placeholder="Rate...")
                
            if st.form_submit_button("Commit Production Entry to Records"):
                if not st.session_state.sel_op or not prod_party:
                    st.error("Operator aur Party selection absolute mandatory hai!")
                elif unified_party_rate is None or (st.session_state.sel_wt != "Carat" and generic_op_rate is None):
                    st.error("Financial rates components missing!")
                else:
                    # Execute mathematical evaluation matching parameters precisely
                    if st.session_state.sel_wt == "PC":
                        calculated_op_amount = float(pcs_count * generic_op_rate)
                        calculated_party_amount = float(pcs_count * unified_party_rate)
                        final_op_rate_logged = generic_op_rate
                    elif st.session_state.sel_wt == "Carat":
                        calculated_op_amount = float((carat_20_weight * op_rate_20_up) + (carat_1_weight * op_rate_1_up))
                        # Unified merged total calculation logic requested by user for party matrix
                        calculated_party_amount = float((carat_20_weight + carat_1_weight) * unified_party_rate)
                        final_op_rate_logged = 0.0
                    else:
                        calculated_op_amount = float(choki_count * generic_op_rate)
                        calculated_party_amount = float(choki_count * unified_party_rate)
                        final_op_rate_logged = generic_op_rate
                        
                    new_production_row = {
                        "Date": str(prod_date), "Operator": st.session_state.sel_op, "Party": prod_party,
                        "Work Type": st.session_state.sel_wt, "Pcs": int(pcs_count),
                        "Carat_20_Up": float(carat_20_weight), "Carat_1_Up": float(carat_1_weight), "Choki": int(choki_count),
                        "Op_Rate_20_Up": float(op_rate_20_up), "Op_Rate_1_Up": float(op_rate_1_up), 
                        "Operator Rate": float(final_op_rate_logged), "Party Rate": float(unified_party_rate),
                        "Operator Amount": float(calculated_op_amount), "Party Amount": float(calculated_party_amount)
                    }
                    df_work = pd.concat([df_work, pd.DataFrame([new_production_row])], ignore_index=True)
                    save_data(df_work, DAILY_WORK_FILE)
                    st.session_state.msg_work = "✔ Daily Production Entry Tracked Matrix Confirmed!"
                    st.rerun()
            
            if st.session_state.msg_work:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_work}</div>', unsafe_allow_html=True)

    with upad_column:
        st.markdown("### 💸 Operator Salary Advances Framework (Upad)")
        
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
            upad_date = st.date_input("Advance Disbursal Date:", key="upad_f_date")
            upad_amount = st.number_input("Disbursed Amount (₹):", min_value=0.0, step=100.0, value=None)
            upad_remark = st.text_area("Reference Note:")
            
            if st.form_submit_button("Log Operator Advance Transaction"):
                if not st.session_state.sel_u_op or upad_amount is None:
                    st.error("Operator Name reference details or Amount are blank!")
                else:
                    new_upad_row = {"Date": str(upad_date), "Operator": st.session_state.sel_u_op, "Amount": float(upad_amount), "Payment Mode": st.session_state.sel_pm, "Remark": upad_remark.strip()}
                    df_upad = pd.concat([df_upad, pd.DataFrame([new_upad_row])], ignore_index=True)
                    save_data(df_upad, OP_UPAD_FILE)
                    st.session_state.msg_upad = "✔ Advance Upad Record Registered!"
                    st.rerun()
                    
            if st.session_state.msg_upad:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_upad}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 Live Enterprise Business Statements & Auditing Logs")
    
    selected_view_ledger = st.radio(
        "Choose Target Balance View Node Sheet:",
        ["Operator Complete Accounting View", "Client Party Outstanding Receivables Balances", "Raw Industrial Processing Logs Summary"]
    )
    
    if selected_view_ledger == "Operator Complete Accounting View" and (not df_work.empty or not df_upad.empty):
        unique_active_ops = sorted(list(set(df_work["Operator"].unique()).union(set(df_upad["Operator"].unique()))))
        if unique_active_ops:
            filter_operator_target = st.selectbox("Select Target Auditing Operator:", unique_active_ops)
            
            st.markdown(f"#### Production Ledger Book: {filter_operator_target}")
            op_production_subset = df_work[df_work["Operator"] == filter_operator_target].copy().reset_index(drop=True)
            
            if not op_production_subset.empty:
                for target_idx, table_row in op_production_subset.iterrows():
                    with st.container():
                        cx1, cx2, cx3, cx4, cx5 = st.columns([1.5, 3.5, 2.0, 1.5, 1.5])
                        cx1.write(f"📅 `{table_row['Date']}`")
                        cx2.write(f"**Party:** {table_row['Party']} | **Type:** {table_row['Work Type']} | **Pcs:** {int(table_row['Pcs'])}")
                        cx3.markdown(f"Op Earning: **₹{table_row['Operator Amount']:.2f}**")
                        
                        wa_txt = f"Work Receipt ({filter_operator_target}):\nDate: {table_row['Date']}\nType: {table_row['Work Type']}\nPcs: {table_row['Pcs']}\nEarnings: ₹{table_row['Operator Amount']}"
                        cx4.markdown(f"<a href='https://wa.me/?text={urllib.parse.quote(wa_txt)}' target='_blank'><button style='background-color:#25D366; border:none; color:white; border-radius:4px;'>💬 WhatsApp</button></a>", unsafe_allow_html=True)
                        
                        if cx5.button("❌ Delete", key=f"del_op_work_row_{target_idx}"):
                            # Match real index back to parent
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
                        ux1, ux2, ux3, ux4 = st.columns([2, 4, 3, 3])
                        ux1.write(f"📅 `{u_row['Date']}`")
                        ux2.write(f"**Mode:** {u_row['Payment Mode']} | **Note:** {u_row['Remark']}")
                        ux3.markdown(f"Draw Amount: <span style='color:#ff5555; font-weight:bold;'>₹{u_row['Amount']:.2f}</span>", unsafe_allow_html=True)
                        
                        if ux4.button("❌ Delete", key=f"del_op_upad_row_{target_u_idx}"):
                            actual_df_u_idx = df_upad[(df_upad["Operator"] == filter_operator_target)].index[target_u_idx]
                            df_upad = df_upad.drop(actual_df_u_idx).reset_index(drop=True)
                            save_data(df_upad, OP_UPAD_FILE)
                            st.rerun()
                        st.markdown("<hr style='margin:2px 0; border-color:#21252b;' />", unsafe_allow_html=True)
                        
            gross_op_credits = op_production_subset["Operator Amount"].sum() if not op_production_subset.empty else 0.0
            gross_op_debits = op_upad_subset["Amount"].sum() if not op_upad_subset.empty else 0.0
            net_payable_salary = gross_op_credits - gross_op_debits
            
            st.markdown("---")
            stat_c1, stat_c2, stat_c3 = st.columns(3)
            stat_c1.metric("Gross Production Value (Earnings)", f"₹{gross_op_credits:.2f}")
            stat_c2.metric("Total Advance Drawn Matrix (Upad)", f"₹{gross_op_debits:.2f}")
            stat_c3.metric("Net Salary Outstanding Payable Balance", f"₹{net_payable_salary:.2f}")
            
            if not op_production_subset.empty:
                pdf_op_blob = generate_pdf_document(op_production_subset[["Date", "Party", "Work Type", "Pcs", "Carat_20_Up", "Carat_1_Up", "Operator Amount"]], f"Production Statement For {filter_operator_target}")
                st.download_button(f"📥 Download {filter_operator_target} PDF Statement", data=pdf_op_blob, file_name=f"{filter_operator_target}_Invoice.pdf", mime="application/pdf")

    elif selected_view_ledger == "Client Party Outstanding Receivables Balances" and not df_work.empty:
        distinct_parties_logged = sorted(df_work["Party"].unique())
        if distinct_parties_logged:
            filter_party_target = st.selectbox("Select Target Client Billing Account Account:", distinct_parties_logged)
            party_billings_subset = df_work[df_work["Party"] == filter_party_target].copy().reset_index(drop=True)
            
            for party_idx, p_row in party_billings_subset.iterrows():
                with st.container():
                    px1, px2, px3, px4, px5 = st.columns([1.5, 3.5, 2.0, 1.5, 1.5])
                    px1.write(f"📅 `{p_row['Date']}`")
                    px2.write(f"**Operator:** {p_row['Operator']} | **Profile Matrix Type:** {p_row['Work Type']} | **Pcs:** {p_row['Pcs']}")
                    px3.markdown(f"Receivable Amt: **₹{p_row['Party Amount']:.2f}**")
                    
                    wa_party_msg = f"Invoice Statement Alert ({filter_party_target}):\nDate: {p_row['Date']}\nProduction Class Type: {p_row['Work Type']}\nCalculated Total Receivable: ₹{p_row['Party Amount']}"
                    px4.markdown(f"<a href='https://wa.me/?text={urllib.parse.quote(wa_party_msg)}' target='_blank'><button style='background-color:#25D366; border:none; color:white; border-radius:4px;'>💬 WhatsApp</button></a>", unsafe_allow_html=True)
                    
                    if px5.button("❌ Delete Log Record", key=f"del_party_work_row_{party_idx}"):
                        actual_df_p_idx = df_work[(df_work["Party"] == filter_party_target)].index[party_idx]
                        df_work = df_work.drop(actual_df_p_idx).reset_index(drop=True)
                        save_data(df_work, DAILY_WORK_FILE)
                        st.rerun()
                    st.markdown("<hr style='margin:2px 0; border-color:#21252b;' />", unsafe_allow_html=True)
            
            st.markdown("---")
            st.metric("Total Consolidated Account Receivables Outstanding Balance", f"₹{party_billings_subset['Party Amount'].sum():.2f}")
            
            pdf_pt_blob = generate_pdf_document(party_billings_subset[["Date", "Operator", "Work Type", "Pcs", "Carat_20_Up", "Carat_1_Up", "Party Rate", "Party Amount"]], f"Account Ledger Statement For {filter_party_target}")
            st.download_button(f"📥 Download {filter_party_target} Statement PDF Invoice", data=pdf_pt_blob, file_name=f"Party_{filter_party_target}_Ledger.pdf", mime="application/pdf")

    else:
        st.markdown("#### Complete Global Audit Raw Matrix Logs")
        if not df_work.empty:
            df_work = df_work.sort_values(by="Date", ascending=False).reset_index(drop=True)
            display_work_df = df_work.copy()
            display_work_df.index = display_work_df.index + 1
            st.dataframe(display_work_df)
        else:
            st.info("No diamond processing transactions stored inside daily registry.")
