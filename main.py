from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mlcroissant as mlc
import pandas as pd

import visualisation


CROISSANT_URL = (
	"https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset/"
	"croissant/download"
)
DATA_DIR = Path(__file__).resolve().parent / "data" / "saas_subscription_churn_analytics"
MANIFEST_PATH = DATA_DIR / "manifest.json"


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


def load_dataset_from_remote() -> dict[str, pd.DataFrame]:
	"""Load every record set exposed by the dataset metadata and cache them locally."""

	dataset = mlc.Dataset(CROISSANT_URL)
	tables: dict[str, pd.DataFrame] = {}

	for record_set in dataset.metadata.record_sets:
		tables[record_set.uuid] = load_record_set(dataset, record_set.uuid)

	cache_dataset(tables)
	return tables


def cache_dataset(tables: dict[str, pd.DataFrame]) -> None:
	"""Persist the downloaded dataset locally as CSV files with a manifest."""

	DATA_DIR.mkdir(parents=True, exist_ok=True)
	manifest = {"tables": list(tables.keys())}
	MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

	for table_name, table in tables.items():
		table.to_csv(DATA_DIR / table_name, index=False)


def load_dataset_from_cache() -> dict[str, pd.DataFrame]:
	"""Load the dataset from the local CSV cache."""

	manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
	tables: dict[str, pd.DataFrame] = {}

	for table_name in manifest["tables"]:
		tables[table_name] = pd.read_csv(DATA_DIR / table_name)

	return tables


def cache_exists() -> bool:
	"""Check whether the local dataset cache is complete."""

	if not MANIFEST_PATH.exists():
		return False

	try:
		manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
	except json.JSONDecodeError:
		return False

	return all((DATA_DIR / table_name).exists() for table_name in manifest.get("tables", []))


def load_dataset() -> dict[str, pd.DataFrame]:
	"""Load the dataset from disk when available, otherwise download it once."""

	if cache_exists():
		return load_dataset_from_cache()

	return load_dataset_from_remote()


def main() -> None:
	tables = load_dataset()

	print(f"Loaded {len(tables)} tables")
	visualisation.visualize(tables)    


if __name__ == "__main__":
	main()
