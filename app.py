import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import io

# -- PAGE CONFIG --
st.set_page_config(page_title="KESCO Billing Analysis", layout="wide", page_icon="⚡")

# -- CUSTOM CSS & THEMING --
st.markdown("""
<style>
    /* Card styling for metrics */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
    }
    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        border: 1px solid #0055A4;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-color: #0055A4;
    }
    /* Section Headers */
    h2 {
        color: #1E293B;
        font-weight: 700;
        margin-top: 1.5rem;
    }
    /* Top padding reduction */
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# -- HERO BANNER & TITLE --
if Path("assets/kesco_banner.png").exists():
    st.image("assets/kesco_banner.png", use_container_width=True)
else:
    st.title("⚡ KESCO Kanpur Billing Analysis")
    
st.markdown("<h2 style='text-align: center; color: #0055A4; margin-bottom: 30px;'>Billing Analysis & Validation Dashboard</h2>", unsafe_allow_html=True)

# -- INITIALIZE FOLDERS --
DATA_DIR = Path("data")
OUTPUTS_DIR = Path("outputs")
DATA_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# -- SESSION STATE INIT --
if 'base_df' not in st.session_state:
    st.session_state['base_df'] = None
if 'merged_df' not in st.session_state:
    st.session_state['merged_df'] = None
if 'active_year' not in st.session_state:
    st.session_state['active_year'] = "2024"
if 'active_month' not in st.session_state:
    st.session_state['active_month'] = "April"
if 'filter_reset_trigger' not in st.session_state:
    st.session_state['filter_reset_trigger'] = 0

def get_workspace_path():
    year = st.session_state['active_year']
    month = st.session_state['active_month']
    path = DATA_DIR / year / month
    path.mkdir(parents=True, exist_ok=True)
    return path

def classify_smart_meter(meter_val):
    if pd.isna(meter_val) or meter_val == "":
        return "Others"
    meter_str = str(meter_val).strip()
    if meter_str.startswith("GP"):
        return "GP"
    elif meter_str.startswith("GE"):
        return "GENUS"
    elif meter_str.startswith("LT"):
        return "LT"
    elif meter_str.startswith("Y"):
        return "Y"
    else:
        return "Others"

def load_and_prepare_df(file_bytes, file_name):
    with st.spinner(f"Loading {file_name}..."):
        # read_excel loads fully into memory; showing spinner as progress indicator
        df = pd.read_excel(file_bytes)
        
        # Apply smart meter classification in strict order
        if 'METER_SERIAL_NBR' in df.columns:
            df['SMART_METER_CLASS'] = df['METER_SERIAL_NBR'].apply(classify_smart_meter)
        else:
            df['SMART_METER_CLASS'] = "Others"
            
        return df

def get_filter_options(df, col_name, default_all=True):
    if df is not None and col_name in df.columns:
        opts = sorted([str(x) for x in df[col_name].dropna().unique()])
        if default_all:
            return ["All"] + opts
        return opts
    return ["All"]

def apply_filters(df):
    if df is None:
        return None
    filtered = df.copy()
    
    # Filter 1: SMART_METER_CLASS
    sm_filter = st.session_state.get('f_smart_meter', ["All"])
    if "All" not in sm_filter and sm_filter:
        filtered = filtered[filtered['SMART_METER_CLASS'].isin(sm_filter)]
        
    # Filter 2: GOVT
    govt_filter = st.session_state.get('f_govt', ["All"])
    if "All" not in govt_filter and govt_filter:
        if "Others" in govt_filter and "GOVTTT" in govt_filter:
            pass # basically all
        elif "GOVTTT" in govt_filter:
            filtered = filtered[filtered['GOVT'] == "GOVTTT"]
        elif "Others" in govt_filter:
            filtered = filtered[filtered['GOVT'] != "GOVTTT"]
            
    # Filter 3: BILL_BASIS
    bb_filter = st.session_state.get('f_bill_basis', ["All"])
    if "All" not in bb_filter and bb_filter:
        named_opts = ["ASS", "CEIL", "MU", "PROV"]
        selected_named = [x for x in bb_filter if x in named_opts]
        
        conditions = []
        if selected_named:
            conditions.append(filtered['BILL_BASIS'].isin(selected_named))
        if "Others" in bb_filter:
            conditions.append(~filtered['BILL_BASIS'].isin(named_opts))
            
        if conditions:
            # Combine multiple conditions with OR
            combined = conditions[0]
            for c in conditions[1:]:
                combined = combined | c
            filtered = filtered[combined]

    # Filter 4: TARIFF_TYPE
    tt_filter = st.session_state.get('f_tariff_type', ["All"])
    if "All" not in tt_filter and tt_filter:
        filtered = filtered[filtered['TARIFF_TYPE'].isin(tt_filter)]
        
    return filtered

# -- SECTION 1: SIDEBAR --
with st.sidebar:
    st.header("Workspace Settings")
    years = [str(y) for y in range(2024, 2029)]
    months = ["April", "May", "June", "July", "August", "September", "October", "November", "December", "January", "February", "March"]
    
    st.session_state['active_year'] = st.selectbox("Select Year", years, index=years.index(st.session_state['active_year']))
    st.session_state['active_month'] = st.selectbox("Select Month", months, index=months.index(st.session_state['active_month']))
    st.markdown(f"**Active Workspace:**\n`{get_workspace_path()}`")

# -- SECTION 6: EXPORT (TOP BAR) --
st.markdown("## 📤 Export Options")
export_col1, export_col2 = st.columns(2)
with export_col1:
    if st.session_state['merged_df'] is not None:
        merged_rename = st.text_input("Filename for Merged Export", value=f"merged_{st.session_state['active_year']}_{st.session_state['active_month']}.xlsx", key="export_merged_rename")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            st.session_state['merged_df'].to_excel(writer, index=False)
        st.download_button(
            label="Download Merged File",
            data=buffer.getvalue(),
            file_name=merged_rename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.button("Download Merged File", disabled=True)

with export_col2:
    today_str = datetime.now().strftime("%Y-%m-%d")
    analysis_file_path = OUTPUTS_DIR / f"{today_str}_analysis.xlsx"
    analysis_rename = st.text_input("Filename for Analysis Export", value=f"analysis_{today_str}.xlsx", key="export_analysis_rename")
    
    if analysis_file_path.exists():
        with open(analysis_file_path, "rb") as f:
            st.download_button(
                label="Download Today's Analysis",
                data=f,
                file_name=analysis_rename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("No analysis saved today yet")

st.divider()

# -- SECTION 2: FILE MANAGEMENT --
st.markdown("## 📁 File Management")
fm_col1, fm_col2 = st.columns(2)

with fm_col1:
    st.subheader("Base File")
    base_file = st.file_uploader("Upload Base File", type=['xlsx'], key="base_uploader")
    base_rename = st.text_input("Save as", value="base.xlsx", key="base_rename")
    base_dest = get_workspace_path() / base_rename
    if base_dest.exists():
        st.warning(f"File exists. Last modified: {datetime.fromtimestamp(base_dest.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    if base_file is not None:
        if st.button("Save & Load Base File"):
            # Save to disk
            with open(base_dest, "wb") as f:
                f.write(base_file.getvalue())
            # Load into session state
            st.session_state['base_df'] = load_and_prepare_df(base_file, base_rename)
            st.success(f"Loaded successfully!")
            
    if st.session_state['base_df'] is not None:
        st.metric("Rows", f"{len(st.session_state['base_df']):,}")
        st.metric("Columns", f"{len(st.session_state['base_df'].columns):,}")

with fm_col2:
    st.subheader("Merged File")
    merged_file = st.file_uploader("Upload Merged File", type=['xlsx'], key="merged_uploader")
    merged_rename = st.text_input("Save as", value="merged.xlsx", key="merged_rename")
    merged_dest = get_workspace_path() / merged_rename
    if merged_dest.exists():
        st.warning(f"File exists. Last modified: {datetime.fromtimestamp(merged_dest.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        
    if merged_file is not None:
        if st.button("Save & Load Merged File"):
            # Save to disk
            with open(merged_dest, "wb") as f:
                f.write(merged_file.getvalue())
            # Load into session state
            st.session_state['merged_df'] = load_and_prepare_df(merged_file, merged_rename)
            st.session_state['merged_rename_latest'] = merged_rename
            st.success(f"Loaded successfully!")

    if st.session_state['merged_df'] is not None:
        st.metric("Rows", f"{len(st.session_state['merged_df']):,}")
        st.metric("Columns", f"{len(st.session_state['merged_df'].columns):,}")

st.divider()

# -- SECTION 3: FILTER AREA --
with st.expander("🔍 Advanced Data Filters", expanded=True):
    if st.button("Clear All Filters"):
        st.session_state['filter_reset_trigger'] += 1

    reset_key = str(st.session_state['filter_reset_trigger'])

    filt_col1, filt_col2, filt_col3, filt_col4 = st.columns(4)

    with filt_col1:
        st.multiselect("Smart Meter Type", ["All", "GENUS", "GP", "LT", "Y", "Others"], default=["All"], key=f"f_smart_meter_{reset_key}")
        st.session_state['f_smart_meter'] = st.session_state[f"f_smart_meter_{reset_key}"]

    with filt_col2:
        st.multiselect("GOVT", ["All", "GOVTTT", "Others"], default=["All"], key=f"f_govt_{reset_key}")
        st.session_state['f_govt'] = st.session_state[f"f_govt_{reset_key}"]

    with filt_col3:
        st.multiselect("Bill Basis", ["All", "ASS", "CEIL", "MU", "PROV", "Others"], default=["All"], key=f"f_bill_basis_{reset_key}")
        st.session_state['f_bill_basis'] = st.session_state[f"f_bill_basis_{reset_key}"]

    with filt_col4:
        st.multiselect("Tariff Type", ["All", "HV1", "HV2", "LMV1", "LMV2", "LMV3", "LMV4", "LMV5", "LMV6", "LMV7", "LMV8", "LMV9", "LMV10", "LMV11"], default=["All"], key=f"f_tariff_type_{reset_key}")
        st.session_state['f_tariff_type'] = st.session_state[f"f_tariff_type_{reset_key}"]

    active_filters_text = []
    if "All" not in st.session_state['f_smart_meter'] and st.session_state['f_smart_meter']: active_filters_text.append(f"Smart Meter = {', '.join(st.session_state['f_smart_meter'])}")
    if "All" not in st.session_state['f_govt'] and st.session_state['f_govt']: active_filters_text.append(f"GOVT = {', '.join(st.session_state['f_govt'])}")
    if "All" not in st.session_state['f_bill_basis'] and st.session_state['f_bill_basis']: active_filters_text.append(f"Bill Basis = {', '.join(st.session_state['f_bill_basis'])}")
    if "All" not in st.session_state['f_tariff_type'] and st.session_state['f_tariff_type']: active_filters_text.append(f"Tariff = {', '.join(st.session_state['f_tariff_type'])}")

    if active_filters_text:
        st.markdown(f"<span style='color:#64748B; font-weight: 600;'>Active filters: {' | '.join(active_filters_text)}</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#64748B; font-weight: 600;'>Active filters: None</span>", unsafe_allow_html=True)

st.divider()

# -- SECTION 4: ANALYSIS SECTION --
st.markdown("## 📊 Statistical Analysis")

def compute_freq_table(df, header):
    if df is None or header not in df.columns:
        return None, 0
    
    # Filter df
    f_df = apply_filters(df)
    
    # Count occurrences
    counts = f_df.groupby(header)['ACCT_ID'].count().reset_index(name='Count')
    counts = counts.sort_values(by='Count', ascending=True)
    
    total = counts['Count'].sum()
    
    # Format counts and percentage
    counts['% of Total'] = (counts['Count'] / total * 100).apply(lambda x: f"{x:.2f}%") if total > 0 else "0.00%"
    
    # Total row
    total_row = pd.DataFrame([{header: 'Total', 'Count': total, '% of Total': '100.00%'}])
    counts = pd.concat([counts, total_row], ignore_index=True)
    
    # Apply comma formatting to counts
    counts['Count'] = counts['Count'].apply(lambda x: f"{int(x):,}")
    
    return counts, total

if st.button("Reset Analysis"):
    st.session_state.pop('analysis_file_1', None)
    st.session_state.pop('analysis_header_1', None)
    st.session_state.pop('analysis_file_2', None)
    st.session_state.pop('analysis_header_2', None)

a_col1, a_col2 = st.columns(2)

# File sources
file_options = []
if st.session_state['base_df'] is not None: file_options.append("Base File")
if st.session_state['merged_df'] is not None: file_options.append("Merged File")

with a_col1:
    f1 = st.selectbox("File 1", ["Select..."] + file_options, key="analysis_file_1")
    df1 = None
    if f1 == "Base File": df1 = st.session_state['base_df']
    elif f1 == "Merged File": df1 = st.session_state['merged_df']
    
    h1_options = []
    if df1 is not None:
        h1_options = list(df1.columns)
    
    h1 = st.selectbox("Header 1", ["Select..."] + h1_options, key="analysis_header_1")
    if f1 != "Select..." and h1 != "Select...":
        st.markdown(f"<span style='color:gray'>( {f1} / {h1} )</span>", unsafe_allow_html=True)
        table1, d1_total = compute_freq_table(df1, h1)
        if table1 is not None:
            st.dataframe(table1, hide_index=True, use_container_width=True)

with a_col2:
    f2 = st.selectbox("File 2", ["Select..."] + file_options, key="analysis_file_2")
    df2 = None
    if f2 == "Base File": df2 = st.session_state['base_df']
    elif f2 == "Merged File": df2 = st.session_state['merged_df']
    
    h2_options = []
    if df2 is not None:
        h2_options = list(df2.columns)
        if f1 == f2 and h1 in h2_options:
            h2_options.remove(h1)
            
    h2 = st.selectbox("Header 2", ["Select..."] + h2_options, key="analysis_header_2")
    if f2 != "Select..." and h2 != "Select...":
        st.markdown(f"<span style='color:gray'>( {f2} / {h2} )</span>", unsafe_allow_html=True)
        table2, d2_total = compute_freq_table(df2, h2)
        if table2 is not None:
            st.dataframe(table2, hide_index=True, use_container_width=True)

# Operation Selector
st.subheader("Operation")
ops = ["Select Operation...", "D1 ÷ D2 × 100", "D2 ÷ D1 × 100", "D1 − D2", "D2 − D1", "D1 ÷ D2", "D2 ÷ D1"]
selected_op = st.selectbox("Compare Totals", ops)

if selected_op != "Select Operation..." and f1 != "Select..." and h1 != "Select..." and f2 != "Select..." and h2 != "Select...":
    st.write(f"**D1:** Total from ({f1} / {h1}) = {d1_total:,}")
    st.write(f"**D2:** Total from ({f2} / {h2}) = {d2_total:,}")
    
    result = None
    result_str = ""
    try:
        if selected_op == "D1 ÷ D2 × 100":
            result = (d1_total / d2_total) * 100
            result_str = f"{result:.2f} %"
        elif selected_op == "D2 ÷ D1 × 100":
            result = (d2_total / d1_total) * 100
            result_str = f"{result:.2f} %"
        elif selected_op == "D1 − D2":
            result = d1_total - d2_total
            result_str = f"{result:,}"
        elif selected_op == "D2 − D1":
            result = d2_total - d1_total
            result_str = f"{result:,}"
        elif selected_op == "D1 ÷ D2":
            result = d1_total / d2_total
            result_str = f"{result:.4f}"
        elif selected_op == "D2 ÷ D1":
            result = d2_total / d1_total
            result_str = f"{result:.4f}"
    except ZeroDivisionError:
        result_str = "Error: Division by Zero"
        
    st.metric("Result", result_str)
    
    save_rename = st.text_input("Save Operation As", value=f"{datetime.now().strftime('%Y-%m-%d')}")
    if st.button("Save Operation Output"):
        today = datetime.now().strftime("%Y-%m-%d")
        path = OUTPUTS_DIR / f"{today}_analysis.xlsx"
        
        output_data = pd.DataFrame([
            {"Metric": "D1 Label", "Value": f"({f1} / {h1})"},
            {"Metric": "D2 Label", "Value": f"({f2} / {h2})"},
            {"Metric": "D1 Count", "Value": d1_total},
            {"Metric": "D2 Count", "Value": d2_total},
            {"Metric": "Operation", "Value": selected_op},
            {"Metric": "Result", "Value": result_str}
        ])
        
        if path.exists():
            # Append as new sheet
            with pd.ExcelWriter(path, mode='a', engine='openpyxl') as writer:
                # Find a unique sheet name
                sheet_idx = len(writer.book.sheetnames) + 1
                output_data.to_excel(writer, sheet_name=f"Analysis_{sheet_idx}", index=False)
        else:
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                output_data.to_excel(writer, sheet_name="Analysis_1", index=False)
                
        st.success(f"Saved to {path.absolute()}")

st.divider()

# -- SECTION 5: RECORD UPDATE --
st.markdown("## ⚡ Live Record Update")
search_acct = st.text_input("Enter Account ID (ACCT_ID)")
if st.button("Search") or search_acct:
    if st.session_state['merged_df'] is not None:
        m_df = st.session_state['merged_df']
        # search ACCT_ID 
        # ACCT_ID may be string or numeric, so safe check
        found = m_df[m_df['ACCT_ID'].astype(str) == str(search_acct).strip()]
        
        if not found.empty:
            st.success("Account ID found!")
            record_idx = found.index[0]
            record = found.iloc[0]
            
            st.subheader("Record Details")
            # Vertical table
            record_display = pd.DataFrame({
                'Header': record.index,
                'Value': record.values
            })
            st.dataframe(record_display, hide_index=True, use_container_width=True)
            
            # Update field
            st.subheader("Update Field")
            field_to_update = st.selectbox("Select field to update", list(m_df.columns))
            
            upd_col1, upd_col2 = st.columns(2)
            with upd_col1:
                current_val = record[field_to_update]
                st.text_input("Current Value", value=str(current_val), disabled=True)
            with upd_col2:
                new_val = st.text_input("New Value")
                
            if st.button("Confirm Update"):
                old_val = current_val
                # Update dataframe
                st.session_state['merged_df'].at[record_idx, field_to_update] = new_val
                
                # Write to disk
                merged_dest = get_workspace_path() / st.session_state.get('merged_rename_latest', 'merged.xlsx')
                with st.spinner("Saving changes to disk..."):
                    st.session_state['merged_df'].to_excel(merged_dest, index=False)
                
                st.success(f"Updated ACCT_ID {search_acct} — {field_to_update}: \"{old_val}\" → \"{new_val}\"")
                # Trigger a rerun to show the updated value
                st.rerun()
        else:
            if search_acct:
                st.error("Account ID not found in Merged File")
    else:
        st.warning("Please upload Merged File first to search records.")

