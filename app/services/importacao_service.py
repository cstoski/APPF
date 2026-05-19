import pandas as pd
from typing import List


def processar_planilha(path: str) -> List[dict]:
    # Accepts xlsx or csv
    if path.lower().endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)
    return df.to_dict(orient="records")
