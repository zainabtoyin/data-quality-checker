import pandas as pd
import streamlit as st
from dq.report import run_all_checks
from dq.cleaner import clean

MAX_ROWS = 200_000

ALL_FIXES = ["standardize_text", "fix_gender", "drop_duplicates", "fill_missing"]

# Allowed ranges for the invalid-value check.
# Columns that don't exist in the uploaded file are skipped automatically.
RULES = {
    "age": {"min": 0, "max": 120},
    "quantity": {"min": 0},
    "price": {"min": 0},
}


def load_file(file):
    name = file.name.lower()
    try:
        if name.endswith((".csv", ".tsv")):
            sep = "\t" if name.endswith(".tsv") else ","
            try:
                df = pd.read_csv(file, sep=sep)
            except UnicodeDecodeError:
                file.seek(0)
                df = pd.read_csv(file, sep=sep, encoding="latin-1")
        elif name.endswith((".xlsx", ".xls")):
            xls = pd.ExcelFile(file)
            sheets = xls.sheet_names
            sheet = st.selectbox("Sheet", sheets) if len(sheets) > 1 else sheets[0]
            df = xls.parse(sheet)
        else:
            df = pd.read_json(file)
    except Exception as e:
        return None, f"Could not read this file: {e}"

    if df.empty:
        return None, "The file has no data."
    if len(df) > MAX_ROWS:
        return None, f"File too large ({len(df):,} rows). Limit is {MAX_ROWS:,}."

    df.columns = [str(c).strip() for c in df.columns]
    if df.columns.duplicated().any():
        return None, "The file has duplicate column names. Please rename them and re-upload."
    return df, None


st.title("Data Quality Checker")

file = st.file_uploader(
    "Upload a data file",
    type=["csv", "tsv", "xlsx", "xls", "json"],
)

if file:
    df, error = load_file(file)
    if error:
        st.error(error)
        st.stop()

    st.subheader("Original data (preview, never changed)")
    st.dataframe(df.head(20))

    issues = run_all_checks(df, RULES)
    if not issues:
        st.success("No issues found.")
    else:
        st.subheader(f"{len(issues)} issues found")
    for i in issues:
        with st.expander(f"[{i['severity'].upper()}] {i['column']}: {i['message']}"):
            st.write("Suggestion:", i["suggestion"])
            st.dataframe(df.loc[i["rows"]])

    st.subheader("Clean the data")
    options = st.multiselect(
        "Fixes to apply",
        ALL_FIXES,
        default=ALL_FIXES,
    )
    if options:
        cleaned, log = clean(df, options)
        st.subheader("Change log")
        st.dataframe(log)
        st.subheader("Cleaned data")
        st.dataframe(cleaned)
        st.download_button("Download cleaned CSV",
                           cleaned.to_csv(index=False), "cleaned.csv", "text/csv")
        st.download_button("Download change log",
                           log.to_csv(index=False), "change_log.csv", "text/csv")