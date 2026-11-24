from dq import checks


def run_all_checks(df, rules=None):
    rules = rules or {}
    steps = {
        "missing values": lambda: checks.check_missing(df),
        "duplicates": lambda: checks.check_duplicates(df),
        "categories": lambda: checks.check_categories(df),
        "gender format": lambda: checks.check_gender(df),
        "invalid values": lambda: checks.check_invalid(df, rules),
        "outliers": lambda: checks.check_outliers(df),
    }
    issues = []
    for name, step in steps.items():
        try:
            issues += step()
        except Exception as e:           # one broken check must not crash the app
            issues.append(checks.make_issue(
                "check_error", "(n/a)", "low", [],
                f"The '{name}' check could not run: {e}",
                "Inspect the data manually",
            ))

    order = {"high": 0, "medium": 1, "low": 2}
    issues.sort(key=lambda i: order[i["severity"]])
    return issues