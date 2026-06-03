import pandas as pd

def visualize(tables: dict[str, pd.DataFrame]) -> None:
    for table_name, table_info in tables.items():
        print(f"\nTable: {table_name}")
        print("-" * 50)

        print(table_info.head())
    