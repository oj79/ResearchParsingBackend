import os
import tabula
import pandas as pd

# If your methods extraction logic is in a separate file (e.g., advanced_methods_extraction.py),
# import it here. We'll assume you have a function named `grobid_extract_methods`.
# Adjust the import path as necessary.
from .advanced_methods_extraction import grobid_extract_methods


def parse_methods_and_tables(pdf_path, pages="all"):
    """
    High-level function that:
      1) Extracts methods text from GROBID (grobid_extract_methods).
      2) Extracts tables from the same PDF using Tabula
         (parse_tables_comprehensive).
      3) Returns a tuple: (methods_text, df_list)
         where 'methods_text' is a string,
         and 'df_list' is a list of DataFrames with table data.
    """

    # 1) Parse methods text via GROBID
    methods_text = ""
    if os.path.exists(pdf_path):
        try:
            methods_text = grobid_extract_methods(pdf_path)
        except Exception as e:
            print(f"ERROR extracting methods: {e}")
    else:
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # 2) Parse tables comprehensively
    df_list = parse_tables_comprehensive(pdf_path, pages=pages)

    return methods_text, df_list


def parse_tables_comprehensive(pdf_path, pages="all"):
    """
    A 'kitchen sink' approach to table extraction using tabula,
    attempting multiple modes (lattice & stream) with rotation off/on.

    Returns a list of DataFrame objects from all attempts combined.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    all_tables = []

    # Attempt 1: Lattice (no rotation)
    df_list1 = _read_pdf_tabula(pdf_path, pages=pages, lattice=True, stream=False, rotate=False)
    all_tables.extend(df_list1)

    # Attempt 2: Stream (no rotation)
    df_list2 = _read_pdf_tabula(pdf_path, pages=pages, lattice=False, stream=True, rotate=False)
    all_tables.extend(df_list2)

    # Attempt 3: Lattice (rotate)
    df_list3 = _read_pdf_tabula(pdf_path, pages=pages, lattice=True, stream=False, rotate=True)
    all_tables.extend(df_list3)

    # Attempt 4: Stream (rotate)
    df_list4 = _read_pdf_tabula(pdf_path, pages=pages, lattice=False, stream=True, rotate=True)
    all_tables.extend(df_list4)

    return all_tables


def _read_pdf_tabula(pdf_path, pages="all", lattice=True, stream=False, rotate=False):
    """
    Helper function calling tabula.read_pdf with specific parameters.
    Returns a list of DataFrame objects.
    """
    print(f"DEBUG: tabula.read_pdf => pages={pages}, lattice={lattice}, stream={stream}, rotate={rotate}")

    try:
        df_list = tabula.read_pdf(
            input_path=pdf_path,
            pages=pages,
            multiple_tables=True,
            lattice=lattice,
            stream=stream,
            guess=True,
            pandas_options={"header": None},  # or tweak if you have known headers
            #rotate=rotate
        )
        return df_list
    except Exception as e:
        print(f"ERROR in tabula.read_pdf (lattice={lattice}, stream={stream}, rotate={rotate}): {e}")
        return []


def tables_to_json(df_list):
    """
    Convert a list of DataFrames into a JSON string for easy display or API returning.
    Each table is stored as a list of dicts (records).
    """
    import json
    output = []
    for df in df_list:
        # Fill NaN with empty strings for cleaner JSON
        table_data = df.fillna("").to_dict(orient="records")
        output.append(table_data)

    return json.dumps(output, indent=2)


def tables_to_csv(df_list):
    """
    Convert a list of DataFrames into a single CSV string,
    separating each table with a marker.
    """
    csv_parts = []
    for i, df in enumerate(df_list, start=1):
        csv_str = df.to_csv(index=False)
        csv_parts.append(f"--- Table {i} ---\n{csv_str}")
    return "\n\n".join(csv_parts)
