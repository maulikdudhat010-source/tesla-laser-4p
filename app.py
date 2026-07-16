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

# Page Config
st.set_page_config(page_title="Tesla Laser 4P", page_icon="💎", layout="wide")

# ---- INITIAL STATE MANAGEMENT (CRITICAL FIX FOR ERRORS) ----
if 'current_screen' not in st.session_state: st.session_state.current_screen = "Main Menu"
if 'success_msg' not in st.session_state: st.session_state.success_msg = ""
if 'sel_op' not in st.session_state: st.session_state.sel_op = ""
if 'sel_pt' not in st.session_state: st.session_state.sel_pt = ""
if 'sel_wt' not in st.session_state: st.session_state.sel_wt = "PC"
if 'sel_u_op' not in st.session_state: st.session_state.sel_u_op = ""
if 'sel_pm' not in st.session_state: st.session_state.sel_pm = "Cash"

# ADVANCED CSS: Hide Streamlit watermarks and custom button styles
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stFooter"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    div.stButton > button {
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ---- FILE STORAGE NAMES ----
OFFICE_FILE = "office_expenses.csv"
HOME_FILE = "home_expenses.csv"
OP_PARTY_MASTER_FILE = "op_party_master.csv"
DAILY_WORK_FILE = "daily_work_entries.csv"
OP_UPAD_FILE = "operator_upad_entries.csv"

# ---- HELPER FUNCTIONS FOR DATA ----
def load_data(file_path, columns):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# Initialize data
df_master = load_data(OP_PARTY_MASTER_FILE, ["Type", "Name"])
df_office = load_data(OFFICE_FILE, ["Date", "Type", "Name", "Amount", "Phone", "Remark"])
df_home = load_data(HOME_FILE, ["Date", "Type", "Name", "Amount", "Phone", "Remark"])

work_cols = ["Date", "Operator", "Party", "Work Type", "Pcs", "Carats", "Choki", "Operator Rate", "Party Rate", "Operator Amount", "Party Amount"]
df_work = load_data(DAILY_WORK_FILE, work_cols)

upad_cols = ["Date", "Operator", "Amount", "Payment Mode", "Remark"]
df_upad = load_data(OP_UPAD_FILE, upad_cols)

def get_whatsapp_link(phone, message):
    if not phone:
        return ""
    phone_clean = "".join(c for c in str(phone) if c.isdigit())
    if len(phone_clean) == 10:
        phone_clean = "91" + phone_clean
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{phone_clean}?text={encoded_msg}"

def generate_pdf(df_download, title_text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, textColor=colors.HexColor('#1A365D'), spaceAfter=15, alignment=1)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, spaceAfter=2)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.white)
    
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 10))
    
    columns = df_download.columns.tolist()
    data = [[Paragraph(str(col), header_style) for col in columns]]
    
    for idx, row in df_download.iterrows():
        row_cells = []
        for col in columns:
            row_cells.append(Paragraph(str(row[col]), cell_style))
        data.append(row_cells)
        
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')])
    ]))
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# Custom Contact Picker Component using HTML5 Contact Picker API
def contact_picker_html(key_suffix):
    html_code = f"""
    <div style="font-family: sans-serif; margin-bottom: 10px;">
        <button id="pickContactBtn_{key_suffix}" style="background-color: #FF4B4B; color: white; border: none; padding: 8px 16px; font-weight: bold; border-radius: 4px; cursor: pointer; width: 100%;">
            📇 Select Contact from Mobile
        </button>
        <p id="status_{key_suffix}" style="font-size: 12px; color: #555; margin-top: 5px; word-break: break-all;">Mobile contact list kholne ke liye upar click karein.</p>
    </div>
    <script>
        const btn = document.getElementById('pickContactBtn_{key_suffix}');
        const status = document.getElementById('status_{key_suffix}');
        
        btn.addEventListener('click', async () => {{
            if (!('contacts' in navigator && 'select' in navigator.contacts)) {{
                status.innerText = "❌ Aapka browser mobile contact picker support nahi karta. Niche haath se number dalein.";
                status.style.color = "red";
                return;
            }}
            
            try {{
                const props = ['tel', 'name'];
                const opts = {{ multiple: false }};
                const contacts = await navigator.contacts.select(props, opts);
                
                if (contacts.length > 0 && contacts[0].tel && contacts[0].tel.length > 0) {{
                    const rawPhone = contacts[0].tel[0];
                    const cleanPhone = rawPhone.replace(/[^\\d]/g, '');
                    status.innerText = "✅ Selected Number: " + cleanPhone + " (Kripya ise copy karke niche Phone Number box me paste karein)";
                    status.style.color = "green";
                }} else {{
                    status.innerText = "⚠️ Koi number select nahi kiya gaya.";
                }}
            }} catch (err) {{
                status.innerText = "Error: " + err.message;
                status.style.color = "red";
            }}
        }});
    </script>
    """
    components.html(html_code, height=90)

# Display success message if it exists
if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = "" # clear after showing

# ==========================================
# 🏠 SCREEN: MAIN MENU
# ==========================================
if st.session_state.current_screen == "Main Menu":
    st.title("💎 Tesla Laser 4P Management")
    st.subheader("Welcome! Kripya neeche diye gaye options me se select karein:")
    st.write("---")
    
    if st.button("🏢 (1) Office Expense Report", key="menu_off", use_container_width=True):
        st.session_state.current_screen = "Office Expense"
        st.rerun()
        
    if st.button("🏡 (2) Home Expenses Report", key="menu_hm", use_container_width=True):
        st.session_state.current_screen = "Home Expense"
        st.rerun()
        
    if st.button("👷 (3) Operator aur Party Account", key="menu_op_pt", use_container_width=True):
        st.session_state.current_screen = "Operator Party"
        st.rerun()

# ==========================================
# 🏢 SCREEN: OFFICE EXPENSE REPORT
# ==========================================
elif st.session_state.current_screen == "Office Expense":
    if st.button("⬅️ Go Back to Main Menu", type="secondary"):
        st.session_state.current_screen = "Main Menu"
        st.rerun()
        
    st.header("🏢 Office Income & Expense Report")
    col_inc, col_exp = st.columns(2)
    
    with col_inc:
        st.subheader("💰 Office Income (Paisa Aaya)")
        contact_picker_html("off_inc")
        with st.form("off_inc_f", clear_on_submit=True):
            dt = st.date_input("Date:", datetime.now().date(), key="oi_dt")
            nm = st.text_input("Jis Party Se Paisa Aaya Uska Nam:")
            amt = st.number_input("Amount (Rs):", min_value=0.0, step=10.0, value=None, placeholder="Amount dalein...")
            ph = st.text_input("Phone Number:", placeholder="Type or paste number here...")
            rem = st.text_area("Remark / Notes:")
            if st.form_submit_button("Save Income Entry"):
                if not nm or amt is None: st.error("Nam aur Amount bharein!")
                else:
                    df_office = pd.concat([df_office, pd.DataFrame([{"Date": str(dt), "Type": "Income (Aaya)", "Name": nm.strip(), "Amount": amt, "Phone": ph.strip(), "Remark": rem.strip()}])], ignore_index=True)
                    save_data(df_office, OFFICE_FILE)
                    st.session_state.success_msg = "🎉 Success! Entry Saved Successfully!"
                    st.rerun()
                    
    with col_exp:
        st.subheader("💸 Office Expense (Paisa Gaya)")
        contact_picker_html("off_exp")
        with st.form("off_exp_f", clear_on_submit=True):
            dt = st.date_input("Date:", datetime.now().date(), key="oe_dt")
            nm = st.text_input("Jise Paisa De Rahe Hai Uska Nam:")
            amt = st.number_input("Amount (Rs):", min_value=0.0, step=10.0, value=None, placeholder="Amount dalein...")
            ph = st.text_input("Phone Number:", placeholder="Type or paste number here...")
            rem = st.text_area("Remark / Notes:")
            if st.form_submit_button("Save Expense Entry"):
                if not nm or amt is None: st.error("Nam aur Amount bharein!")
                else:
                    df_office = pd.concat([df_office, pd.DataFrame([{"Date": str(dt), "Type": "Expense (Gaya)", "Name": nm.strip(), "Amount": amt, "Phone": ph.strip(), "Remark": rem.strip()}])], ignore_index=True)
                    save_data(df_office, OFFICE_FILE)
                    st.session_state.success_msg = "🎉 Success! Entry
