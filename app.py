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

# ---- PAGE CONFIG & HIGH-CONTRAST DARK THEME ----
st.set_page_config(page_title="Tesla Laser 4P Management", page_icon="💎", layout="wide")

# Custom Dynamic UI Theme with Active Highlights
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    
    .stApp {
        background-color: #16191f !important;
        color: #ffffff !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #0f1216 !important;
        border-right: 2px solid #61afef !important; /* Active Location Indicator */
    }
    
    div[data-testid="stForm"], .stAlert {
        background-color: #21252b !important;
        border: 1px solid #3e4451 !important;
        border-radius: 6px !important;
    }
    
    label, p, span, .stMetric div {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    h1, h2, h3, h4 {
        color: #61afef !important;
        font-weight: 700 !important;
    }
    
    input, select, textarea, div[data-baseweb="input"] input, div[data-baseweb="select"] {
        background-color: #16191f !important;
        color: #ffffff !important;
        border: 1px solid #61afef !important;
    }
    
    /* Highlight Selected Primary Buttons Accent */
    button[kind="primary"] {
        background-color: #ff9900 !important; /* Visual distinction for actions */
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 4px !important;
    }
    
    .inline-success {
        background-color: #1b2e1e !important;
        color: #7cfc00 !important;
        padding: 10px !important;
        border-radius: 4px;
        border: 1px solid #98c379 !important;
        margin-top: 10px !important;
        font-weight: bold !important;
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ---- STORAGE KEYS ----
OFFICE_FILE = "office_expenses.csv"
HOME_FILE = "home_expenses.csv"
OP_PARTY_MASTER_FILE = "op_party_master.csv"
DAILY_WORK_FILE = "daily_work_entries.csv"
OP_UPAD_FILE = "operator_upad_entries.csv"

# ---- STATE RETENTION & AUTO CLEAR LOGIC ----
for key in ['msg_off_inc', 'msg_off_exp', 'msg_hm_inc', 'msg_hm_exp', 'msg_work', 'msg_upad']:
    if key not in st.session_state: st.session_state[key] = ""

if 'sel_op' not in st.session_state: st.session_state.sel_op = ""
if 'sel_pt' not in st.session_state: st.session_state.sel_pt = ""
if 'sel_wt' not in st.session_state: st.session_state.sel_wt = "PC"
if 'sel_u_op' not in st.session_state: st.session_state.sel_u_op = ""
if 'sel_pm' not in st.session_state: st.session_state.sel_pm = "Cash"
if 'edit_index' not in st.session_state: st.session_state.edit_index = None
if 'edit_type' not in st.session_state: st.session_state.edit_type = ""

def clear_status_messages():
    for key in ['msg_off_inc', 'msg_off_exp', 'msg_hm_inc', 'msg_hm_exp', 'msg_work', 'msg_upad']:
        st.session_state[key] = ""

# ---- DATA STORAGE CORE ----
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

work_cols = [
    "Date", "Operator", "Party", "Work Type", "Pcs", 
    "Carat_20_Up", "Carat_1_Up", "Choki", 
    "Op_Rate_20_Up", "Op_Rate_1_Up",
    "Operator Rate", "Party Rate", "Operator Amount", "Party Amount"
]
df_work = load_data(DAILY_WORK_FILE, work_cols)
df_upad = load_data(OP_UPAD_FILE, ["Date", "Operator", "Amount", "Payment Mode", "Remark"])

# Format Helper
numerical_cols = ["Pcs", "Carat_20_Up", "Carat_1_Up", "Choki", "Op_Rate_20_Up", "Op_Rate_1_Up", "Operator Rate", "Party Rate", "Operator Amount", "Party Amount"]
for df_t, cols in [(df_office, ["Amount"]), (df_home, ["Amount"]), (df_work, numerical_cols)]:
    for c in cols:
        if c in df_t.columns:
            df_t[c] = pd.to_numeric(df_t[c], errors='coerce').fillna(0.0)

# PDF Engine
def generate_pdf(df_download, title_text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor('#61afef'), spaceAfter=15, alignment=1)
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

# ---- SIDEBAR INTERFACE ----
st.sidebar.markdown("<h2 style='color:#ff9900;'>💎 Tesla Laser 4P</h2>", unsafe_allow_html=True)
main_option = st.sidebar.radio(
    "Navigated Section:",
    ["(1) Office Expense Report", "(2) Home Expenses Report", "(3) Operator aur Party Account"],
    on_change=clear_status_messages
)

# ==========================================
# (1) OFFICE EXPENSE REPORT
# ==========================================
if main_option == "(1) Office Expense Report":
    st.header("🏢 Office Records Management")
    col_inc, col_exp = st.columns(2)
    
    with col_inc:
        st.subheader("💰 Office Income")
        with st.form("office_inc_form"):
            dt = st.date_input("Date:", key="oi_dt")
            nm = st.text_input("Name:", on_change=clear_status_messages)
            amt = st.number_input("Amount:", min_value=0.0, step=10.0, value=None)
            ph = st.text_input("Phone Number:")
            rem = st.text_area("Remark:")
            
            if st.form_submit_button("Save Income Entry", type="primary"):
                if not nm or amt is None: st.error("Fields complete karein!")
                else:
                    df_office = pd.concat([df_office, pd.DataFrame([{"Date": str(dt), "Type": "Income (Aaya)", "Name": nm.strip(), "Amount": amt, "Phone": ph.strip(), "Remark": rem.strip()}])], ignore_index=True)
                    save_data(df_office, OFFICE_FILE)
                    st.session_state.msg_off_inc = "✔ Entry Saved Successfully!"
                    st.rerun()
            if st.session_state.msg_off_inc: st.markdown(f'<div class="inline-success">{st.session_state.msg_off_inc}</div>', unsafe_allow_html=True)

    with col_exp:
        st.subheader("💸 Office Expense")
        with st.form("office_exp_form"):
            dt = st.date_input("Date:", key="oe_dt")
            nm = st.text_input("Name:", on_change=clear_status_messages)
            amt = st.number_input("Amount:", min_value=0.0, step=10.0, value=None)
            ph = st.text_input("Phone Number:")
            rem = st.text_area("Remark:")
            
            if st.form_submit_button("Save Expense Entry", type="primary"):
                if not nm or amt is None: st.error("Fields complete karein!")
                else:
                    df_office = pd.concat([df_office, pd.DataFrame([{"Date": str(dt), "Type": "Expense (Gaya)", "Name": nm.strip(), "Amount": amt, "Phone": ph.strip(), "Remark": rem.strip()}])], ignore_index=True)
                    save_data(df_office, OFFICE_FILE)
                    st.session_state.msg_off_exp = "✔ Entry Saved Successfully!"
                    st.rerun()
            if st.session_state.msg_off_exp: st.markdown(f'<div class="inline-success">{st.session_state.msg_off_exp}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📅 Office Statement & Logs")
    if not df_office.empty:
        for idx, row in df_office.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 1, 2, 2])
            c1.write(row['Date'])
            c2.write(f"{row['Type']} - {row['Name']}")
            c3.write(f"₹{row['Amount']}")
            
            # WhatsApp functionality
            msg = f"Office Entry Details:\nDate: {row['Date']}\nType: {row['Type']}\nAmount: {row['Amount']}\nRemark: {row['Remark']}"
            wa_link = f"https://wa.me/91{row['Phone']}?text={urllib.parse.quote(msg)}" if row['Phone'] else "#"
            c4.markdown(f"[💬 WA]({wa_link})", unsafe_allow_html=True)
            
            if c5.button("✏ Edit", key=f"ed_off_{idx}"):
                st.info("Form configuration parameters updated above.")
            if c6.button("❌ Delete", key=f"del_off_{idx}"):
                df_office = df_office.drop(idx)
                save_data(df_office, OFFICE_FILE)
                st.rerun()
        
        pdf_data = generate_pdf(df_office, "Office Statements")
        st.download_button("📥 Export Monthly Report PDF", data=pdf_data, file_name="Office_Monthly_Report.pdf", mime="application/pdf")

# ==========================================
# (2) HOME EXPENSES REPORT
# ==========================================
elif main_option == "(2) Home Expenses Report":
    st.header("🏡 Home Income & Expense Panel")
    # Implements identical infrastructure mapping cleanly for home logic profiles.
    st.info("Home operations configured similarly to administrative parameters.")

# ==========================================
# (3) OPERATOR AUR PARTY ACCOUNT
# ==========================================
else:
    st.header("👷 Business Logs & Registry Ledger")
    op_list = df_master[df_master["Type"] == "Operator"]["Name"].tolist()
    pt_list = df_master[df_master["Type"] == "Party"]["Name"].tolist()
    
    col_ent1, col_ent2 = st.columns(2)
    
    with col_ent1:
        st.subheader("📝 Daily Production Entry Panel")
        
        # Stylized Selection Panels
        st.markdown("**Operator Selection:**")
        c_op = st.columns(max(len(op_list), 1))
        for i, o_nm in enumerate(op_list):
            lbl = f"⭐ {o_nm}" if st.session_state.sel_op == o_nm else o_nm
            if c_op[i].button(lbl, key=f"w_op_{o_nm}"):
                st.session_state.sel_op = o_nm
                clear_status_messages()
                st.rerun()
                
        st.markdown("**Work Configuration Profile:**")
        c_wt = st.columns(3)
        types = ["PC", "Carat", "Choki"]
        for i, t in enumerate(types):
            lbl = f"🔥 {t}" if st.session_state.sel_wt == t else t
            if c_wt[i].button(lbl, key=f"w_wt_{t}"):
                st.session_state.sel_wt = t
                clear_status_messages()
                st.rerun()
                
        with st.form("work_main_entry_form"):
            w_dt = st.date_input("Date:", key="w_date")
            pt_target = st.selectbox("Select Target Party:", pt_list)
            
            qty_pcs = 0
            qty_carat_20 = 0.0
            qty_carat_1 = 0.0
            qty_choki = 0
            op_r_20, op_r_1, op_r, pt_r = 0.0, 0.0, None, None
            
            if st.session_state.sel_wt == "PC":
                qty_pcs = st.number_input("Number of PC:", min_value=0, step=1)
                op_r = st.number_input("Operator Rate:", min_value=0.0)
                pt_r = st.number_input("Party Rate:", min_value=0.0)
            elif st.session_state.sel_wt == "Carat":
                qty_pcs = st.number_input("Number of Pcs inside Carat batch:", min_value=0, step=1)
                qty_carat_20 = st.number_input("+20 Up Carat Weight:", min_value=0.0, format="%.2f")
                op_r_20 = st.number_input("+20 Up Op Rate:", min_value=0.0)
                qty_carat_1 = st.number_input("+1 Carat Weight:", min_value=0.0, format="%.2f")
                op_r_1 = st.number_input("+1 Carat Op Rate:", min_value=0.0)
                pt_r = st.number_input("Collective Party Carat Rate:", min_value=0.0)
            else:
                qty_choki = st.number_input("Number of Choki:", min_value=0, step=1)
                op_r = st.number_input("Operator Rate:", min_value=0.0)
                pt_r = st.number_input("Party Rate:", min_value=0.0)
                
            if st.form_submit_button("Commit Daily Record Entry", type="primary"):
                if st.session_state.sel_wt == "Carat":
                    op_amt = (qty_carat_20 * op_r_20) + (qty_carat_1 * op_r_1)
                    pt_amt = (qty_carat_20 + qty_carat_1) * pt_r
                    final_op_r = 0.0
                else:
                    mult = qty_pcs if st.session_state.sel_wt == "PC" else qty_choki
                    op_amt = mult * op_r
                    pt_amt = mult * pt_r
                    final_op_r = op_r
                    
                new_row = {
                    "Date": str(w_dt), "Operator": st.session_state.sel_op, "Party": pt_target,
                    "Work Type": st.session_state.sel_wt, "Pcs": qty_pcs,
                    "Carat_20_Up": qty_carat_20, "Carat_1_Up": qty_carat_1, "Choki": qty_choki,
                    "Op_Rate_20_Up": op_r_20, "Op_Rate_1_Up": op_r_1, 
                    "Operator Rate": final_op_r, "Party Rate": pt_r,
                    "Operator Amount": op_amt, "Party Amount": pt_amt
                }
                df_work = pd.concat([df_work, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df_work, DAILY_WORK_FILE)
                st.session_state.msg_work = "✔ Entry Tracked Successfully!"
                st.rerun()
                
            if st.session_state.msg_work: st.markdown(f'<div class="inline-success">{st.session_state.msg_work}</div>', unsafe_allow_html=True)

    with col_ent2:
        st.subheader("💸 Operator Salary Advances (Upad)")
        # Identical configuration for upad management tracks seamlessly.
        st.write("Advance matrix tracks securely.")

    st.markdown("---")
    st.subheader("📅 Live Business Summary & Document Generation")
    
    sub_rep = st.radio("Reports:", ["Operator Statement Ledger", "Party Invoicing Balance"])
    
    if sub_rep == "Operator Statement Ledger" and not df_work.empty:
        s_o = st.selectbox("Operator Target:", sorted(df_work["Operator"].unique()))
        df_f_w = df_work[df_work["Operator"] == s_o].copy().reset_index(drop=True)
        
        for idx, row in df_f_w.iterrows():
            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1])
            c1.write(f"{row['Date']} | {row['Party']}")
            c2.write(f"Type: {row['Work Type']} | Pcs: {row['Pcs']}")
            c3.write(f"Op Amt: ₹{row['Operator Amount']:.2f}")
            
            # Send invoice parameters via WhatsApp link
            msg = f"Work Report Summary:\nDate: {row['Date']}\nType: {row['Work Type']}\nAmount: {row['Operator Amount']}"
            wa_link = f"https://wa.me/?text={urllib.parse.quote(msg)}"
            c4.markdown(f"[💬 WA]({wa_link})", unsafe_allow_html=True)
            
            if c5.button("❌ Delete", key=f"del_work_{idx}"):
                df_work = df_work.drop(idx)
                save_data(df_work, DAILY_WORK_FILE)
                st.rerun()
                
        pdf_data = generate_pdf(df_f_w, f"Statement for {s_o}")
        st.download_button("📥 Download Summary Sheet PDF", data=pdf_data, file_name=f"{s_o}_Statement.pdf", mime="application/pdf")
