import os
import io
import math
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
import pandas as pd

app = FastAPI()

# Enable CORS for the local React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("../data")
OUTPUTS_DIR = Path("../outputs")
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory store
STORE = {
    "base_df": None,
    "merged_df": None,
    "active_year": None,
    "active_month": None
}

def get_workspace_path(year: str, month: str):
    path = DATA_DIR / year / month
    path.mkdir(parents=True, exist_ok=True)
    return path

def classify_smart_meter(meter_val):
    if pd.isna(meter_val) or str(meter_val).strip() == "":
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

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...), # "base" or "merged"
    year: str = Form(...),
    month: str = Form(...)
):
    workspace = get_workspace_path(year, month)
    dest_path = workspace / f"{file_type}.xlsx"
    
    contents = await file.read()
    with open(dest_path, "wb") as f:
        f.write(contents)
        
    # Load into pandas
    df = pd.read_excel(io.BytesIO(contents))
    
    if 'METER_SERIAL_NBR' in df.columns:
        df['SMART_METER_CLASS'] = df['METER_SERIAL_NBR'].apply(classify_smart_meter)
    else:
        df['SMART_METER_CLASS'] = "Others"
        
    if file_type == "base":
        STORE["base_df"] = df
    else:
        STORE["merged_df"] = df
        
    STORE["active_year"] = year
    STORE["active_month"] = month
        
    return {
        "status": "success", 
        "rows": len(df), 
        "columns": len(df.columns),
        "headers": list(df.columns)
    }

@app.get("/api/status")
def get_status():
    return {
        "base_loaded": STORE["base_df"] is not None,
        "merged_loaded": STORE["merged_df"] is not None,
        "base_headers": list(STORE["base_df"].columns) if STORE["base_df"] is not None else [],
        "merged_headers": list(STORE["merged_df"].columns) if STORE["merged_df"] is not None else []
    }

@app.post("/api/analysis")
def get_analysis(payload: dict):
    # payload contains filters and selected headers
    filters = payload.get("filters", {})
    f1 = payload.get("f1") # "Base File" or "Merged File"
    h1 = payload.get("h1")
    f2 = payload.get("f2")
    h2 = payload.get("h2")
    
    def apply_filters(df):
        if df is None: return None
        filtered = df.copy()
        
        # Smart Meter
        sm = filters.get("smart_meter", ["All"])
        if "All" not in sm and sm:
            filtered = filtered[filtered['SMART_METER_CLASS'].isin(sm)]
            
        # GOVT
        govt = filters.get("govt", ["All"])
        if "All" not in govt and govt:
            if "GOVTTT" in govt and "Others" not in govt:
                filtered = filtered[filtered['GOVT'] == "GOVTTT"]
            elif "Others" in govt and "GOVTTT" not in govt:
                filtered = filtered[filtered['GOVT'] != "GOVTTT"]
                
        # Bill Basis
        bb = filters.get("bill_basis", ["All"])
        if "All" not in bb and bb:
            named = ["ASS", "CEIL", "MU", "PROV"]
            sel_named = [x for x in bb if x in named]
            conds = []
            if sel_named: conds.append(filtered['BILL_BASIS'].isin(sel_named))
            if "Others" in bb: conds.append(~filtered['BILL_BASIS'].isin(named))
            if conds:
                comb = conds[0]
                for c in conds[1:]: comb = comb | c
                filtered = filtered[comb]
                
        # Tariff
        tt = filters.get("tariff_type", ["All"])
        if "All" not in tt and tt:
            filtered = filtered[filtered['TARIFF_TYPE'].isin(tt)]
            
        return filtered

    def compute_table(file_type, header):
        if file_type == "Base File": df = STORE["base_df"]
        elif file_type == "Merged File": df = STORE["merged_df"]
        else: return None, 0
        
        if df is None or header not in df.columns: return None, 0
        f_df = apply_filters(df)
        
        counts = f_df.groupby(header)['ACCT_ID'].count().reset_index(name='Count')
        counts = counts.sort_values(by='Count', ascending=True)
        total = counts['Count'].sum()
        
        def safe_percent(c, t):
            if t == 0: return "0.00%"
            return f"{(c/t*100):.2f}%"
            
        res = []
        for _, row in counts.iterrows():
            res.append({
                "value": str(row[header]),
                "count": int(row['Count']),
                "percent": safe_percent(row['Count'], total)
            })
            
        return res, int(total)

    t1, d1_tot = compute_table(f1, h1) if f1 and h1 else (None, 0)
    t2, d2_tot = compute_table(f2, h2) if f2 and h2 else (None, 0)
    
    return {
        "table1": t1,
        "d1_total": d1_tot,
        "table2": t2,
        "d2_total": d2_tot
    }

@app.post("/api/save_operation")
def save_operation(payload: dict):
    today = datetime.now().strftime("%Y-%m-%d")
    path = OUTPUTS_DIR / f"{today}_analysis.xlsx"
    
    df = pd.DataFrame([
        {"Metric": "D1 Label", "Value": payload.get("d1_label")},
        {"Metric": "D2 Label", "Value": payload.get("d2_label")},
        {"Metric": "D1 Count", "Value": payload.get("d1_count")},
        {"Metric": "D2 Count", "Value": payload.get("d2_count")},
        {"Metric": "Operation", "Value": payload.get("operation")},
        {"Metric": "Result", "Value": payload.get("result")}
    ])
    
    if path.exists():
        with pd.ExcelWriter(path, mode='a', engine='openpyxl') as writer:
            sheet_idx = len(writer.book.sheetnames) + 1
            df.to_excel(writer, sheet_name=f"Analysis_{sheet_idx}", index=False)
    else:
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Analysis_1", index=False)
            
    return {"status": "success", "file": str(path.absolute())}

@app.get("/api/search/{acct_id}")
def search_record(acct_id: str):
    m_df = STORE["merged_df"]
    if m_df is None:
        raise HTTPException(status_code=400, detail="Merged file not loaded")
        
    found = m_df[m_df['ACCT_ID'].astype(str) == str(acct_id).strip()]
    if found.empty:
        raise HTTPException(status_code=404, detail="Account ID not found")
        
    # Replace NaN/Infinity with None for JSON serialization
    record = found.iloc[0].replace({float('nan'): None, float('inf'): None, float('-inf'): None}).to_dict()
    return {"status": "success", "record": record}

@app.post("/api/update/{acct_id}")
def update_record(acct_id: str, payload: dict):
    m_df = STORE["merged_df"]
    if m_df is None:
        raise HTTPException(status_code=400, detail="Merged file not loaded")
        
    field = payload.get("field")
    new_val = payload.get("value")
    
    found = m_df[m_df['ACCT_ID'].astype(str) == str(acct_id).strip()]
    if found.empty:
        raise HTTPException(status_code=404, detail="Account ID not found")
        
    idx = found.index[0]
    STORE["merged_df"].at[idx, field] = new_val
    
    # Save back to disk
    workspace = get_workspace_path(STORE["active_year"], STORE["active_month"])
    dest_path = workspace / "merged.xlsx"
    STORE["merged_df"].to_excel(dest_path, index=False)
    
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
