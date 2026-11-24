import pandas as pd

GENDER_MAP = {"m": "Male", "male": "Male", "f": "Female", "female": "Female"}


def make_issue(check, column, severity, rows, message, suggestion):
    return {
        "check": check,
        "column": column,
        "severity": severity,
        "rows": list(rows),
        "count": len(rows),
        "message": message,
        "suggestion": suggestion,
    }


def text_columns(df):
    """Columns that hold text (works across pandas versions)."""
    return [
        c for c in df.columns
        if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c])
    ]


def gender_columns(df):
    return [c for c in text_columns(df)
            if "gender" in str(c).lower() or "sex" in str(c).lower()]


def check_missing(df):
    issues = []
    for col in df.columns:
        rows = df.index[df[col].isna()]
        if len(rows) == 0:
            continue
        pct = len(rows) / len(df)
        sev = "high" if pct > 0.3 else "medium" if pct > 0.05 else "low"
        issues.append(make_issue(
            "missing_values", col, sev, rows,
            f"{len(rows)} missing values ({pct:.0%})",
            "Fill with median/mode or drop the rows",
        ))
    return issues


def check_duplicates(df):
    rows = df.index[df.duplicated(keep="first")]
    if len(rows) == 0:
        return []
    return [make_issue(
        "duplicates", "(all columns)", "medium", rows,
        f"{len(rows)} duplicate rows",
        "Drop the duplicate rows",
    )]


def check_categories(df):
    issues = []
    for col in text_columns(df):
        s = df[col].dropna().astype(str)
        if s.empty:
            continue
        normalized = s.str.strip().str.lower()
        spellings = s.groupby(normalized).nunique()
        bad = spellings[spellings > 1].index
        if len(bad) == 0:
            continue
        mask = normalized.isin(bad)
        found = sorted(s[mask].unique())
        issues.append(make_issue(
            "inconsistent_categories", col, "medium", s.index[mask],
            f"Same value written differently: {found}",
            "Standardize to one spelling (e.g. Title Case)",
        ))
    return issues


def check_gender(df):
    issues = []
    for col in gender_columns(df):
        s = df[col].dropna().astype(str)
        short = s.str.strip().str.lower().isin(["m", "f"])
        if short.any():
            issues.append(make_issue(
                "gender_format", col, "medium", s.index[short],
                f"Abbreviated values found: {sorted(s[short].unique())}",
                "Change M/F to Male/Female",
            ))
    return issues


def check_invalid(df, rules):
    issues = []
    for col, rule in rules.items():
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        mask = pd.Series(False, index=df.index)
        if "min" in rule:
            mask |= s < rule["min"]
        if "max" in rule:
            mask |= s > rule["max"]
        rows = df.index[mask]
        if len(rows):
            issues.append(make_issue(
                "invalid_values", col, "high", rows,
                f"{len(rows)} values outside allowed range {rule}",
                "Correct or remove these rows",
            ))
    return issues


def check_outliers(df):
    issues = []
    for col in df.select_dtypes(include="number").columns:
        if df[col].notna().sum() < 4:      # too few values to judge
            continue
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        mask = (df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)
        rows = df.index[mask]
        if len(rows):
            issues.append(make_issue(
                "outliers", col, "low", rows,
                f"{len(rows)} unusual values (IQR rule)",
                "Check whether these are typos or real extreme values",
            ))
    return issues