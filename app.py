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

# ---- PAGE CONFIG & HIGH-CONTRAST PROFESSIONAL DARK THEME ----
st.set_page_config(page_title="Tesla Laser 4P Management", page_icon="💎", layout="wide")

# Custom Professional High-Contrast Theme (Deep Charcoal, Pure White text, Diamond Blue accents)
st.markdown("""
    <style>
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    
    /* Global Text and Background Contrast */
    .stApp {
        background-color: #16191f !important;
        color: #ffffff !important;
    }
    
    /* Sidebar Text & styling */
    section[data-testid="stSidebar"] {
        background-color: #0f1216 !important;
        border-right: 1px solid #2d3139 !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    
    /* Box/Container styling */
    div[data-testid="stForm"], .stAlert, div[data-testid="element-container"] div.stMarkdown {
        background-color: #21252b !important;
        border: 1px solid #3e4451 !important;
        border-radius: 6px !important;
    }
    
    /* All Labels Bright & Visible */
    label, p, span, .stMetric div {
        color: #ffffff !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }
    
    /* Subheadings Contrast */
    h1, h2, h3, h4, h5, h6 {
        color: #61afef !important;
        font-weight: 700 !important;
    }
    
    /* Inputs Text Visibility */
    input, select, textarea, div[data-baseweb="input"] input, div[data-baseweb="select"] {
        background-color: #16191f !important;
        color: #ffffff !important;
        border: 1px solid #3e4451 !important;
    }
    
    /* Dataframe Table Text Color */
    .stDataFrame div, table, tr, td, th {
        color: #ffffff !important;
    }
    
    /* Primary buttons (Save/Execute) */
    button[kind="primary"], div.stButton > button:first-child {
        background-color: #4a75a0 !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: bold !important;
        width: 100% !important;
        border-radius: 4px !important;
        padding: 10px !important;
    }
    
    button[kind="primary"]:hover, div.stButton > button:first-child:hover {
        background-color: #5b87b3 !important;
    }
    
    /* Form Inline Message Design */
    .inline-success {
        background-color: #1b2e1e !important;
        color: #7cfc00 !important;
        padding: 10px !important;
        border-radius: 4px !important;
        border: 1px solid #98c379 !important;
        margin-top: 10px !important;
        font-size: 15px !important;
        font-weight: bold !important;
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ---- FILE STORAGE SETTINGS ----
OFFICE_FILE = "office_expenses.csv"
HOME_FILE = "home_expenses.csv"
OP_PARTY_MASTER_FILE = "op_party_master.csv"
DAILY_WORK_FILE = "daily_work_entries.csv"
OP_UPAD_FILE = "operator_upad_entries.csv"

# ---- PERSISTENT STATE MANAGEMENT ----
if 'msg_off_inc' not in st.session_state: st.session_state.msg_off_inc = ""
if 'msg_off_exp' not in st.session_state: st.session_state.msg_off_exp = ""
if 'msg_hm_inc' not in st.session_state: st.session_state.msg_hm_inc = ""
if 'msg_hm_exp' not in st.session_state: st.session_state.msg_hm_exp = ""
if 'msg_work' not in st.session_state: st.session_state.msg_work = ""
if 'msg_upad' not in st.session_state: st.session_state.msg_upad = ""

if 'sel_op' not in st.session_state: st.session_state.sel_op = ""
if 'sel_pt' not in st.session_state: st.session_state.sel_pt = ""
if 'sel_wt' not in st.session_state: st.session_state.sel_wt = "PC"
if 'sel_u_op' not in st.session_state: st.session_state.sel_u_op = ""
if 'sel_pm' not in st.session_state: st.session_state.sel_pm = "Cash"

# Helper Function to clear all messages on tab/menu switch
def clear_all_messages():
    for key in ['msg_off_inc', 'msg_off_exp', 'msg_hm_inc', 'msg_hm_exp', 'msg_work', 'msg_upad']:
        st.session_state[key] = ""

# ---- DATA HANDLING CORE ----
def load_data(file_path, columns):
    if os.path.exists(file_path):
        try: return pd.read_csv(file_path)
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

df_master = load_data(OP_PARTY_MASTER_FILE, ["Type", "Name"])
df_office = load_data(OFFICE_FILE, ["Date", "Type", "Name", "Amount", "Phone", "Remark"])
df_home = load_data(HOME_FILE, ["Date", "Type", "Name", "Amount", "Phone", "Remark"])

# Kept standardized columns for tracking data structured accurately
work_cols = [
    "Date", "Operator", "Party", "Work Type", "Pcs", 
    "Carat_20_Up", "Carat_1_Up", "Choki", 
    "Op_Rate_20_Up", "Op_Rate_1_Up",
    "Operator Rate", "Party Rate", "Operator Amount", "Party Amount"
]
df_work = load_data(DAILY_WORK_FILE, work_cols)
df_upad = load_data(OP_UPAD_FILE, ["Date", "Operator", "Amount", "Payment Mode", "Remark"])

# Formats numerical data cleanly
numerical_cols = [
    "Pcs", "Carat_20_Up", "Carat_1_Up", "Choki", 
    "Op_Rate_20_Up", "Op_Rate_1_Up",
    "Operator Rate", "Party Rate", "Operator Amount", "Party Amount"
]
for df_t, cols in [(df_office, ["Amount"]), (df_home, ["Amount"]), (df_work, numerical_cols)]:
    for c in cols:
        if c in df_t.columns:
            df_t[c] = pd.to_numeric(df_t[c], errors='coerce').fillna(0.0)

# WhatsApp Link Generator
def get_whatsapp_link(phone, message):
    if not phone: return ""
    phone_clean = "".join(c for c in str(phone) if c.isdigit())
    if len(phone_clean) == 10: phone_clean = "91" + phone_clean
    return f"https://wa.me/{phone_clean}?text={urllib.parse.quote(message)}"

# PDF Generator
def generate_pdf(df_download, title_text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, textColor=colors.HexColor('#4a75a0'), spaceAfter=15, alignment=1)
    cell_style = ParagraphStyle('CStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, spaceAfter=2)
    header_style = ParagraphStyle('HStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.white)
    
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 10))
    columns = df_download.columns.tolist()
    data = [[Paragraph(str(col), header_style) for col in columns]]
    
    for _, row in df_download.iterrows():
        data.append([Paragraph(str(row[col]), cell_style) for col in columns])
        
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f242d')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# Custom Contact Picker Logic
def render_contact_picker(key_suffix):
    html_code = f"""
    <div style="font-family: sans-serif; margin-bottom: 5px;">
        <button id="pick_{key_suffix}" style="background-color: #2b313d; color: #61afef; border: 1px solid #3e4451; padding: 6px 12px; font-weight: bold; border-radius: 4px; cursor: pointer; width: 100%;">
            📇 Select Contact from Mobile List
        </button>
        <p id="st_{key_suffix}" style="font-size: 11px; color: #ffffff; margin-top: 3px; margin-bottom:0; text-align:center; font-weight: bold;"></p>
    </div>
    <script>
        document.getElementById('pick_{key_suffix}').addEventListener('click', async () => {{
            const st = document.getElementById('st_{key_suffix}');
            if (!('contacts' in navigator)) {{
                st.innerText = "Niche box me haath se number likhein."; return;
            }}
            try {{
                const contacts = await navigator.contacts.select(['tel'], {{ multiple: false }});
                if (contacts.length > 0 && contacts[0].tel.length > 0) {{
                    st.innerText = "Copy & Paste this: " + contacts[0].tel[0].replace(/[^\\d]/g, '');
                    st.style.color = "#7cfc00";
                }}
            }} catch (err) {{ }}
        }});
    </script>
    """
    components.html(html_code, height=45)

# ---- SIDEBAR MENU INTERFACE ----
st.sidebar.title("💎 Tesla Laser 4P")
main_option = st.sidebar.radio(
    "Select Section / Report:",
    ["(1) Office Expense Report", "(2) Home Expenses Report", "(3) Operator aur Party Account"],
    on_change=clear_all_messages
)

# ==========================================
# (1) OFFICE EXPENSE REPORT
# ==========================================
if main_option == "(1) Office Expense Report":
    st.header("🏢 Office Income & Expense Management")
    col_inc, col_exp = st.columns(2)
    
    with col_inc:
        st.subheader("💰 Office Income (Paisa Aaya)")
        render_contact_picker("off_i")
        with st.form("office_inc_form"):
            dt = st.date_input("Date:", key="oi_dt")
            nm = st.text_input("Jis Party Se Paisa Aaya Uska Nam:")
            amt = st.number_input("Amount (Rs):", min_value=0.0, step=10.0, value=None, placeholder="Amount dalein...")
            ph = st.text_input("Phone Number:")
            rem = st.text_area("Remark / Notes:")
            
            if st.form_submit_button("Save Income Entry"):
                if not nm or amt is None: st.error("Nam aur Amount bharein!")
                else:
                    df_office = pd.concat([df_office, pd.DataFrame([{"Date": str(dt), "Type": "Income (Aaya)", "Name": nm.strip(), "Amount": amt, "Phone": ph.strip(), "Remark": rem.strip()}])], ignore_index=True)
                    save_data(df_office, OFFICE_FILE)
                    st.session_state.msg_off_inc = "✔ Saved Successfully!"
                    st.rerun()
            
            if st.session_state.msg_off_inc:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_off_inc}</div>', unsafe_allow_html=True)

    with col_exp:
        st.subheader("💸 Office Expense (Paisa Gaya)")
        render_contact_picker("off_e")
        with st.form("office_exp_form"):
            dt = st.date_input("Date:", key="oe_dt")
            nm = st.text_input("Jise Paisa De Rahe Hai Uska Nam:")
            amt = st.number_input("Amount (Rs):", min_value=0.0, step=10.0, value=None, placeholder="Amount dalein...")
            ph = st.text_input("Phone Number:")
            rem = st.text_area("Remark / Notes:")
            
            if st.form_submit_button("Save Expense Entry"):
                if not nm or amt is None: st.error("Nam aur Amount bharein!")
                else:
                    df_office = pd.concat([df_office, pd.DataFrame([{"Date": str(dt), "Type": "Expense (Gaya)", "Name": nm.strip(), "Amount": amt, "Phone": ph.strip(), "Remark": rem.strip()}])], ignore_index=True)
                    save_data(df_office, OFFICE_FILE)
                    st.session_state.msg_off_exp = "✔ Saved Successfully!"
                    st.rerun()
            
            if st.session_state.msg_off_exp:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_off_exp}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📅 Office Monthly Report & Actions")
    if not df_office.empty:
        df_office = df_office.sort_values(by="Date", ascending=False).reset_index(drop=True)
        display_df = df_office.copy()
        display_df.index = display_df.index + 1
        st.dataframe(display_df[["Date", "Type", "Name", "Amount", "Phone", "Remark"]])
        
        pdf_data = generate_pdf(display_df[["Date", "Type", "Name", "Amount", "Phone", "Remark"]], "Office Income & Expense Report")
        st.download_button("📥 Download Report PDF", data=pdf_data, file_name="Office_Report.pdf", mime="application/pdf")

# ==========================================
# (2) HOME EXPENSES REPORT
# ==========================================
elif main_option == "(2) Home Expenses Report":
    st.header("🏡 Home Income & Expense Management")
    col_inc, col_exp = st.columns(2)
    
    with col_inc:
        st.subheader("💰 Home Income (Paisa Aaya)")
        render_contact_picker("hm_i")
        with st.form("home_inc_form"):
            dt = st.date_input("Date:", key="hi_dt")
            nm = st.text_input("Kahan Se Paisa Aaya:")
            amt = st.number_input("Amount (Rs):", min_value=0.0, step=10.0, value=None, placeholder="Amount dalein...")
            ph = st.text_input("Phone Number:")
            rem = st.text_area("Remark / Notes:")
            
            if st.form_submit_button("Save Income Entry"):
                if not nm or amt is None: st.error("Nam aur Amount bharein!")
                else:
                    df_home = pd.concat([df_home, pd.DataFrame([{"Date": str(dt), "Type": "Income (Aaya)", "Name": nm.strip(), "Amount": amt, "Phone": ph.strip(), "Remark": rem.strip()}])], ignore_index=True)
                    save_data(df_home, HOME_FILE)
                    st.session_state.msg_hm_inc = "✔ Saved Successfully!"
                    st.rerun()
            
            if st.session_state.msg_hm_inc:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_hm_inc}</div>', unsafe_allow_html=True)

    with col_exp:
        st.subheader("💸 Home Expense (Paisa Gaya)")
        render_contact_picker("hm_e")
        with st.form("home_exp_form"):
            dt = st.date_input("Date:", key="he_dt")
            nm = st.text_input("Jise Paisa De Rahe Hai Uska Nam:")
            amt = st.number_input("Amount (Rs):", min_value=0.0, step=10.0, value=None, placeholder="Amount dalein...")
            ph = st.text_input("Phone Number:")
            rem = st.text_area("Remark / Notes:")
            
            if st.form_submit_button("Save Expense Entry"):
                if not nm or amt is None: st.error("Nam aur Amount bharein!")
                else:
                    df_home = pd.concat([df_home, pd.DataFrame([{"Date": str(dt), "Type": "Expense (Gaya)", "Name": nm.strip(), "Amount": amt, "Phone": ph.strip(), "Remark": rem.strip()}])], ignore_index=True)
                    save_data(df_home, HOME_FILE)
                    st.session_state.msg_hm_exp = "✔ Saved Successfully!"
                    st.rerun()
            
            if st.session_state.msg_hm_exp:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_hm_exp}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📅 Home Monthly Report & Actions")
    if not df_home.empty:
        df_home = df_home.sort_values(by="Date", ascending=False).reset_index(drop=True)
        display_df = df_home.copy()
        display_df.index = display_df.index + 1
        st.dataframe(display_df[["Date", "Type", "Name", "Amount", "Phone", "Remark"]])

# ==========================================
# (3) OPERATOR AUR PARTY ACCOUNT
# ==========================================
else:
    st.header("👷 Master Registry, Work & Upad Records")
    
    op_list = df_master[df_master["Type"] == "Operator"]["Name"].tolist()
    pt_list = df_master[df_master["Type"] == "Party"]["Name"].tolist()
    
    # MASTER SETUP
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        st.subheader("Manage Operators")
        with st.form("op_m_form"):
            name_in = st.text_input("Operator Name:")
            act = st.selectbox("Action:", ["Add", "Remove"])
            if st.form_submit_button("Execute"):
                if act == "Add" and name_in.strip():
                    if not ((df_master['Type'] == 'Operator') & (df_master['Name'] == name_in.strip())).any():
                        df_master = pd.concat([df_master, pd.DataFrame([{"Type": "Operator", "Name": name_in.strip()}])], ignore_index=True)
                        save_data(df_master, OP_PARTY_MASTER_FILE)
                        st.rerun()
                elif act == "Remove" and name_in.strip():
                    df_master = df_master[~((df_master['Type'] == 'Operator') & (df_master['Name'] == name_in.strip()))]
                    save_data(df_master, OP_PARTY_MASTER_FILE)
                    st.rerun()

    with c_m2:
        st.subheader("Manage Parties")
        with st.form("pt_m_form"):
            name_in = st.text_input("Party Name:")
            act = st.selectbox("Action:", ["Add", "Remove"])
            if st.form_submit_button("Execute"):
                if act == "Add" and name_in.strip():
                    if not ((df_master['Type'] == 'Party') & (df_master['Name'] == name_in.strip())).any():
                        df_master = pd.concat([df_master, pd.DataFrame([{"Type": "Party", "Name": name_in.strip()}])], ignore_index=True)
                        save_data(df_master, OP_PARTY_MASTER_FILE)
                        st.rerun()
                elif act == "Remove" and name_in.strip():
                    df_master = df_master[~((df_master['Type'] == 'Party') & (df_master['Name'] == name_in.strip()))]
                    save_data(df_master, OP_PARTY_MASTER_FILE)
                    st.rerun()

    st.markdown("---")
    col_ent1, col_ent2 = st.columns(2)
    
    # --- PANEL 1: DAILY WORK FORM ---
    with col_ent1:
        st.subheader("📝 Daily Work Entry Panel")
        
        st.markdown("**Click Select Operator:**")
        if op_list:
            c_op = st.columns(min(len(op_list), 4))
            for i, o_nm in enumerate(op_list):
                with c_op[i % 4]:
                    if st.button(o_nm, key=f"work_op_{o_nm}", type="primary" if st.session_state.sel_op == o_nm else "secondary"):
                        st.session_state.sel_op = o_nm
                        st.rerun()
                        
        st.markdown("**Click Select Party:**")
        if pt_list:
            c_pt = st.columns(min(len(pt_list), 4))
            for i, p_nm in enumerate(pt_list):
                with c_pt[i % 4]:
                    if st.button(p_nm, key=f"work_pt_{p_nm}", type="primary" if st.session_state.sel_pt == p_nm else "secondary"):
                        st.session_state.sel_pt = p_nm
                        st.rerun()

        st.markdown("**Click Select Work Type:**")
        c_wt = st.columns(3)
        with c_wt[0]:
            if st.button("🔴 PC", type="primary" if st.session_state.sel_wt == "PC" else "secondary"):
                st.session_state.sel_wt = "PC"
                st.rerun()
        with c_wt[1]:
            if st.button("🟢 Carat", type="primary" if st.session_state.sel_wt == "Carat" else "secondary"):
                st.session_state.sel_wt = "Carat"
                st.rerun()
        with c_wt[2]:
            if st.button("🔵 Choki", type="primary" if st.session_state.sel_wt == "Choki" else "secondary"):
                st.session_state.sel_wt = "Choki"
                st.rerun()

        st.info(f"👉 Active -> Op: `{st.session_state.sel_op}` | Pt: `{st.session_state.sel_pt}` | Type: `{st.session_state.sel_wt}`")
        
        with st.form("save_work_form"):
            w_dt = st.date_input("Date:", key="w_date")
            
            qty_pcs = 0
            qty_carat_20 = 0.0
            qty_carat_1 = 0.0
            qty_choki = 0
            
            # Initializing input state variables
            op_r, pt_r = None, None
            op_r_20, op_r_1 = 0.0, 0.0
            
            # Conditionally render inputs based on Selection
            if st.session_state.sel_wt == "PC":
                qty_pcs = st.number_input("Number of PC:", min_value=0, value=0, step=1)
                op_r = st.number_input("Operator Rate (per PC):", min_value=0.0, step=0.1, value=None, placeholder="Type Rate...")
                pt_r = st.number_input("Party Rate (per PC):", min_value=0.0, step=0.1, value=None, placeholder="Type Rate...")
                
            elif st.session_state.sel_wt == "Carat":
                st.markdown("<p style='color:#61afef; font-weight:bold; margin-bottom:2px;'>Carat Weights & Rates Configuration:</p>", unsafe_allow_html=True)
                
                # Weight entries
                c_w1, c_w2 = st.columns(2)
                with c_w1:
                    qty_carat_20 = st.number_input("+20 Up Weight:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
                with c_w2:
                    qty_carat_1 = st.number_input("+1 Carat Weight:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
                
                # Rates: Operator has split rates, Party has a single combined rate
                st.markdown("<p style='color:#ffffff; font-size:13px; margin-top:5px; margin-bottom:2px;'>💰 Rate Entry (Op details separate | Party collective)</p>", unsafe_allow_html=True)
                c_r1, c_r2, c_r3 = st.columns(3)
                with c_r1:
                    op_r_20 = st.number_input("+20 Up Op Rate:", min_value=0.0, value=0.0, step=0.1, format="%.1f")
                with c_r2:
                    op_r_1 = st.number_input("+1 Carat Op Rate:", min_value=0.0, value=0.0, step=0.1, format="%.1f")
                with c_r3:
                    pt_r = st.number_input("Party Carat Rate (Total):", min_value=0.0, step=0.1, value=None, placeholder="Type Rate...")
            
            else:
                qty_choki = st.number_input("Number of Choki:", min_value=0, value=0, step=1)
                op_r = st.number_input("Operator Rate (per Choki):", min_value=0.0, step=0.1, value=None, placeholder="Type Rate...")
                pt_r = st.number_input("Party Rate (per Choki):", min_value=0.0, step=0.1, value=None, placeholder="Type Rate...")
                
            if st.form_submit_button("Save Work Entry"):
                if not st.session_state.sel_op or not st.session_state.sel_pt:
                    st.error("Operator aur Party select karein!")
                elif pt_r is None or (st.session_state.sel_wt != "Carat" and op_r is None):
                    st.error("Rates bharein!")
                else:
                    # Calculate Amounts based on logic requirements
                    if st.session_state.sel_wt == "PC":
                        op_amt = qty_pcs * op_r
                        pt_amt = qty_pcs * pt_r
                        final_op_r = op_r
                    elif st.session_state.sel_wt == "Carat":
                        # Operator: Separate split multiplication
                        op_amt = (qty_carat_20 * op_r_20) + (qty_carat_1 * op_r_1)
                        # Party: Merged total calculation (as requested)
                        pt_amt = (qty_carat_20 + qty_carat_1) * pt_r
                        final_op_r = 0.0
                    else:
                        op_amt = qty_choki * op_r
                        pt_amt = qty_choki * pt_r
                        final_op_r = op_r
                    
                    new_row = {
                        "Date": str(w_dt), "Operator": st.session_state.sel_op, "Party": st.session_state.sel_pt,
                        "Work Type": st.session_state.sel_wt, "Pcs": qty_pcs,
                        "Carat_20_Up": qty_carat_20, "Carat_1_Up": qty_carat_1, "Choki": qty_choki,
                        "Op_Rate_20_Up": op_r_20, "Op_Rate_1_Up": op_r_1, 
                        "Operator Rate": final_op_r, "Party Rate": pt_r,
                        "Operator Amount": op_amt, "Party Amount": pt_amt
                    }
                    df_work = pd.concat([df_work, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df_work, DAILY_WORK_FILE)
                    st.session_state.msg_work = "✔ Saved Successfully!"
                    st.rerun()
            
            if st.session_state.msg_work:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_work}</div>', unsafe_allow_html=True)

    # --- PANEL 2: OPERATOR UPAD FORM ---
    with col_ent2:
        st.subheader("💸 Operator Upad Entry Panel")
        
        st.markdown("**Click Select Operator for Upad:**")
        if op_list:
            c_u_op = st.columns(min(len(op_list), 4))
            for i, o_nm in enumerate(op_list):
                with c_u_op[i % 4]:
                    if st.button(o_nm, key=f"upad_op_{o_nm}", type="primary" if st.session_state.sel_u_op == o_nm else "secondary"):
                        st.session_state.sel_u_op = o_nm
                        st.rerun()
                        
        st.markdown("**Click Payment Mode:**")
        c_pm = st.columns(2)
        with c_pm[0]:
            if st.button("💵 Cash", type="primary" if st.session_state.sel_pm == "Cash" else "secondary"):
                st.session_state.sel_pm = "Cash"
                st.rerun()
        with c_pm[1]:
            if st.button("📱 GPay", type="primary" if st.session_state.sel_pm == "GPay" else "secondary"):
                st.session_state.sel_pm = "GPay"
                st.rerun()

        st.info(f"👉 Active Upad -> Op: `{st.session_state.sel_u_op}` | Mode: `{st.session_state.sel_pm}`")
        
        with st.form("save_upad_form"):
            u_dt = st.date_input("Date:", key="u_date")
            u_amt = st.number_input("Upad Amount (Rs):", min_value=0.0, step=50.0, value=None, placeholder="Upad daalein...")
            u_rem = st.text_area("Remark:")
            
            if st.form_submit_button("Save Upad Entry"):
                if not st.session_state.sel_u_op or u_amt is None:
                    st.error("Operator aur Amount fill karein!")
                else:
                    df_upad = pd.concat([df_upad, pd.DataFrame([{"Date": str(u_dt), "Operator": st.session_state.sel_u_op, "Amount": u_amt, "Payment Mode": st.session_state.sel_pm, "Remark": u_rem.strip()}])], ignore_index=True)
                    save_data(df_upad, OP_UPAD_FILE)
                    st.session_state.msg_upad = "✔ Saved Successfully!"
                    st.rerun()
            
            if st.session_state.msg_upad:
                st.markdown(f'<div class="inline-success">{st.session_state.msg_upad}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📅 Live Business Summary Sheets")
    
    sub_rep = st.radio("Select Summary Ledger:", ["Operator Statement Ledger", "Party Invoicing Balance", "Raw Daily Logs Summary"])
    
    if sub_rep == "Operator Statement Ledger" and (not df_work.empty or not df_upad.empty):
        all_ops = sorted(list(set(df_work["Operator"].unique()).union(set(df_upad["Operator"].unique()))))
        if all_ops:
            s_o = st.selectbox("Select Operator:", all_ops)
            st.markdown("### Work Record Summary")
            df_f_w = df_work[df_work["Operator"] == s_o].copy().reset_index(drop=True)
            if not df_f_w.empty:
                df_f_w.index = df_f_w.index + 1
                st.dataframe(df_f_w[["Date", "Party", "Work Type", "Pcs", "Carat_20_Up", "Carat_1_Up", "Choki", "Op_Rate_20_Up", "Op_Rate_1_Up", "Operator Amount"]])
            
            st.markdown("### Upad History Logs")
            df_f_u = df_upad[df_upad["Operator"] == s_o].copy().reset_index(drop=True)
            if not df_f_u.empty:
                df_f_u.index = df_f_u.index + 1
                st.dataframe(df_f_u[["Date", "Amount", "Payment Mode", "Remark"]])
                
            w_sum = df_f_w["Operator Amount"].sum() if not df_f_w.empty else 0.0
            u_sum = df_f_u["Amount"].sum() if not df_f_u.empty else 0.0
            
            col_st1, col_st2, col_st3 = st.columns(3)
            col_st1.metric("Gross Earnings Total", f"₹{w_sum:.2f}")
            col_st2.metric("Total Advances Collected (Upad)", f"₹{u_sum:.2f}")
            col_st3.metric("Net Salary Balance (Payable)", f"₹{w_sum - u_sum:.2f}")

    elif sub_rep == "Party Invoicing Balance" and not df_work.empty:
        s_p = st.selectbox("Select Target Party:", sorted(df_work["Party"].unique()))
        df_p = df_work[df_work["Party"] == s_p].copy().reset_index(drop=True)
        df_p.index = df_p.index + 1
        st.dataframe(df_p[["Date", "Operator", "Work Type", "Pcs", "Carat_20_Up", "Carat_1_Up", "Choki", "Party Rate", "Party Amount"]])
        st.metric("Total Accounts Receivables Outstanding", f"₹{df_p['Party Amount'].sum():.2f}")
        
    else:
        if not df_work.empty:
            st.markdown("### Master Raw Logs")
            df_work = df_work.sort_values(by="Date", ascending=False).reset_index(drop=True)
            d_df = df_work.copy()
            d_df.index = d_df.index + 1
            st.dataframe(d_df)
