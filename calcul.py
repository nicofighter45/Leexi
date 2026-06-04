import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path


def visualize_tables(tables: dict[str, pd.DataFrame]) -> None:
    for table_name, data_frame in tables.items():
        print(f"\nTable {table_name} variables:")
        for var in data_frame.columns:
            print(f"{var.split('/', 1)[1]} ({data_frame[var].dtype})")


def show_mrr(tables: dict[str, pd.DataFrame]) -> None:
    subscriptions = tables["ravenstack_subscriptions.csv"].rename(
        columns=lambda column_name: column_name.split("/", 1)[1]
    )

    start_month = subscriptions["start_date"].dt.to_period("M")
    end_month = subscriptions["end_date"].dt.to_period("M")
    last_active_month = pd.concat([start_month, end_month.dropna()]).max()
    first_active_month = start_month.min()
    month_index = pd.period_range(first_active_month, last_active_month, freq="M")
 
    monthly_mrr = []
    for month in month_index:
        new_subscriptions = start_month == month
        churned_subscriptions = subscriptions["churn_flag"] & end_month.eq(month)
        active_subscriptions = (
            (start_month <= month)
            & (end_month.isna() | (end_month >= month))
        )
        new_mrr = subscriptions.loc[new_subscriptions, "mrr_amount"].sum() / 1_000_000
        churned_mrr = -subscriptions.loc[churned_subscriptions, "mrr_amount"].sum() / 1_000_000
        total_mrr = subscriptions.loc[active_subscriptions, "mrr_amount"].sum() / 1_000_000
        monthly_mrr.append(
            {
                "month": month.to_timestamp(),
                "new_mrr": new_mrr,
                "churned_mrr": churned_mrr,
                "net_mrr_evolution": new_mrr + churned_mrr,
                "total_mrr": total_mrr,
            }
        )

    monthly_mrr_frame = pd.DataFrame(monthly_mrr)

    figure, (movement_axis, total_axis) = plt.subplots(
        2,
        1,
        figsize=(12, 9),
        sharex=True,
        gridspec_kw={"height_ratios": [2, 1]},
    )
    series_styles = [
        ("new_mrr", "New MRR", "#16a34a"),
        ("churned_mrr", "Churned MRR", "#dc2626"),
        ("net_mrr_evolution", "Net MRR evolution", "#2563eb"),
    ]
    for column_name, label, color in series_styles:
        movement_axis.plot(
            monthly_mrr_frame["month"],
            monthly_mrr_frame[column_name],
            marker="o",
            linewidth=2.5,
            color=color,
            label=label,
        )
        for month, value in zip(monthly_mrr_frame["month"], monthly_mrr_frame[column_name]):
            movement_axis.annotate(
                f"€{value:.2f}M",
                (month, value),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                fontsize=8,
                color=color,
            )
    movement_axis.axhline(0, color="#9ca3af", linewidth=1)
    movement_axis.set_title("Monthly MRR Movement", pad=12, fontsize=14)
    movement_axis.set_ylabel("MRR (€M)")
    movement_axis.grid(True, axis="y", linestyle="--", alpha=0.3)
    movement_axis.legend()

    total_axis.plot(
        monthly_mrr_frame["month"],
        monthly_mrr_frame["total_mrr"],
        marker="o",
        linewidth=2.5,
        color="#7c3aed",
        label="Total MRR",
    )
    for month, value in zip(monthly_mrr_frame["month"], monthly_mrr_frame["total_mrr"]):
        total_axis.annotate(
            f"€{value:.2f}M",
            (month, value),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=8,
            color="#5b21b6",
        )
    total_axis.set_title("Total MRR", pad=12, fontsize=14)
    total_axis.set_xlabel("Month")
    total_axis.set_ylabel("MRR (€M)")
    total_axis.grid(True, axis="y", linestyle="--", alpha=0.3)
    total_axis.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
    total_axis.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(total_axis.get_xticklabels(), rotation=45, ha="right")
    plt.tight_layout()
    output_path = Path(__file__).resolve().parent / "output" / "monthly_mrr.jpg"
    figure.savefig(output_path, format="jpg", dpi=200, bbox_inches="tight")
    plt.show()


def show_churn(tables: dict[str, pd.DataFrame]) -> None:
    churns = tables["ravenstack_churn_events.csv"].rename(
        columns=lambda column_name: column_name.split("/", 1)[1]
    )
    churns["churn_date"] = pd.to_datetime(churns["churn_date"], errors="coerce")
    churns = churns.dropna(subset=["churn_date"])
    churns["month"] = churns["churn_date"].dt.to_period("M")

    monthly_churn = (
        churns.groupby("month")
        .agg(
            total_churn=("churn_event_id", "count"),
            churn_preceding_upgrade=("preceding_upgrade_flag", "sum"),
            churn_preceding_downgrade=("preceding_downgrade_flag", "sum"),
        )
        .reset_index()
    )

    month_index = pd.period_range(monthly_churn["month"].min(), monthly_churn["month"].max(), freq="M")
    monthly_churn = (
        monthly_churn.set_index("month")
        .reindex(month_index, fill_value=0)
        .rename_axis("month")
        .reset_index()
    )
    monthly_churn["month"] = monthly_churn["month"].dt.to_timestamp()

    figure, axis = plt.subplots(figsize=(12, 6))

    series_styles = [
        (monthly_churn["total_churn"], monthly_churn["total_churn"], "Total churn", "#2563eb"),
        (monthly_churn["churn_preceding_upgrade"]+monthly_churn["churn_preceding_downgrade"], monthly_churn["churn_preceding_upgrade"],"Churn after upgrade", "#16a34a"),
        (monthly_churn["churn_preceding_downgrade"], monthly_churn["churn_preceding_downgrade"], "Churn after downgrade", "#dc2626"),
    ]
    
    for column, column_values, label, color in series_styles:
        axis.fill_between(
            monthly_churn["month"],
            column,
            0,
            color=color,
            alpha=0.3,
            label=label,
        )
        for month, value, column_value in zip(monthly_churn["month"], column, column_values):
            axis.annotate(
                f"{int(column_value)}",
                (month, value),
                textcoords="offset points",
                xytext=(-4, 8),
                ha="center",
                fontsize=10,
                color=color,
            )

    axis.set_title("Monthly Churn", pad=12, fontsize=14)
    axis.set_xlabel("Month")
    axis.set_ylabel("Churn events")
    axis.grid(True, axis="y", linestyle="--", alpha=0.3)
    axis.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(axis.get_xticklabels(), rotation=45, ha="right")
    axis.legend()

    plt.tight_layout()
    output_path = Path(__file__).resolve().parent / "output" / "monthly_churn.jpg"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, format="jpg", dpi=200, bbox_inches="tight")
    plt.show()
