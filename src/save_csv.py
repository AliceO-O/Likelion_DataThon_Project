# 저장

import os
import pandas as pd

def append_to_csv(rows, csv_path: str):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    new_df = pd.DataFrame(rows)

    if os.path.exists(csv_path):
        old_df = pd.read_csv(csv_path)
        df = pd.concat([old_df, new_df], ignore_index=True)
        df = df.drop_duplicates(
            subset=["target_date", "platform", "keyword"],
            keep="last"
        )
    else:
        df = new_df

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")