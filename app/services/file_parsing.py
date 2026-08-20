import io

import pandas as pd

EXCEL_EXTENSIONS = (".xlsx", ".xls")


def load_raw_grid(content: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith(EXCEL_EXTENSIONS):
        return pd.read_excel(io.BytesIO(content), header=None, dtype=str, engine="openpyxl")

    text = content.decode("utf-8-sig")
    return pd.read_csv(io.StringIO(text), header=None, dtype=str)


def find_header_row(grid: pd.DataFrame, expected_header: list[str]) -> int | None:
    for i, row in grid.iterrows():
        cells = [str(c).strip() if pd.notna(c) else "" for c in row.tolist()]
        if cells[: len(expected_header)] == expected_header:
            return i
    return None
