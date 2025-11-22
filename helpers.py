import os
from datetime import datetime, timezone
import pandas as pd
from werkzeug.security import generate_password_hash

# Utility: load CSV via pandas and normalize header names
def parse_csv_preserve_fields(filepath):
    """
    Read CSV and return list-of-dicts where:
    - Column names are trimmed (leading/trailing spaces kept trimmed)
    - 'Serial No' (case-insensitive) is ignored/dropped
    - Values are basic Python types; Age converted to int if possible
    """
    df = pd.read_csv(filepath, dtype=str)  # read all as strings to preserve content
    # Trim header whitespace
    df.columns = [c.strip() for c in df.columns]
    # Drop Serial No column variants
    cols_lower = [c.lower() for c in df.columns]
    if 'serial no' in cols_lower:
        idx = cols_lower.index('serial no')
        col_to_drop = df.columns[idx]
        df = df.drop(columns=[col_to_drop])
    # Convert rows to dicts
    records = []
    for _, row in df.iterrows():
        doc = {}
        for k, v in row.items():
            if pd.isna(v):
                continue
            val = v.strip()
            # Try convert Age to int if the column name is Age (case-insensitive)
            if k.strip().lower() == 'age':
                try:
                    doc[k] = int(float(val))
                except:
                    # keep as original string if cannot convert
                    doc[k] = val
            else:
                doc[k] = val
        if doc:
            records.append(doc)
    return records

def ensure_admin_exists(users_col, admin_username, admin_password):
    if users_col.find_one({'username': admin_username, 'role': 'admin'}):
        return
    users_col.insert_one({
        'username': admin_username,
        'password_hash': generate_password_hash(admin_password),
        'name': 'Administrator',
        'email': '',
        'role': 'admin',
        'created_at': datetime.now(timezone.utc)
    })
