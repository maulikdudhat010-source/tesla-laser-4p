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

# ADVANCED CSS: Hide Streamlit watermarks and header/footer
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

# ---- STATE MANAGEMENT ----
if 'current_screen' not in st.session_state:
    st.session_state.current_screen = "Main Menu"

if 'success_msg' not in st.session_state:
    st.session_state.success_msg = ""

# Display sticky success message if it exists
if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = "" # clear

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
                    st.session_state.success_msg = "🎉 Success! Entry Saved Successfully!"
                    st.rerun()

    st.markdown("---")
    st.subheader("📅 Office Monthly Report")
    if not df_office.empty:
        df_office = df_office.sort_values(by="Date", ascending=False).reset_index(drop=True)
        display_df = df_office.copy()
        display_df.index = display_df.index + 1
        st.dataframe(display_df[["Date", "Type", "Name", "Amount", "Phone", "Remark"]])
        
        pdf_data = generate_pdf(display_df[["Date", "Type", "Name", "Amount", "Phone", "Remark"]], "Office Income & Expense Report")
        st.download_button("📥 Download Report PDF", data=pdf_data, file_name="Office_Expense_Report.pdf", mime="application/pdf")
        
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            row_ed = st.number_input("Edit Serial Number:", min_value=1, max_value=len(df_office), step=1, key="off_ed_s")
            idx = row_ed - 1
            curr = df_office.iloc[idx]
            n_name = st.text_input("Naya Nam:", value=str(curr["Name"]), key="off_en")
            n_amt = st.number_input("Naya Amount:", value=float(curr["Amount"]), key="off_ea")
            n_ph = st.text_input("Naya Phone:", value=str(curr["Phone"]), key="off_eph")
            n_rem = st.text_area("Naya Remark:", value=str(curr["Remark"]), key="off_er")
            if st.button("Update Entry"):
                df_office.at[idx, "Name"] = n_name.strip()
                df_office.at[idx, "Amount"] = n_amt
                df_office.at[idx, "Phone"] = n_ph.strip()
                df_office.at[idx, "Remark"] = n_rem.strip()
                save_data(df_office, OFFICE_FILE)
                st.session_state.success_msg = "🎉 Success! Entry Updated Successfully!"
                st.rerun()
        with col_e2:
            row_del = st.number_input("Delete Serial Number:", min_value=1, max_value=len(df_office), step=1, key="off_del_s")
            if st.button("Confirm Delete Office Entry", type="primary"):
                df_office = df_office.drop(row_del - 1).reset_index(drop=True)
                save_data(df_office, OFFICE_FILE)
                st.session_state.success_msg = "🎉 Success! Entry Deleted Successfully!"
                st.rerun()
        with col_e3:
            row_wa = st.number_input("WhatsApp Serial Number:", min_value=1, max_value=len(df_office), step=1, key="off_wa_s")
            curr_wa = df_office.iloc[row_wa - 1]
            msg = f"Office Report:\nDate: {curr_wa['Date']}\nType: {curr_wa['Type']}\nName: {curr_wa['Name']}\nAmount: {curr_wa['Amount']}\nNotes: {curr_wa['Remark']}"
            url = get_whatsapp_link(curr_wa["Phone"], msg)
            if curr_wa["Phone"]:
                st.markdown(f'<a href="{url}" target="_blank"><button style="background-color:#25D366;color:white;border:none;padding:10px 20px;border-radius:5px;">Send WhatsApp 💬</button></a>', unsafe_allow_html=True)
            else: st.info("No phone number.")
    else: st.info("No entries.")

# ==========================================
# 🏡 SCREEN: HOME EXPENSES REPORT
# ==========================================
elif st.session_state.current_screen == "Home Expense":
    if st.button("⬅️ Go Back to Main Menu", type="secondary"):
        st.session_state.current_screen = "Main Menu"
        st.rerun()
        
    st.header("🏡 Home Income & Expense Report")
    col_inc, col_exp = st.columns(2)
    
    with col_inc:
        st.subheader("💰 Home Income (Paisa Aaya)")
        contact_picker_html("hm_inc")
        with st.form("hm_inc_f", clear_on_submit=True):
            dt = st.date_input("Date:", datetime.now().date(), key="hmi_dt")
            nm = st.text_input("Kahan Se Paisa Aaya:")
            amt = st.number_input("Amount (Rs):", min_value=0.0, step=10.0, value=None, placeholder="Amount dalein...")
            ph = st.text_input("Phone Number:", placeholder="Type or paste number here...")
            rem = st.text_area("Remark / Notes:")
            if st.form_submit_button("Save Income Entry"):
                if not nm or amt is None: st.error("Nam aur Amount bharein!")
                else:
                    df_home = pd.concat([df_home, pd.DataFrame([{"Date": str(dt), "Type": "Income (Aaya)", "Name": nm.strip(), "Amount": amt, "Phone": ph.strip(), "Remark": rem.strip()}])], ignore_index=True)
                    save_data(df_home, HOME_FILE)
                    st.session_state.success_msg = "🎉 Success! Entry Saved Successfully!"
                    st.rerun()
                    
    with col_exp:
        st.subheader("💸 Home Expense (Paisa Gaya)")
        contact_picker_html("hm_exp")
        with st.form("hm_exp_f", clear_on_submit=True):
            dt = st.date_input("Date:", datetime.now().date(), key="hme_dt")
            nm = st.text_input("Jise Paisa De Rahe Hai Uska Nam:")
            amt = st.number_input("Amount (Rs):", min_value=0.0, step=10.0, value=None, placeholder="Amount dalein...")
            ph = st.text_input("Phone Number:", placeholder="Type or paste number here...")
            rem = st.text_area("Remark / Notes:")
            if st.form_submit_button("Save Expense Entry"):
                if not nm or amt is None: st.error("Nam aur Amount bharein!")
                else:
                    df_home = pd.concat([df_home, pd.DataFrame([{"Date": str(dt), "Type": "Expense (Gaya)", "Name": nm.strip(), "Amount": amt, "Phone": ph.strip(), "Remark": rem.strip()}])], ignore_index=True)
                    save_data(df_home, HOME_FILE)
                    st.session_state.success_msg = "🎉 Success! Entry Saved Successfully!"
                    st.rerun()

    st.markdown("---")
    st.subheader("📅 Home Monthly Report")
    if not df_home.empty:
        df_home = df_home.sort_values(by="Date", ascending=False).reset_index(drop=True)
        display_df = df_home.copy()
        display_df.index = display_df.index + 1
        st.dataframe(display_df[["Date", "Type", "Name", "Amount", "Phone", "Remark"]])
        
        pdf_data = generate_pdf(display_df[["Date", "Type", "Name", "Amount", "Phone", "Remark"]], "Home Income & Expense Report")
        st.download_button("📥 Download Report PDF", data=pdf_data, file_name="Home_Expense_Report.pdf", mime="application/pdf")
        
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            row_ed = st.number_input("Edit Serial Number:", min_value=1, max_value=len(df_home), step=1, key="hm_ed_s")
            idx = row_ed - 1
            curr = df_home.iloc[idx]
            n_name = st.text_input("Naya Nam:", value=str(curr["Name"]), key="hm_en")
            n_amt = st.number_input("Naya Amount:", value=float(curr["Amount"]), key="hm_ea")
            n_ph = st.text_input("Naya Phone:", value=str(curr["Phone"]), key="hm_eph")
            n_rem = st.text_area("Naya Remark:", value=str(curr["Remark"]), key="hm_er")
            if st.button("Update Entry"):
                df_home.at[idx, "Name"] = n_name.strip()
                df_home.at[idx, "Amount"] = n_amt
                df_home.at[idx, "Phone"] = n_ph.strip()
                df_home.at[idx, "Remark"] = n_rem.strip()
                save_data(df_home, HOME_FILE)
                st.session_state.success_msg = "🎉 Success! Entry Updated Successfully!"
                st.rerun()
        with col_e2:
            row_del = st.number_input("Delete Serial Number:", min_value=1, max_value=len(df_home), step=1, key="hm_del_s")
            if st.button("Confirm Delete Home Entry", type="primary"):
                df_home = df_home.drop(row_del - 1).reset_index(drop=True)
                save_data(df_home, HOME_FILE)
                st.session_state.success_msg = "🎉 Success! Entry Deleted Successfully!"
                st.rerun()
        with col_e3:
            row_wa = st.number_input("WhatsApp Serial Number:", min_value=1, max_value=len(df_home), step=1, key="hm_wa_s")
            curr_wa = df_home.iloc[row_wa - 1]
            msg = f"Home Report:\nDate: {curr_wa['Date']}\nType: {curr_wa['Type']}\nName: {curr_wa['Name']}\nAmount: {curr_wa['Amount']}\nNotes: {curr_wa['Remark']}"
            url = get_whatsapp_link(curr_wa["Phone"], msg)
            if curr_wa["Phone"]:
                st.markdown(f'<a href="{url}" target="_blank"><button style="background-color:#25D366;color:white;border:none;padding:10px 20px;border-radius:5px;">Send WhatsApp 💬</button></a>', unsafe_allow_html=True)
            else: st.info("No phone number.")
    else: st.info("No entries.")

# ==========================================
# 👷 SCREEN: OPERATOR AND PARTY ACCOUNT
# ==========================================
elif st.session_state.current_screen == "Operator Party":
    if st.button("⬅️ Go Back to Main Menu", type="secondary"):
        st.session_state.current_screen = "Main Menu"
        st.rerun()
        
    st.header("👷 Operator & Party Account Module")
    
    if 'sel_op' not in st.session_state: st.session_state.sel_op = ""
    if 'sel_pt' not in st.session_state: st.session_state.sel_pt = ""
    if 'sel_wt' not in st.session_state: st.session_state.sel_wt = "PC"
    if 'sel_u_op' not in st.session_state: st.session_state.sel_u_op = ""
    if 'sel_pm' not in st.session_state: st.session_state.sel_pm = "Cash"
    
    op_list = df_master[df_master["Type"] == "Operator"]["Name"].tolist()
    pt_list = df_master[df_master["Type"] == "Party"]["Name"].tolist()

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.subheader("Manage Operators (Add / Remove)")
        with st.form("op_m", clear_on_submit=True):
            name_in = st.text_input("Operator Name:")
            act = st.selectbox("Action:", ["Add", "Remove"])
            if st.form_submit_button("Submit"):
                if act == "Add" and name_in.strip():
                    if not ((df_master['Type'] == 'Operator') & (df_master['Name'] == name_in.strip())).any():
                        df_master = pd.concat([df_master, pd.DataFrame([{"Type": "Operator", "Name": name_in.strip()}])], ignore_index=True)
                        save_data(df_master, OP_PARTY_MASTER_FILE)
                        st.session_state.success_msg = "🎉 Success! Operator Added Successfully!"
                        st.rerun()
                elif act == "Remove" and name_in.strip():
                    df_master = df_master[~((df_master['Type'] == 'Operator') & (df_master['Name'] == name_in.strip()))]
                    save_data(df_master, OP_PARTY_MASTER_FILE)
                    st.session_state.success_msg = "🎉 Success! Operator Removed Successfully!"
                    st.rerun()
                    
    with col_m2:
        st.subheader("Manage Parties (Add / Remove)")
        with st.form("pt_m", clear_on_submit=True):
            name_in = st.text_input("Party Name:")
            act = st.selectbox("Action:", ["Add", "Remove"])
            if st.form_submit_button("Submit"):
                if act == "Add" and name_in.strip():
                    if not ((df_master['Type'] == 'Party') & (df_master['Name'] == name_in.strip())).any():
                        df_master = pd.concat([df_master, pd.DataFrame([{"Type": "Party", "Name": name_in.strip()}])], ignore_index=True)
                        save_data(df_master, OP_PARTY_MASTER_FILE)
                        st.session_state.success_msg = "🎉 Success! Party Added Successfully!"
                        st.rerun()
                elif act == "Remove" and name_in.strip():
                    df_master = df_master[~((df_master['Type'] == 'Party') & (df_master['Name'] == name_in.strip()))]
                    save_data(df_master, OP_PARTY_MASTER_FILE)
                    st.session_state.success_msg = "🎉 Success! Party Removed Successfully!"
                    st.rerun()

    st.markdown("---")
    
    col_ent1, col_ent2 = st.columns(2)
    
    with col_ent1:
        st.subheader("📝 Daily Work Entry Panel")
        st.markdown("**Select Operator Button:**")
        if op_list:
            c_op = st.columns(min(len(op_list), 4))
            for i, o_nm in enumerate(op_list):
                with c_op[i % 4]:
                    if st.button(o_nm, key=f"o_{o_nm}"): st.session_state.sel_op = o_nm
        else: st.info("No saved operators.")
                    
        st.markdown("**Select Party Button:**")
        if pt_list:
            c_pt = st.columns(min(len(pt_list), 4))
            for i, p_nm in enumerate(pt_list):
                with c_pt[i % 4]:
                    if st.button(p_nm, key=f"p_{p_nm}"): st.session_state.sel_pt = p_nm
        else: st.info("No saved parties.")

        st.markdown("**Select Work Type Button:**")
        c_wt = st.columns(3)
        with c_wt[0]:
            if st.button("🔴 PC", key="wt_pc"): st.session_state.sel_wt = "PC"
        with c_wt[1]:
            if st.button("🟢 Carat", key="wt_carat"): st.session_state.sel_wt = "Carat"
        with c_wt[2]:
            if st.button("🔵 Choki", key="wt_choki"): st.session_state.sel_wt = "Choki"

        st.info(f"👉 Selected -> Op: `{st.session_state.sel_op}` | Pt: `{st.session_state.sel_pt}` | Wrk: `{st.session_state.sel_wt}`")
        
        with st.form("save_work_form", clear_on_submit=True):
            w_dt = st.date_input("Date:", key="w_dt_in")
            qty = 0
            if st.session_state.sel_wt == "PC":
                qty = st.number_input("Number of PC:", min_value=0, value=0, step=1)
            elif st.session_state.sel_wt == "Carat":
                qty = st.number_input("Number of Carats:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            else:
                qty = st.number_input("Number of Choki:", min_value=0, value=0, step=1)
                
            op_r = st.number_input("Operator Rate (Rs):", min_value=0.0, step=0.1, value=None, placeholder="Type Operator Rate...")
            pt_r = st.number_input("Party Rate (Rs):", min_value=0.0, step=0.1, value=None, placeholder="Type Party Rate...")
            
            if st.form_submit_button("Save Work Entry"):
                if not st.session_state.sel_op or not st.session_state.sel_pt:
                    st.error("Kripya Operator aur Party select karein!")
                elif op_r is None or pt_r is None:
                    st.error("Kripya dono ke rate dalein!")
                else:
                    op_amt = qty * op_r
                    pt_amt = qty * pt_r
                    new_row = {
                        "Date": str(w_dt), "Operator": st.session_state.sel_op, "Party": st.session_state.sel_pt,
                        "Work Type": st.session_state.sel_wt,
                        "Pcs": qty if st.session_state.sel_wt == "PC" else 0,
                        "Carats": qty if st.session_state.sel_wt == "Carat" else 0.0,
                        "Choki": qty if st.session_state.sel_wt == "Choki" else 0,
                        "Operator Rate": op_r, "Party Rate": pt_r,
                        "Operator Amount": op_amt, "Party Amount": pt_amt
                    }
                    df_work = pd.concat([df_work, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df_work, DAILY_WORK_FILE)
                    st.session_state.success_msg = "🎉 Success! Work Entry Saved Successfully!"
                    st.rerun()

    with col_ent2:
        st.subheader("💸 Operator Upad (Advance) Entry Panel")
        st.markdown("**Select Operator for Upad:**")
        if op_list:
            c_u_op = st.columns(min(len(op_list), 4))
            for i, o_nm in enumerate(op_list):
                with c_u_op[i % 4]:
                    if st.button(o_nm, key=f"u_o_{o_nm}"): st.session_state.sel_u_op = o_nm
        else: st.info("No saved operators.")
        
        st.markdown("**Select Payment Mode Button:**")
        c_pm = st.columns(2)
        with c_pm[0]:
            if st.button("💵 Cash", key="pm_cash"): st.session_state.sel_pm = "Cash"
        with c_pm[1]:
            if st.button("📱 GPay", key="pm_gpay"): st.session_state.sel_pm = "GPay"
            
        st.info(f"👉 Selected for Upad -> Op: `{st.session_state.sel_u_op}` | Mode: `{st.session_state.sel_pm}`")
        
        with st.form("save_upad_form", clear_on_submit=True):
            u_dt = st.date_input("Date:", key="u_dt_in")
            u_amt = st.number_input("Upad Amount (Rs):", min_value=0.0, step=50.0, value=None, placeholder="Upad ka amount dalein...")
            u_rem = st.text_area("Remark / Notes (Optional):", placeholder="Upad details...")
            
            if st.form_submit_button("Save Upad Entry"):
                if not st.session_state.sel_u_op:
                    st.error("Kripya Operator select karein!")
                elif u_amt is None or u_amt <= 0:
                    st.error("Kripya valid Upad amount dalein!")
                else:
                    new_upad = {
                        "Date": str(u_dt), "Operator": st.session_state.sel_u_op,
                        "Amount": u_amt, "Payment Mode": st.session_state.sel_pm, "Remark": u_rem.strip()
                    }
                    df_upad = pd.concat([df_upad, pd.DataFrame([new_upad])], ignore_index=True)
                    save_data(df_upad, OP_UPAD_FILE)
                    st.session_state.success_msg = "🎉 Success! Upad Entry Saved Successfully!"
                    st.rerun()

    st.markdown("---")
    st.subheader("📅 Operator & Party Reports")
    sub_rep = st.radio("Select View:", ["Operator Salary & Upad Table", "Party Outstanding Table", "Full Work Panel", "Full Upad Panel"])
    
    if sub_rep == "Operator Salary & Upad Table" and (not df_work.empty or not df_upad.empty):
        unique_ops = sorted(list(set(df_work["Operator"].unique()).union(set(df_upad["Operator"].unique()))))
        sel_o = st.selectbox("Select Operator for Monthly Report:", unique_ops)
        
        st.markdown("#### 🛠️ Work Details (Kaam ka Hisab)")
        df_f_work = df_work[df_work["Operator"] == sel_o].copy().reset_index(drop=True)
        if not df_f_work.empty:
            df_f_work.index = df_f_work.index + 1
            st.dataframe(df_f_work[["Date", "Party", "Work Type", "Pcs", "Carats", "Choki", "Operator Rate", "Operator Amount"]])
        else: st.info("Is mahine ka koi kaam nahi mila.")
            
        st.markdown("#### 💸 Upad Details (Advance ka Hisab)")
        df_f_upad = df_upad[df_upad["Operator"] == sel_o].copy().reset_index(drop=True)
        if not df_f_upad.empty:
            df_f_upad.index = df_f_upad.index + 1
            st.dataframe(df_f_upad[["Date", "Amount", "Payment Mode", "Remark"]])
        else: st.info("Koi upad / advance nahi liya gaya.")
            
        total_salary = df_f_work["Operator Amount"].sum() if not df_f_work.empty else 0.0
        total_upad = df_f_upad["Amount"].sum() if not df_f_upad.empty else 0.0
        net_payable = total_salary - total_upad
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Total Work Salary", f"₹{total_salary:.2f}")
        c_m2.metric("Total Upad (Advance)", f"₹{total_upad:.2f}", delta=f"-₹{total_upad:.2f}", delta_color="inverse")
        c_m3.metric("Net Baaki (Payable Amount)", f"₹{net_payable:.2f}")
        
    elif sub_rep == "Party Outstanding Table" and not df_work.empty:
        sel_p = st.selectbox("Select Party:", sorted(df_work["Party"].unique()))
        df_f = df_work[df_work["Party"] == sel_p].copy().reset_index(drop=True)
        df_f.index = df_f.index + 1
        st.dataframe(df_f[["Date", "Operator", "Work Type", "Pcs", "Carats", "Choki", "Party Rate", "Party Amount"]])
        st.metric("Total Outstanding Amount", f"₹{df_f['Party Amount'].sum():.2f}")
        
    elif sub_rep == "Full Work Panel" and not df_work.empty:
        df_work = df_work.sort_values(by="Date", ascending=False).reset_index(drop=True)
        display_df = df_work.copy()
        display_df.index = display_df.index + 1
        st.dataframe(display_df)
        
        c_ed1, c_ed2 = st.columns(2)
        with c_ed1:
            row_e = st.number_input("Edit Serial Number:", min_value=1, max_value=len(df_work), step=1, key="w_ed")
            idx_w = row_e - 1
            curr_w = df_work.iloc[idx_w]
            n_op_r = st.number_input("Naya Operator Rate:", value=float(curr_w["Operator Rate"]))
            n_pt_r = st.number_input("Naya Party Rate:", value=float(curr_w["Party Rate"]))
            if st.button("Update Work Values"):
                w_t = curr_w["Work Type"]
                mult = curr_w["Pcs"] if w_t == "PC" else (curr_w["Carats"] if w_t == "Carat" else curr_w["Choki"])
                df_work.at[idx_w, "Operator Rate"] = n_op_r
                df_work.at[idx_w, "Party Rate"] = n_pt_r
                df_work.at[idx_w, "Operator Amount"] = mult * n_op_r
                df_work.at[idx_w, "Party Amount"] = mult * n_pt_r
                save_data(df_work, DAILY_WORK_FILE)
                st.session_state.success_msg = "🎉 Success! Work Entry Updated Successfully!"
                st.rerun()
        with c_ed2:
            row_d = st.number_input("Delete Serial Number:", min_value=1, max_value=len(df_work), step=1, key="w_del")
            if st.button("Confirm Delete Work Row", type="primary"):
                df_work = df_work.drop(row_d - 1).reset_index(drop=True)
                save_data(df_work, DAILY_WORK_FILE)
                st.session_state.success_msg = "🎉 Success! Work Entry Deleted Successfully!"
                st.rerun()
        
    elif sub_rep == "Full Upad Panel" and not df_upad.empty:
        df_upad = df_upad.sort_values(by="Date", ascending=False).reset_index(drop=True)
        display_df = df_upad.copy()
        display_df.index = display_df.index + 1
        st.dataframe(display_df)
        
        c_u_ed1, c_u_ed2 = st.columns(2)
        with c_u_ed1:
            row_u_e = st.number_input("Edit Upad Serial Number:", min_value=1, max_value=len(df_upad), step=1, key="u_ed")
            idx_u = row_u_e - 1
            curr_u = df_upad.iloc[idx_u]
            n_u_amt = st.number_input("Naya Upad Amount:", value=float(curr_u["Amount"]))
            n_u_rem = st.text_area("Naya Upad Remark:", value=str(curr_u["Remark"]))
            if st.button("Update Upad Values"):
                df_upad.at[idx_u, "Amount"] = n_u_amt
                df_upad.at[idx_u, "Remark"] = n_u_rem.strip()
                save_data(df_upad, OP_UPAD_FILE)
                st.session_state.success_msg = "🎉 Success! Upad Entry Updated Successfully!"
                st.rerun()
        with c_u_ed2:
            row_u_d = st.number_input("Delete Upad Serial Number:", min_value=1, max_value=len(df_upad), step=1, key="u_del")
            if st.button("Confirm Delete Upad Row", type="primary"):
                df_upad = df_upad.drop(row_u_d - 1).reset_index(drop=True)
                save_data(df_upad, OP_UPAD_FILE)
                st.session_state.success_msg = "🎉 Success! Upad Entry Deleted Successfully!"
                st.rerun()
