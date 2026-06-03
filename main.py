from __future__ import annotations

from typing import Any

import pandas as pd
import mlcroissant as mlc


CROISSANT_URL = (
	"https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset/"
	"croissant/download"
)


def decode_value(value: Any) -> Any:
	"""Convert Croissant values into pandas-friendly Python objects."""

	if isinstance(value, bytes):
		return value.decode("utf-8")
	return value


def load_record_set(dataset: mlc.Dataset, record_set_id: str) -> pd.DataFrame:
	"""Load one Croissant record set into a pandas DataFrame."""

	records = dataset.records(record_set=record_set_id)
	rows = [{key: decode_value(value) for key, value in row.items()} for row in records]
	return pd.DataFrame(rows)


def load_dataset() -> dict[str, pd.DataFrame]:
	"""Load every record set exposed by the dataset metadata."""

	dataset = mlc.Dataset(CROISSANT_URL)
	tables: dict[str, pd.DataFrame] = {}

	for record_set in dataset.metadata.record_sets:
		tables[record_set.uuid] = load_record_set(dataset, record_set.uuid)

	return tables


def main() -> None:
	tables = load_dataset()

	print(f"Loaded {len(tables)} tables from Croissant metadata")
	for table_name, table in tables.items():
		print(f"\n=== {table_name} ===")
		print(table.head())
		print(f"Rows: {len(table):,} | Columns: {len(table.columns):,}")


if __name__ == "__main__":
	main()

