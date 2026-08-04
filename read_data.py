import pandas as pd
import os


def load_and_clean_data_old():
    # Load the data
    df = pd.read_csv("data.csv")

    # 1. Cleanup
    df = (
        df.dropna()
        .query("`Entry Date` != 'Entry Date'")
        .replace({"₹": "", ",": "", "%": ""}, regex=True)
        .reset_index(drop=True)
    )

    # 2. Convert Numeric Columns (Floats & Integers)
    numeric_cols = [
        "Entry",
        "SL",
        "Target",
        "Spot points",
        "Option Entry",
        "Option Exit",
        "Option pts",
        "Option",
        "Lot",
        "PnL",
        "Return on Cap",
        "Capital",
    ]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    # 3. Convert Date Columns
    date_cols = ["Entry Date", "Exit Date"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format="%d/%m/%y", errors="coerce")

    # 4. Convert Time Columns (Optional: keeps them as clean string or converts to time)
    time_cols = ["Entry Time", "Exit Time"]
    for col in time_cols:
        df[col] = pd.to_datetime(df[col], format="%H:%M:%S", errors="coerce").dt.time

    return df


def load_and_clean_data():
    # Load the data
    filename = os.listdir("..")[-3]
    df = pd.read_excel(
        f"../{filename}", engine="odf", skiprows=40, sheet_name="Hourly_Futures"
    )
    print(df.columns.tolist())
    # 1. Cleanup
    df = (
        df.dropna()
        .query("`Entry Date` != 'Entry Date'")
        .replace({"₹": "", ",": "", "%": ""}, regex=True)
        .reset_index(drop=True)
    )
    # 2. Convert Numeric Columns (Floats & Integers)
    numeric_cols = [
        "Entry",
        "SL",
        "Target",
        "Spot points",
        "Option Entry",
        "Option Exit",
        "Option pts",
        "Lot",
        "PnL",
        "Return on Cap",
        "Capital",
    ]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    # 3. Convert Date Columns
    date_cols = ["Entry Date", "Exit Date"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format="%d/%m/%y", errors="coerce")

    # 4. Convert Time Columns (Optional: keeps them as clean string or converts to time)
    time_cols = ["Entry Time", "Exit Time"]
    for col in time_cols:
        df[col] = pd.to_datetime(df[col], format="%H:%M:%S", errors="coerce").dt.time

    df = df.rename(columns={"Unnamed: 17": "Moneyness"})

    return df
