import pandas as pd

def visualize(tables: dict[str, pd.DataFrame]) -> None:
    for table_name, data_frame in tables.items():
        print(f"\nTable {table_name} variables:")
        for var in data_frame.columns:
            print(f"{var.split("/")[1]} ({data_frame[var].dtype})")
    