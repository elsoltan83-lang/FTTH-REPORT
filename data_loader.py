import os
import pandas as pd
import numpy as np

COL_NAMES = [
    "Senior_Sector",
    "Sector",
    "Region",
    "Type",
    "New_Completed_YTD",
    "New_Survey_Done_YTD",
    "New_Last_7_Days",
    "New_Yesterday",
    "New_Pending_Survey",
    "Mig_Completed_YTD",
    "Mig_Survey_Done_YTD",
    "Mig_Last_7_Days",
    "Mig_Yesterday",
    "Mig_Pending_Survey",
    "Flagged_Total",
    "Flagged_Last_7_Days",
    "Flagged_Yesterday",
]

NUMERIC_COLS = [
    "New_Completed_YTD",
    "New_Survey_Done_YTD",
    "New_Last_7_Days",
    "New_Yesterday",
    "New_Pending_Survey",
    "Mig_Completed_YTD",
    "Mig_Survey_Done_YTD",
    "Mig_Last_7_Days",
    "Mig_Yesterday",
    "Mig_Pending_Survey",
    "Flagged_Total",
    "Flagged_Last_7_Days",
    "Flagged_Yesterday",
]


def load_raw_data(file_source="FTTH Report.xlsx"):
    """
    Loads and standardizes 'today' and 'yesterday' sheets from Excel file or uploaded bytes/path.
    """
    xl = pd.ExcelFile(file_source)
    sheet_names = xl.sheet_names

    today_sheet = "today" if "today" in sheet_names else sheet_names[1] if len(sheet_names) > 1 else sheet_names[0]
    yesterday_sheet = "yesterday" if "yesterday" in sheet_names else sheet_names[2] if len(sheet_names) > 2 else None

    # Load today sheet
    df_today = pd.read_excel(xl, sheet_name=today_sheet, header=0)
    df_today = _clean_dataframe(df_today)

    df_yesterday = None
    if yesterday_sheet:
        df_yesterday = pd.read_excel(xl, sheet_name=yesterday_sheet, header=0)
        df_yesterday = _clean_dataframe(df_yesterday)

    # Load summary Sheet1 if available
    df_summary = None
    if "Sheet1" in sheet_names:
        try:
            df_summary = pd.read_excel(xl, sheet_name="Sheet1")
        except Exception:
            pass

    return df_today, df_yesterday, df_summary


def _clean_dataframe(df):
    """
    Standardizes column names and types for operational sheets (today / yesterday).
    """
    # If columns count matches or exceeds COL_NAMES, map them
    if len(df.columns) >= len(COL_NAMES):
        df = df.iloc[:, :len(COL_NAMES)].copy()
        df.columns = COL_NAMES
    else:
        # Fallback renaming
        cols = list(df.columns)
        rename_map = {}
        for i, c in enumerate(cols):
            if i < len(COL_NAMES):
                rename_map[c] = COL_NAMES[i]
        df = df.rename(columns=rename_map)

    # Clean text columns
    for col in ["Senior_Sector", "Sector", "Region", "Type"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Drop any total rows or empty rows
    if "Senior_Sector" in df.columns:
        df = df[~df["Senior_Sector"].str.lower().isin(["nan", "none", "", "total", "إجمالي", "المجموع"])]

    # Cast numeric columns
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Add calculated aggregate columns
    df["Total_Completed_YTD"] = df["New_Completed_YTD"] + df["Mig_Completed_YTD"]
    df["Total_Survey_Done_YTD"] = df["New_Survey_Done_YTD"] + df["Mig_Survey_Done_YTD"]
    df["Total_Yesterday"] = df["New_Yesterday"] + df["Mig_Yesterday"]
    df["Total_Last_7_Days"] = df["New_Last_7_Days"] + df["Mig_Last_7_Days"]
    df["Total_Pending_Survey"] = df["New_Pending_Survey"] + df["Mig_Pending_Survey"]

    # Efficiency & Completion Rates (%)
    df["Completion_Rate"] = np.where(
        df["Total_Survey_Done_YTD"] > 0,
        (df["Total_Completed_YTD"] / df["Total_Survey_Done_YTD"] * 100).round(1),
        0.0,
    )
    df["New_Completion_Rate"] = np.where(
        df["New_Survey_Done_YTD"] > 0,
        (df["New_Completed_YTD"] / df["New_Survey_Done_YTD"] * 100).round(1),
        0.0,
    )
    df["Mig_Completion_Rate"] = np.where(
        df["Mig_Survey_Done_YTD"] > 0,
        (df["Mig_Completed_YTD"] / df["Mig_Survey_Done_YTD"] * 100).round(1),
        0.0,
    )

    # Migration Share (%)
    df["Mig_Share"] = np.where(
        df["Total_Completed_YTD"] > 0,
        (df["Mig_Completed_YTD"] / df["Total_Completed_YTD"] * 100).round(1),
        0.0,
    )

    return df


def calculate_comparisons(df_today, df_yesterday):
    """
    Merges today and yesterday to compute daily velocity and deltas.
    """
    if df_yesterday is None or df_today is None:
        return df_today.copy()

    merge_keys = ["Senior_Sector", "Sector", "Region"]
    merged = pd.merge(
        df_today,
        df_yesterday[merge_keys + NUMERIC_COLS + ["Total_Completed_YTD", "Total_Pending_Survey", "Total_Survey_Done_YTD"]],
        on=merge_keys,
        how="left",
        suffixes=("", "_yest"),
    )

    # Daily deltas (Today YTD - Yesterday YTD)
    merged["Delta_Total_Completed"] = merged["Total_Completed_YTD"] - merged["Total_Completed_YTD_yest"].fillna(merged["Total_Completed_YTD"])
    merged["Delta_New_Completed"] = merged["New_Completed_YTD"] - merged["New_Completed_YTD_yest"].fillna(merged["New_Completed_YTD"])
    merged["Delta_Mig_Completed"] = merged["Mig_Completed_YTD"] - merged["Mig_Completed_YTD_yest"].fillna(merged["Mig_Completed_YTD"])
    merged["Delta_Pending_Survey"] = merged["Total_Pending_Survey"] - merged["Total_Pending_Survey_yest"].fillna(merged["Total_Pending_Survey"])
    merged["Delta_Flagged"] = merged["Flagged_Total"] - merged["Flagged_Total_yest"].fillna(merged["Flagged_Total"])

    return merged
