import pandas as pd
from dq.checks import text_columns, gender_columns, GENDER_MAP


def _tidy(value):
    # only touch real strings; leave numbers, dates and blanks alone
    return value.strip().title() if isinstance(value, str) else value


def clean(df, actions):
    df = df.copy()          # never touch the original
    log = []

    if "standardize_text" in actions:
        for col in text_columns(df):
            before = df[col].copy()
            df[col] = df[col].map(_tidy)
            changed = (before != df[col]) & before.notna()
            if changed.any():
                log.append({
                    "action": "standardize_text",
                    "column": col,
                    "rows_affected": int(changed.sum()),
                    "detail": "Trimmed spaces and applied Title Case",
                })

    if "fix_gender" in actions:
        for col in gender_columns(df):
            before = df[col].copy()
            df[col] = df[col].map(
                lambda v: GENDER_MAP.get(v.strip().lower(), v) if isinstance(v, str) else v
            )
            changed = (before != df[col]) & before.notna()
            if changed.any():
                log.append({
                    "action": "fix_gender",
                    "column": col,
                    "rows_affected": int(changed.sum()),
                    "detail": "Changed M/F to Male/Female",
                })

    if "drop_duplicates" in actions:
        dup_rows = df.index[df.duplicated(keep="first")]
        if len(dup_rows):
            df = df.drop(index=dup_rows)
            log.append({
                "action": "drop_duplicates",
                "column": "(all columns)",
                "rows_affected": len(dup_rows),
                "detail": f"Removed rows {list(dup_rows)}",
            })

    if "fill_missing" in actions:
        for col in df.columns:
            n = int(df[col].isna().sum())
            if n == 0:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                value = df[col].median()
                method = "median"
                if pd.isna(value):          # column is entirely empty
                    continue
            else:
                if df[col].mode().empty:
                    continue
                value = df[col].mode().iloc[0]
                method = "most common value"
            df[col] = df[col].fillna(value)
            log.append({
                "action": "fill_missing",
                "column": col,
                "rows_affected": n,
                "detail": f"Filled with {method}: {value}",
            })

    return df, pd.DataFrame(log)