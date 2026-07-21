import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler


def handle_missing_values(df: pd.DataFrame, strategy: str = "ffill") -> pd.DataFrame:
    """Handle missing values in DataFrame.

    Args:
        df: Input DataFrame
        strategy: "ffill", "bfill", "mean", "median", or "drop"

    Returns:
        Processed DataFrame
    """
    df = df.copy()
    if strategy == "ffill":
        df = df.ffill().bfill()
    elif strategy == "bfill":
        df = df.bfill().ffill()
    elif strategy in ["mean", "median"]:
        for col in df.select_dtypes(include=[np.number]).columns:
            fill_val = df[col].mean() if strategy == "mean" else df[col].median()
            df[col] = df[col].fillna(fill_val)
    elif strategy == "drop":
        df = df.dropna()
    return df


def remove_duplicates(df: pd.DataFrame, subset: list | None = None) -> pd.DataFrame:
    return df.copy().drop_duplicates(subset=subset)


def detect_outliers_iqr(series: pd.Series) -> tuple:
    """Detect outliers using IQR method.

    Returns:
        (lower_bound, upper_bound, outliers_mask)
    """
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    mask = (series < lower_bound) | (series > upper_bound)
    return lower_bound, upper_bound, mask


def remove_outliers(df: pd.DataFrame, columns: list | None = None) -> pd.DataFrame:
    df = df.copy()
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns
    for col in columns:
        _, _, mask = detect_outliers_iqr(df[col])
        df = df[~mask]
    return df


def scale_features(
    df: pd.DataFrame,
    columns: list | None = None,
    scaler_type: str = "minmax"
) -> tuple[pd.DataFrame, object]:
    """Scale numerical features.

    Args:
        df: Input DataFrame
        columns: Columns to scale (all numeric if None)
        scaler_type: "minmax", "standard", or "robust"

    Returns:
        (scaled_df, fitted_scaler_object)
    """
    df = df.copy()
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns

    if scaler_type == "minmax":
        scaler = MinMaxScaler()
    elif scaler_type == "standard":
        scaler = StandardScaler()
    elif scaler_type == "robust":
        scaler = RobustScaler()
    else:
        raise ValueError(f"Unknown scaler type: {scaler_type}")

    df[columns] = scaler.fit_transform(df[columns])
    return df, scaler


def add_time_features(df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column])

    df["day_of_week"] = df[date_column].dt.dayofweek
    df["day_of_month"] = df[date_column].dt.day
    df["month"] = df[date_column].dt.month
    df["quarter"] = df[date_column].dt.quarter
    return df


def add_lag_features(
    df: pd.DataFrame,
    column: str,
    lags: list[int] = [1, 7, 14]
) -> pd.DataFrame:
    df = df.copy()
    for lag in lags:
        df[f"{column}_lag_{lag}"] = df[column].shift(lag)
    return df


def add_rolling_features(
    df: pd.DataFrame,
    column: str,
    window: int = 7,
    center: bool = False
) -> pd.DataFrame:
    df = df.copy()
    df[f"{column}_roll_mean_{window}"] = df[column].rolling(window=window, center=center).mean()
    df[f"{column}_roll_std_{window}"] = df[column].rolling(window=window, center=center).std()
    df[f"{column}_roll_median_{window}"] = df[column].rolling(window=window, center=center).median()
    return df
