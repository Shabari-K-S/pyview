"""Universal tabular data normalization and serialization utilities for PyView."""

from typing import Any, Dict, List, Optional, Tuple, Union
import json
import math


def normalize_tabular_data(data: Any) -> Dict[str, Any]:
    """Normalize various Python tabular data formats into a standard dictionary representation.

    Supports:
    - pandas.DataFrame / pandas.Series
    - polars.DataFrame (duck-typed)
    - list of dicts: [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
    - dict of lists: {'a': [1, 3], 'b': [2, 4]}
    - 2D list/tuple: [[1, 2], [3, 4]]
    - 1D list/tuple: [1, 2, 3]
    """
    if data is None:
        return {
            "columns": [],
            "data": [],
            "index": [],
            "column_types": {},
            "original_type": "none",
        }

    # 1. Pandas DataFrame / Series
    data_type_name = type(data).__name__
    module_name = getattr(type(data), "__module__", "")

    if "pandas" in module_name or data_type_name in ("DataFrame", "Series"):
        try:
            import pandas as pd
            import numpy as np

            if data_type_name == "Series":
                data = data.to_frame()

            columns = [str(c) for c in data.columns]
            index = [str(i) if not isinstance(i, (int, float)) else i for i in data.index.tolist()]

            column_types = {}
            for col in data.columns:
                col_str = str(col)
                dtype = data[col].dtype
                if pd.api.types.is_bool_dtype(dtype):
                    column_types[col_str] = "checkbox"
                elif pd.api.types.is_numeric_dtype(dtype):
                    column_types[col_str] = "number"
                else:
                    column_types[col_str] = "text"

            df_copy = data
            dt_cols = df_copy.select_dtypes(include=["datetime", "datetimetz"]).columns
            if len(dt_cols) > 0:
                df_copy = df_copy.copy()
                for col in dt_cols:
                    df_copy[col] = df_copy[col].astype(str)

            if df_copy.select_dtypes(include=["floating"]).columns.size > 0:
                if df_copy is data:
                    df_copy = df_copy.copy()
                df_copy = df_copy.replace([np.inf, -np.inf], np.nan)

            df_obj = df_copy.astype(object)
            df_clean = df_obj.where(pd.notnull(df_obj), None)
            raw_data = df_clean.values.tolist()

            return {
                "columns": columns,
                "data": raw_data,
                "index": index,
                "column_types": column_types,
                "original_type": "pandas",
            }
        except Exception:
            pass

    # 2. Polars DataFrame (duck-typed)
    if "polars" in module_name or hasattr(data, "to_dicts"):
        try:
            records = data.to_dicts()
            return _normalize_list_of_dicts(records, original_type="polars")
        except Exception:
            pass

    # 3. List of Dicts: [{'col1': val1, 'col2': val2}, ...]
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        return _normalize_list_of_dicts(data, original_type="list_of_dicts")

    # 4. Dict of Lists / Dict of Iterables: {'col1': [v1, v2], 'col2': [v3, v4]}
    if isinstance(data, dict):
        columns = list(data.keys())
        first_col_val = data[columns[0]] if columns else []
        if isinstance(first_col_val, (list, tuple)):
            num_rows = len(first_col_val)
            raw_data = []
            column_types = {}
            for r_idx in range(num_rows):
                row = []
                for c in columns:
                    val = data[c][r_idx] if r_idx < len(data[c]) else None
                    sanitized = _sanitize_value(val)
                    row.append(sanitized)
                    if str(c) not in column_types:
                        column_types[str(c)] = _infer_type(sanitized)
                raw_data.append(row)

            return {
                "columns": [str(c) for c in columns],
                "data": raw_data,
                "index": list(range(num_rows)),
                "column_types": column_types,
                "original_type": "dict_of_lists",
            }
        else:
            # Single-row dict or key-value table: {'Key': 'Val'}
            return _normalize_list_of_dicts([data], original_type="dict")

    # 5. List of Lists / 2D array: [[1, 2], [3, 4]]
    if isinstance(data, (list, tuple)):
        if len(data) == 0:
            return {
                "columns": [],
                "data": [],
                "index": [],
                "column_types": {},
                "original_type": "list_of_lists",
            }

        if isinstance(data[0], (list, tuple)):
            num_cols = len(data[0])
            columns = [f"Col {i + 1}" for i in range(num_cols)]
            raw_data = []
            column_types = {}
            for r_idx, row_raw in enumerate(data):
                row = []
                for c_idx in range(num_cols):
                    val = row_raw[c_idx] if c_idx < len(row_raw) else None
                    sanitized = _sanitize_value(val)
                    row.append(sanitized)
                    col_name = columns[c_idx]
                    if col_name not in column_types:
                        column_types[col_name] = _infer_type(sanitized)
                raw_data.append(row)

            return {
                "columns": columns,
                "data": raw_data,
                "index": list(range(len(data))),
                "column_types": column_types,
                "original_type": "list_of_lists",
            }
        else:
            # 1D List: [1, 2, 3] -> Single column table
            columns = ["Value"]
            raw_data = [[_sanitize_value(v)] for v in data]
            column_types = {"Value": _infer_type(raw_data[0][0]) if raw_data else "text"}
            return {
                "columns": columns,
                "data": raw_data,
                "index": list(range(len(data))),
                "column_types": column_types,
                "original_type": "list",
            }

    # Fallback
    return {
        "columns": ["Value"],
        "data": [[_sanitize_value(data)]],
        "index": [0],
        "column_types": {"Value": "text"},
        "original_type": "scalar",
    }


def _normalize_list_of_dicts(records: List[Dict[str, Any]], original_type: str = "list_of_dicts") -> Dict[str, Any]:
    """Helper to normalize a list of dicts into uniform column & row arrays."""
    if not records:
        return {
            "columns": [],
            "data": [],
            "index": [],
            "column_types": {},
            "original_type": original_type,
        }

    # Collect ordered union of keys
    columns = []
    seen = set()
    for row in records:
        if isinstance(row, dict):
            for k in row.keys():
                if k not in seen:
                    seen.add(k)
                    columns.append(k)

    str_columns = [str(c) for c in columns]
    raw_data = []
    column_types: Dict[str, str] = {}
    unresolved_cols = set(str_columns)

    for row in records:
        row_arr = []
        is_dict = isinstance(row, dict)
        for c, c_str in zip(columns, str_columns):
            val = row.get(c, None) if is_dict else None
            sanitized = _sanitize_value(val)
            row_arr.append(sanitized)
            if c_str in unresolved_cols and sanitized is not None:
                column_types[c_str] = _infer_type(sanitized)
                unresolved_cols.remove(c_str)
        raw_data.append(row_arr)

    # Set default type for remaining columns
    for c_str in unresolved_cols:
        column_types[c_str] = "text"

    return {
        "columns": str_columns,
        "data": raw_data,
        "index": list(range(len(records))),
        "column_types": column_types,
        "original_type": original_type,
    }


def reconstruct_tabular_data(edited_payload: Any, original_data: Any) -> Any:
    """Reconstruct an updated Python object from the edited payload matching the original type."""
    if not isinstance(edited_payload, dict):
        if isinstance(edited_payload, list):
            return _convert_to_original_type(edited_payload, original_data)
        return original_data

    columns = edited_payload.get("columns", [])
    data_rows = edited_payload.get("data", [])
    indices = edited_payload.get("index", None)

    module_name = getattr(type(original_data), "__module__", "")
    type_name = type(original_data).__name__

    # Fast path for Pandas DataFrame: avoid creating temporary list of dicts
    if "pandas" in module_name or type_name == "DataFrame":
        try:
            import pandas as pd
            df = pd.DataFrame(data_rows, columns=columns)
            if indices and len(indices) == len(df):
                df.index = indices
            return df
        except Exception:
            pass

    # Build list of dict records for non-DataFrame types
    records = []
    for row in data_rows:
        rec = {}
        for c_idx, col_name in enumerate(columns):
            rec[col_name] = row[c_idx] if c_idx < len(row) else None
        records.append(rec)

    return _convert_to_original_type(records, original_data, columns=columns, indices=indices, data_rows=data_rows)


def _convert_to_original_type(records: List[Dict[str, Any]], original_data: Any, columns=None, indices=None, data_rows=None) -> Any:
    """Convert records to matching input type (pandas DataFrame, polars, dict_of_lists, list_of_dicts)."""
    module_name = getattr(type(original_data), "__module__", "")
    type_name = type(original_data).__name__

    # 1. Pandas DataFrame
    if "pandas" in module_name or type_name == "DataFrame":
        try:
            import pandas as pd
            df = pd.DataFrame(records)
            if indices and len(indices) == len(df):
                df.index = indices
            return df
        except Exception:
            pass

    # 2. Polars DataFrame
    if "polars" in module_name:
        try:
            import polars as pl
            return pl.DataFrame(records)
        except Exception:
            pass

    # 3. Dict of lists: {'ColA': [1, 2], 'ColB': [3, 4]}
    if isinstance(original_data, dict):
        first_val = next(iter(original_data.values()), None)
        if isinstance(first_val, (list, tuple)):
            cols = columns or (list(records[0].keys()) if records else list(original_data.keys()))
            dict_of_lists = {c: [] for c in cols}
            for rec in records:
                for c in cols:
                    dict_of_lists[c].append(rec.get(c, None))
            return dict_of_lists
        else:
            return records[0] if records else {}

    # 4. List of lists: [[1, 2], [3, 4]]
    if isinstance(original_data, list) and original_data and isinstance(original_data[0], list):
        if data_rows is not None:
            return data_rows
        cols = columns or (list(records[0].keys()) if records else [])
        return [[rec.get(c, None) for c in cols] for rec in records]

    # Default: list of dicts
    return records


def _sanitize_value(val: Any) -> Any:
    """Convert numpy scalars, datetime objects, and other types to JSON-safe primitives."""
    if val is None:
        return None
    t = type(val)
    if t is int or t is str or t is bool:
        return val
    if t is float:
        return None if (math.isnan(val) or math.isinf(val)) else val
    if hasattr(val, "item"):
        try:
            native = val.item()
            if isinstance(native, float) and (math.isnan(native) or math.isinf(native)):
                return None
            return native
        except Exception:
            pass
    if hasattr(val, "isoformat"):
        return val.isoformat()
    val_type = t.__name__
    if "int" in val_type:
        return int(val)
    if "float" in val_type:
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if "bool" in val_type:
        return bool(val)
    return str(val)


def _infer_type(val: Any) -> str:
    """Infer simple UI type classification for a value."""
    if isinstance(val, bool):
        return "checkbox"
    if isinstance(val, (int, float)):
        return "number"
    return "text"
