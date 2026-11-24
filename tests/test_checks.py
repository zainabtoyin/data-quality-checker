import pandas as pd
from dq.checks import check_missing, check_duplicates, check_categories
from dq.cleaner import clean
from dq.report import run_all_checks


def test_finds_missing():
    df = pd.DataFrame({"a": [1, None, 3]})
    assert check_missing(df)[0]["count"] == 1


def test_finds_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2]})
    assert check_duplicates(df)[0]["count"] == 1


def test_finds_inconsistent_categories():
    df = pd.DataFrame({"state": ["Lagos", "lagos", "LAGOS", "Abuja"]})
    assert len(check_categories(df)) == 1


def test_clean_data_has_no_issues():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": ["x", "y", "z", "w", "v"]})
    assert run_all_checks(df) == []


def test_single_row_does_not_crash():
    run_all_checks(pd.DataFrame({"a": [1]}))


def test_all_missing_column_does_not_crash():
    df = pd.DataFrame({"a": [None, None, None], "b": [1, 2, 3]})
    run_all_checks(df)
    clean(df, ["fill_missing", "standardize_text", "drop_duplicates"])


def test_mixed_types_are_not_destroyed():
    df = pd.DataFrame({"a": ["ade", 5, "bola"]})
    cleaned, _ = clean(df, ["standardize_text"])
    assert cleaned["a"].iloc[1] == 5


def test_original_is_not_modified():
    df = pd.DataFrame({"s": ["lagos", "LAGOS"]})
    clean(df, ["standardize_text"])
    assert df["s"].tolist() == ["lagos", "LAGOS"]