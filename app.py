import os
import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Files jahan data save hoga
DATA_FILE = "diamond_jobwork_data.csv"
UPAD_FILE = "operator_upad_data.csv"
OPERATORS_FILE = "operators_list.txt"

# Data Load karne ke functions
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        return df
    return pd.DataFrame(
        columns=[
            "Date", "Operator", "Party", "Pieces (Qty)", "Piece Rate",
            "Carat (Qty)", "Carat Rate", "Piece Total", "Carat Total", "Grand Total"
        ]
    )

def load_upad_data():
    if os.path.exists(UPAD_FILE):
        df = pd.read_csv(UPAD_FILE)
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        return df
    return pd.DataFrame(columns=["Date", "Operator", "Amount", "Payment Type"])

def load_operators():
    if os.path.exists(OPERATORS_FILE):
        with open(OPERATORS_FILE, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["Mahesh", "Suresh", "Ramesh"]

# Data Save karne ke functions
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def save_upad_data(df):
    df.to_csv(UPAD_FILE, index=False)

def save_operators(operators):
    with open(OPERATORS_FILE, "w") as f:
        for op in operators:
            f.write(f"{op}\n")

# PDF Generate karne ka function
def generate_pdf(title_text, summary_text, dataframe):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0066CC'), spaceAfter=10)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=11, spaceAfter=6)
    
    story.append(Paragraph(f"<b>{title_text}</b>", title_style))
    story.append(Paragraph(f"Date Generated: {datetime.today().strftime('%d-%b-%Y')}", normal_style))
    story.append(Spacer(1, 10))
    
    for line in summary_text:
        story.append(Paragraph(line, normal_style))
    story.append(Spacer(1, 15))
    
    df_string = dataframe.astype(str)
    table_data = [df_string.columns.values.tolist()] + df_string.values.tolist()
    
    t = Table(table_data, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0066CC')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F5F7FA')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# Initialize Data
df = load_data()
df_upad = load_upad_data()
operators = load_operators()

# Initialize Session State for Locking Rates
if "locked_pc_rate" not in st.session_state:
    st.session_state.locked_pc_rate = 0.0
if "locked_carat_rate" not in st.session_state:
    st.session_state.locked_carat_rate = 0.0

# Streamlit App UI
st.set_page_config(page_title="Tesla Laser 4P", layout="wide")
st.title("💎 Tesla Laser 4P Management")
st.markdown("---")

# Sidebar - Manage Operators
st.sidebar.header("👤 Manage Operators")
new_op = st.sidebar.text_input("Naye Operator Ka Naam:")
if st.sidebar.button("Naya Operator Add Karein"):
    if new_op and new_op not in operators:
        operators.append(new_op)
        save_operators(operators)
        st.sidebar.success(f"'{new_op}' ko add kar diya gaya hai!")
        st.rerun()

# Delete Operator Option in Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🗑️ Delete Operator")
if operators:
    op_to_delete = st.sidebar.selectbox("Delete karne ke liye chunein:", operators, key="del_op_select")
    if st.sidebar.button("Operator Delete Karein", type="secondary"):
        if op_to_delete in operators:
            operators.remove(op_to_delete)
            save_operators(operators)
            st.sidebar.success(f"'{op_to_delete}' ko list se hata diya gaya hai!")
            st.rerun()

# Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📝 Rozana Entry",
        "💰 Operator Accounts (Salary)",
        "📊 Party Accounts (Bill Summary)",
        "💸 Operator Upad Ledger",
        "✏️ Edit / Delete Entries"
    ]
)

# --- TAB 1: ROZANA DATA ENTRY ---
with tab1:
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.header("Daily Work Entry")
        with st.form(key="entry_form", clear_on_submit=False):
            col_main1, col_main2 = st.columns(2)
            with col_main1:
                entry_date = st.date_input("Tareekh (Date):", datetime.today().date(), key="work_date")
                selected_operator = st.selectbox("Operator Chunyein:", operators, key="work_op")
            with col_main2:
                party_name = st.text_input("Party Ka Naam (e.g., RD Patel, RJ Diamond):", value="")

            st.markdown("---")
            col_pc, col_carat = st.columns(2)
            with col_pc:
                st.subheader("📦 Piece (Pc) Work")
                pc_qty = st.number_input("Pieces Quantity:", min_value=0.0, step=1.0, value=0.0)
                pc_rate = st.number_input("Piece Rate (Rs):", min_value=0.0, step=1.0, value=st.session_state.locked_pc_rate)
            with col_carat:
                st.subheader("💎 Carat Work")
                carat_qty = st.number_input("Carat Weight:", min_value=0.0, step=1.0, value=0.0)
                carat_rate = st.number_input("Carat Rate (Rs):", min_value=0.0, step=1.0, value=st.session_state.locked_carat_rate)

            st.markdown("---")
            submit_button = st.form_submit_button("Work Entry Save Karein", type="primary")

            if submit_button:
                if party_name.strip() == "": 
                    st.error("Kripya Party ka naam likhein!")
                elif (pc_qty <= 0 or pc_rate <= 0) and (carat_qty <= 0 or carat_rate <= 0):
                    st.error("Qty aur Rate likhna zaroori hai!")
                else:
                    st.session_state.locked_pc_rate = pc_rate
                    st.session_state.locked_carat_rate = carat_rate
                    p_total = pc_qty * pc_rate
                    c_total = carat_qty * carat_rate
                    g_total = p_total + c_total

                    new_row = {
                        "Date": entry_date, "Operator": selected_operator, "Party": party_name.strip().upper(),
                        "Pieces (Qty)": pc_qty, "Piece Rate": pc_rate, "Carat (Qty)": carat_qty, "Carat Rate": carat_rate,
                        "Piece Total": p_total, "Carat Total": c_total, "Grand Total": g_total,
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df)
                    st.success(f"Work Entry Saved! Total: ₹{g_total:.2f}")
                    st.rerun()

    with col_right:
        st.header("💸 Upad Entry")
        with st.form(key="upad_form", clear_on_submit=True):
            upad_date = st.date_input("Upad Date:", datetime.today().date(), key="upad_date_input")
            upad_operator = st.selectbox("Operator Chunyein:", operators, key="upad_op")
            upad_amount = st.number_input("Upad Amount (₹):", min_value=0.0, step=100.0, value=0.0)
            upad_type = st.radio("Payment Type:", ["Cash", "GPay"], horizontal=True)
            
            submit_upad = st.form_submit_button("Upad Save Karein", type="secondary")
            
            if submit_upad:
                if upad_amount <= 0: 
                    st.error("Kripya sahi Upad Amount bharein!")
                else:
                    new_upad = {"Date": upad_date, "Operator": upad_operator, "Amount": upad_amount, "Payment Type": upad_type}
                    df_upad = pd.concat([df_upad, pd.DataFrame([new_upad])], ignore_index=True)
                    save_upad_data(df_upad)
                    st.success(f"Upad Saved! ₹{upad_amount}")
                    st.rerun()

    st.markdown("---")
    st.markdown("### Aaj Ki Total Entries")
    today_data = df[df["Date"] == datetime.today().date()]
    if not today_data.empty:
        st.dataframe(today_data, use_container_width=True)
    else:
        st.info("Aaj ki koi entry nahi hai.")

# --- TAB 2: OPERATOR ACCOUNTS ---
with tab2:
    st.header("👤 Operator Wise Search & Ledger")
    if not df.empty:
        df["Month"] = pd.to_datetime(df["Date"]).dt.strftime("%B-%Y")
        all_months = sorted(list(df["Month"].unique()))

        col_op1, col_op2 = st.columns(2)
        with col_op1: 
            search_operator = st.selectbox("Search Operator:", sorted(list(df["Operator"].unique())), key="search_op_tab2")
        with col_op2: 
            search_month_op = st.selectbox("Mahina (Month) Chunyein:", all_months, key="search_month_tab2")

        op_filtered = df[(df["Operator"] == search_operator) & (df["Month"] == search_month_op)]

        if not op_filtered.empty:
            total_pcs = op_filtered["Pieces (Qty)"].sum()
            total_carats = op_filtered["Carat (Qty)"].sum()
            total_salary = op_filtered["Grand Total"].sum()

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Pieces Cut", f"{total_pcs:.2f} Pcs")
            m2.metric("Total Carat Cut", f"{total_carats:.2f} Cts")
            m3.metric("Total Salary Earned", f"₹ {total_salary:.2f}")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                pdf_summary = [f"Operator Name: {search_operator}", f"Month: {search_month_op}", f"Total Pieces: {total_pcs:.2f} Pcs", f"Total Carats: {total_carats:.2f} Cts", f"Total Gross Salary: ₹{total_salary:.2f}"]
                pdf_data = op_filtered[["Date", "Party", "Pieces (Qty)", "Piece Total", "Carat (Qty)", "Carat Total", "Grand Total"]]
                pdf_file = generate_pdf("Tesla Laser 4P - Operator Work Invoice", pdf_summary, pdf_data)
                st.download_button(label="📥 Download Salary Bill PDF", data=pdf_file, file_name=f"{search_operator}_{search_month_op}_Salary.pdf", mime="application/pdf")
            
            with col_btn2:
                wa_msg = f"*Tesla Laser 4P - Work Summary*\n\nHello {search_operator},\nAapka *{search_month_op}* ka work ledger details:\n- Total Pieces: {total_pcs:.2f} Pcs\n- Total Carat Weight: {total_carats:.2f} Cts\n- *Total Salary Earned: ₹{total_salary:.2f}*\n\nThank you!"
                encoded_msg = urllib.parse.quote(wa_msg)
                st.markdown(f'<a href="https://wa.me/?text={encoded_msg}" target="_blank"><button style="background-color:#25D366;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-weight:bold;width:100%;">💬 Send Work Summary on WhatsApp</button></a>', unsafe_allow_html=True)

            st.dataframe(op_filtered[["Date", "Party", "Pieces (Qty)", "Piece Rate", "Piece Total", "Carat (Qty)", "Carat Rate", "Carat Total", "Grand Total"]], use_container_width=True)
        else: 
            st.info("Is Mahine ki koi entry nahi hai.")

# --- TAB 3: PARTY ACCOUNTS ---
with tab3:
    st.header("📊 Party Wise Work Summary")
    if not df.empty:
        df["Month"] = pd.to_datetime(df["Date"]).dt.strftime("%B-%Y")
        all_months_party = sorted(list(df["Month"].unique()))

        col_p1, col_p2 = st.columns(2)
        with col_p1: 
            search_party = st.selectbox("Search Party:", sorted(list(df["Party"].unique())))
        with col_p2: 
            search_month_party = st.selectbox("Select Month:", all_months_party, key="party_month_sel")

        party_filtered = df[(df["Party"] == search_party) & (df["Month"] == search_month_party)]

        if not party_filtered.empty:
            p_pcs = party_filtered["Pieces (Qty)"].sum()
            p_carats = party_filtered["Carat (Qty)"].sum()
            p_bill = party_filtered["Grand Total"].sum()

            pm1, pm2, pm3 = st.columns(3)
            pm1.metric("Total Pieces Recieved", f"{p_pcs:.2f} Pcs")
            pm2.metric("Total Carat Recieved", f"{p_carats:.2f} Cts")
            pm3.metric("Total Outstanding Bill", f"₹ {p_bill:.2f}")

            col_pbtn1, col_pbtn2 = st.columns(2)
            with col_pbtn1:
                pdf_summary_p = [f"Party Name: {search_party}", f"Month: {search_month_party}", f"Total Pieces Recieved: {p_pcs:.2f} Pcs", f"Total Carats Recieved: {p_carats:.2f} Cts", f"Total Bill Amount: ₹{p_bill:.2f}"]
                pdf_data_p = party_filtered[["Date", "Operator", "Pieces (Qty)", "Piece Total", "Carat (Qty)", "Carat Total", "Grand Total"]]
                pdf_file_p = generate_pdf("Tesla Laser 4P - Party Bill Statement", pdf_summary_p, pdf_data_p)
                st.download_button(label="📥 Download Party Bill PDF", data=pdf_file_p, file_name=f"Bill_{search_party}_{search_month_party}.pdf", mime="application/pdf")
            
            with col_pbtn2:
                wa_msg_p = f"*Tesla Laser 4P - Jobwork Outstanding Bill*\n\nRespected Sir/Madam ({search_party}),\nAapka *{search_month_party}* ka Jobwork Summary details:\n- Total Pieces: {p_pcs:.2f} Pcs\n- Total Carat Weight: {p_carats:.2f} Cts\n- *Total Outstanding Amount: ₹{p_bill:.2f}*\n\nKripya bill check karke payment clear karein. Thank you!"
                encoded_msg_p = urllib.parse.quote(wa_msg_p)
                st.markdown(f'<a href="https://wa.me/?text={encoded_msg_p}" target="_blank"><button style="background-color:#25D366;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-weight:bold;width:100%;">💬 Send Bill on WhatsApp</button></a>', unsafe_allow_html=True)

            st.dataframe(party_filtered[["Date", "Operator", "Pieces (Qty)", "Piece Rate", "Piece Total", "Carat (Qty)", "Carat Rate", "Carat Total", "Grand Total"]], use_container_width=True)
        else: 
            st.info("Is Mahine me is party ka koi data nahi hai.")

# --- TAB 4: OPERATOR UPAD LEDGER ---
with tab4:
    st.header("💸 Operator Upad & Advance Ledger")
    if not df_upad.empty:
        df_upad["Month"] = pd.to_datetime(df_upad["Date"]).dt.strftime("%B-%Y")
        all_upad_months = sorted(list(df_upad["Month"].unique()))
        
        col_u1, col_u2 = st.columns(2)
        with col_u1: 
            search_upad_op = st.selectbox("Select Operator for Upad:", sorted(list(df_upad["Operator"].unique())))
        with col_u2: 
            search_upad_month = st.selectbox("Select Month for Upad:", all_upad_months)
            
        upad_filtered = df_upad[(df_upad["Operator"] == search_upad_op) & (df_upad["Month"] == search_upad_month)]
        
        total_cash = upad_filtered[upad_filtered["Payment Type"] == "Cash"]["Amount"].sum()
        total_gpay = upad_filtered[upad_filtered["Payment Type"] == "GPay"]["Amount"].sum()
        grand_upad = total_cash + total_gpay
        
        um1, um2, um3 = st.columns(3)
        um1.metric("💵 Total Cash Upad", f"₹ {total_cash:.2f}")
        um2.metric("📱 Total GPay Upad", f"₹ {total_gpay:.2f}")
        um3.metric("💰 Total Upad (Month)", f"₹ {grand_upad:.2f}")
        
        if not upad_filtered.empty:
            col_ubtn1, col_ubtn2 = st.columns(2)
            with col_ubtn1:
                pdf_summary_u = [f"Operator Name: {search_upad_op}", f"Month: {search_upad_month}", f"Total Cash Advance: ₹{total_cash:.2f}", f"Total GPay Advance: ₹{total_gpay:.2f}", f"Total Upad Amount: ₹{grand_upad:.2f}"]
                pdf_data_u = upad_filtered[["Date", "Amount", "Payment Type"]]
                pdf_file_u = generate_pdf("Tesla Laser 4P - Operator Upad Statement", pdf_summary_u, pdf_data_u)
                st.download_button(label="📥 Download Upad PDF", data=pdf_file_u, file_name=f"Upad_{search_upad_op}_{search_upad_month}.pdf", mime="application/pdf")
            
            with col_ubtn2:
                wa_msg_u = f"*Tesla Laser 4P - Upad/Advance Statement*\n\nHello {search_upad_op},\nAapka *{search_upad_month}* ka Upad (Advance) statement:\n- Cash Taken: ₹{total_cash:.2f}\n- GPay Taken: ₹{total_gpay:.2f}\n- *Total Advance Received: ₹{grand_upad:.2f}*\n\nThank you!"
                encoded_msg_u = urllib.parse.quote(wa_msg_u)
                st.markdown(f'<a href="https://wa.me/?text={encoded_msg_u}" target="_blank"><button style="background-color:#25D366;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-weight:bold;width:100%;">💬 Send Upad Statement on WhatsApp</button></a>', unsafe_allow_html=True)

            st.dataframe(upad_filtered[["Date", "Amount", "Payment Type"]], use_container_width=True)
        else: 
            st.info("Is Mahine ki koi upad entry nahi hai.")
    else: 
        st.info("Abhi tak koi upad ya advance entry nahi ki gayi hai.")

# --- TAB 5: EDIT / DELETE ENTRIES ---
with tab5:
    st.header("✏️ Edit ya Delete Karein (Mistake Fixer)")
    
    sub_tab1, sub_tab2 = st.tabs(["📝 Work Entries", "💸 Upad Entries"])
    
    with sub_tab1:
        st.subheader("Work Entries List")
        if not df.empty:
            # Create a selection list with temporary IDs (index)
            df_display = df.copy()
            df_display['Entry_ID'] = df_display.index
            
            st.dataframe(df_display[['Entry_ID', 'Date', 'Operator', 'Party', 'Pieces (Qty)', 'Piece Rate', 'Carat (Qty)', 'Carat Rate', 'Grand Total']], use_container_width=True)
            
            selected_id = st.number_input("Jis Entry ID ko Edit/Delete karna hai wo likhein:", min_value=0, max_value=len(df)-1, step=1, key="work_id_input")
            
            row_data = df.iloc[selected_id]
            st.warning(f"Chuni gayi entry: Date: {row_data['Date']} | Operator: {row_data['Operator']} | Party: {row_data['Party']} | Total: ₹{row_data['Grand Total']}")
            
            col_ed1, col_ed2 = st.columns(2)
            with col_ed1:
                st.markdown("### 📝 Edit Karein")
                with st.form(key="edit_work_form"):
                    e_date = st.date_input("New Date:", row_data['Date'])
                    e_op = st.selectbox("New Operator:", operators, index=operators.index(row_data['Operator']) if row_data['Operator'] in operators else 0)
                    e_party = st.text_input("New Party:", row_data['Party'])
                    e_p_qty = st.number_input("New Piece Qty:", value=float(row_data['Pieces (Qty)']))
                    e_p_rate = st.number_input("New Piece Rate:", value=float(row_data['Piece Rate']))
                    e_c_qty = st.number_input("New Carat Qty:", value=float(row_data['Carat (Qty)']))
                    e_c_rate = st.number_input("New Carat Rate:", value=float(row_data['Carat Rate']))
                    
                    save_edit = st.form_submit_button("Badlav Save Karein", type="primary")
                    if save_edit:
                        p_t = e_p_qty * e_p_rate
                        c_t = e_c_qty * e_c_rate
                        df.at[selected_id, 'Date'] = e_date
                        df.at[selected_id, 'Operator'] = e_op
                        df.at[selected_id, 'Party'] = e_party.strip().upper()
                        df.at[selected_id, 'Pieces (Qty)'] = e_p_qty
                        df.at[selected_id, 'Piece Rate'] = e_p_rate
                        df.at[selected_id, 'Piece Total'] = p_t
                        df.at[selected_id, 'Carat (Qty)'] = e_c_qty
                        df.at[selected_id, 'Carat Rate'] = e_c_rate
                        df.at[selected_id, 'Carat Total'] = c_t
                        df.at[selected_id, 'Grand Total'] = p_t + c_t
                        save_data(df)
                        st.success("Entry perfectly update ho gayi!")
                        st.rerun()
                        
            with col_ed2:
                st.markdown("### 🗑️ Delete Karein")
                st.error("Kya aap is entry ko poori tarah delete karna chahte hain?")
                if st.button("HAAN, ENTRY DELETE KAREIN", type="secondary", key="del_work_btn"):
                    df = df.drop(selected_id).reset_index(drop=True)
                    save_data(df)
                    st.success("Entry successfully delete kar di gayi hai!")
                    st.rerun()
        else:
            st.info("Work entry me koi data nahi hai.")
            
    with sub_tab2:
        st.subheader("Upad Entries List")
        if not df_upad.empty:
            df_upad_display = df_upad.copy()
            df_upad_display['Upad_ID'] = df_upad_display.index
            
            st.dataframe(df_upad_display[['Upad_ID', 'Date', 'Operator', 'Amount', 'Payment Type']], use_container_width=True)
            
            selected_upad_id = st.number_input("Jis Upad ID ko Edit/Delete karna hai wo likhein:", min_value=0, max_value=len(df_upad)-1, step=1, key="upad_id_input")
            u_row_data = df_upad.iloc[selected_upad_id]
            st.warning(f"Chuni gayi Upad entry: Date: {u_row_data['Date']} | Operator: {u_row_data['Operator']} | Amount: ₹{u_row_data['Amount']}")
            
            col_u_ed1, col_u_ed2 = st.columns(2)
            with col_u_ed1:
                st.markdown("### 📝 Edit Upad")
                with st.form(key="edit_upad_form"):
                    eu_date = st.date_input("New Upad Date:", u_row_data['Date'])
                    eu_op = st.selectbox("New Operator:", operators, index=operators.index(u_row_data['Operator']) if u_row_data['Operator'] in operators else 0)
                    eu_amt = st.number_input("New Amount (₹):", value=float(u_row_data['Amount']))
                    eu_type = st.radio("New Payment Type:", ["Cash", "GPay"], index=0 if u_row_data['Payment Type'] == "Cash" else 1)
                    
                    save_u_edit = st.form_submit_button("Upad Change Save Karein", type="primary")
                    if save_u_edit:
                        df_upad.at[selected_upad_id, 'Date'] = eu_date
                        df_upad.at[selected_upad_id, 'Operator'] = eu_op
                        df_upad.at[selected_upad_id, 'Amount'] = eu_amt
                        df_upad.at[selected_upad_id, 'Payment Type'] = eu_type
                        save_upad_data(df_upad)
                        st.success("Upad Entry successfully update ho gayi!")
                        st.rerun()
                        
            with col_u_ed2:
                st.markdown("### 🗑️ Delete Upad")
                st.error("Kya aap is Upad entry ko poori tarah mita dena chahte hain?")
                if st.button("HAAN, UPAD DELETE KAREIN", type="secondary", key="del_upad_btn"):
                    df_upad = df_upad.drop(selected_upad_id).reset_index(drop=True)
                    save_upad_data(df_upad)
                    st.success("Upad Entry completely clear kar di gayi hai!")
                    st.rerun()
        else:
            st.info("Upad entry me koi data nahi hai.")