import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Page Config and CSS to hide Streamlit branding
st.set_page_config(page_title="Tesla Laser 4P", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none;}
    </style>
    """, unsafe_allow_html=True)

st.title("💎 Tesla Laser 4P Management")

# --- DATA STORAGE SETUP ---
# local files to store data
ENTRIES_FILE = "daily_entries.csv"
OPERATORS_FILE = "operators.csv"
PARTIES_FILE = "parties.csv"

# Load or Initialize Data
def load_data(file_path, columns):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# Initialize DataFrames
entries_cols = ["Date", "Operator", "Party", "Work Type", "Pcs", "Carats", "Choki", "Operator Rate", "Party Rate", "Operator Amount", "Party Amount"]
df_entries = load_data(ENTRIES_FILE, entries_cols)

# Ensure columns are present
for col in entries_cols:
    if col not in df_entries.columns:
        df_entries[col] = 0.0 if "Amount" in col or "Rate" in col else ""

# Tabs setup
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Rozana Entry", 
    "👷 Operator Accounts (Salary)", 
    "🏢 Party Accounts (Outstanding)", 
    "📅 Monthly Report & Edit/Delete"
])

# --- TAB 1: ROZANA ENTRY ---
with tab1:
    st.header("Daily Work Entry")
    
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            entry_date = st.date_input("Tarikh (Date):", datetime.now().date())
            operator_name = st.text_input("Operator Ka Naam:")
            party_name = st.text_input("Party Ka Naam:")
            
        with col2:
            work_type = st.selectbox("Kaam Ka Type (Work Type):", ["PC Work", "Carat Work", "Choki Work"])
            
            # Sub-fields based on Work Type
            pcs = 0
            carats = 0.0
            choki = 0
            
            if work_type == "PC Work":
                pcs = st.number_input("Total Pieces (Pcs):", min_value=0, step=1, value=0)
            elif work_type == "Carat Work":
                carats = st.number_input("Total Carats:", min_value=0.0, step=0.01, format="%.2f", value=0.0)
            elif work_type == "Choki Work":
                choki = st.number_input("Total Choki:", min_value=0, step=1, value=0)

        st.markdown("---")
        st.subheader("Rates (Bhav) Setting")
        col3, col4 = st.columns(2)
        
        with col3:
            # Value = None keeps it blank (no 0.00 by default)
            op_rate = st.number_input("Operator Rate (Per Pc/Carat/Choki):", min_value=0.0, step=0.1, value=None, placeholder="Type Operator Rate...")
        with col4:
            party_rate = st.number_input("Party Rate (Per Pc/Carat/Choki):", min_value=0.0, step=0.1, value=None, placeholder="Type Party Rate...")
            
        submit_btn = st.form_submit_button("Save Entry")
        
        if submit_btn:
            if not operator_name or not party_name:
                st.error("Kripya Operator aur Party dono ka naam likhein!")
            elif op_rate is None or party_rate is None:
                st.error("Kripya Operator aur Party dono ka Rate (Bhav) dalein!")
            else:
                # Calculations
                multiplier = pcs if work_type == "PC Work" else (carats if work_type == "Carat Work" else choki)
                op_amount = multiplier * op_rate
                party_amount = multiplier * party_rate
                
                # Create New Row
                new_row = {
                    "Date": str(entry_date),
                    "Operator": operator_name.strip(),
                    "Party": party_name.strip(),
                    "Work Type": work_type,
                    "Pcs": pcs,
                    "Carats": carats,
                    "Choki": choki,
                    "Operator Rate": op_rate,
                    "Party Rate": party_rate,
                    "Operator Amount": op_amount,
                    "Party Amount": party_amount
                }
                
                df_entries = pd.concat([df_entries, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df_entries, ENTRIES_FILE)
                
                # Success Message to avoid double submission
                st.success(f"🎉 Success! Entry Saved successfully! (Operator Amount: ₹{op_amount:.2f} | Party Amount: ₹{party_amount:.2f})")
                st.balloons()

# --- TAB 2: OPERATOR ACCOUNTS ---
with tab2:
    st.header("Operator Salary & Khata")
    if not df_entries.empty:
        operators = df_entries["Operator"].unique()
        selected_op = st.selectbox("Select Operator:", operators)
        
        op_data = df_entries[df_entries["Operator"] == selected_op]
        st.dataframe(op_data[["Date", "Party", "Work Type", "Pcs", "Carats", "Choki", "Operator Rate", "Operator Amount"]])
        
        total_salary = op_data["Operator Amount"].sum()
        st.metric(label=f"Total Salary Payable to {selected_op}", value=f"₹{total_salary:.2f}")
    else:
        st.info("Abhi tak koi entry nahi hui hai.")

# --- TAB 3: PARTY ACCOUNTS ---
with tab3:
    st.header("Party Bill & Outstanding")
    if not df_entries.empty:
        parties = df_entries["Party"].unique()
        selected_party = st.selectbox("Select Party:", parties)
        
        party_data = df_entries[df_entries["Party"] == selected_party]
        st.dataframe(party_data[["Date", "Operator", "Work Type", "Pcs", "Carats", "Choki", "Party Rate", "Party Amount"]])
        
        total_outstanding = party_data["Party Amount"].sum()
        st.metric(label=f"Total Outstanding from {selected_party}", value=f"₹{total_outstanding:.2f}")
    else:
        st.info("Abhi tak koi entry nahi hui hai.")

# --- TAB 4: MONTHLY REPORT & EDIT / DELETE ---
with tab4:
    st.header("All Entries (Edit & Delete Panel)")
    
    if not df_entries.empty:
        # Sort by date
        df_entries = df_entries.sort_values(by="Date", ascending=False).reset_index(drop=True)
        
        # Display table with index
        st.write("Niche di gayi list me se jis entry ko badalna ya mitaana hai, uska serial number select karein:")
        
        # Show clean display dataframe
        display_df = df_entries.copy()
        display_df.index = display_df.index + 1 # 1-based indexing for users
        st.dataframe(display_df)
        
        st.markdown("---")
        col_ed1, col_ed2 = st.columns(2)
        
        with col_ed1:
            st.subheader("✏️ Edit Entry")
            row_to_edit = st.number_input("Edit karne ke liye Serial Number dalein:", min_value=1, max_value=len(df_entries), step=1)
            actual_index = row_to_edit - 1
            
            # Show current values of selected row
            current_row = df_entries.iloc[actual_index]
            st.write(f"Selected: {current_row['Operator']} - {current_row['Party']} ({current_row['Date']})")
            
            new_op_rate = st.number_input("Naya Operator Rate:", value=float(current_row["Operator Rate"]), key="edit_op_rate")
            new_pt_rate = st.number_input("Naya Party Rate:", value=float(current_row["Party Rate"]), key="edit_pt_rate")
            
            if st.button("Update Entry"):
                # Recalculate amounts
                work_type = current_row["Work Type"]
                multiplier = current_row["Pcs"] if work_type == "PC Work" else (current_row["Carats"] if work_type == "Carat Work" else current_row["Choki"])
                
                df_entries.at[actual_index, "Operator Rate"] = new_op_rate
                df_entries.at[actual_index, "Party Rate"] = new_pt_rate
                df_entries.at[actual_index, "Operator Amount"] = multiplier * new_op_rate
                df_entries.at[actual_index, "Party Amount"] = multiplier * new_pt_rate
                
                save_data(df_entries, ENTRIES_FILE)
                st.success(f"Entry #{row_to_edit} updated successfully!")
                st.rerun()
                
        with col_ed2:
            st.subheader("🗑️ Delete Entry")
            row_to_delete = st.number_input("Delete karne ke liye Serial Number dalein:", min_value=1, max_value=len(df_entries), step=1, key="del_idx")
            
            if st.button("🔴 Confirm Delete", type="primary"):
                df_entries = df_entries.drop(actual_index).reset_index(drop=True)
                save_data(df_entries, ENTRIES_FILE)
                st.success(f"Entry #{row_to_delete} deleted successfully!")
                st.rerun()
    else:
        st.info("Abhi tak koi entry nahi hui hai.")
