"""BigQuery storage for market OHLCV data."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from google.api_core import exceptions as gcp_exceptions
from google.cloud import bigquery

TABLE_PREFIX = "ohlcv_"

SCHEMA = [
    bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("open", "FLOAT64"),
    bigquery.SchemaField("high", "FLOAT64"),
    bigquery.SchemaField("low", "FLOAT64"),
    bigquery.SchemaField("close", "FLOAT64"),
    bigquery.SchemaField("volume", "INT64"),
    bigquery.SchemaField("collected_at", "TIMESTAMP"),
]


class BigQueryStore:
    """Read/write OHLCV data to BigQuery."""

    def __init__(
        self,
        project_id: str,
        dataset_id: str = "kubera_market",
        key_path: str | None = None,
    ) -> None:
        self.project_id = project_id
        self.dataset_id = dataset_id

        if key_path:
            self.client = bigquery.Client.from_service_account_json(
                key_path, project=project_id
            )
        else:
            self.client = bigquery.Client(project=project_id)

        self._ensure_dataset()

    def _ensure_dataset(self) -> None:
        dataset_ref = f"{self.project_id}.{self.dataset_id}"
        dataset = bigquery.Dataset(dataset_ref)
        self.client.create_dataset(dataset, exists_ok=True)

    def _table_id(self, market: str) -> str:
        return f"{self.project_id}.{self.dataset_id}.{TABLE_PREFIX}{market}"

    def _ensure_table(self, market: str) -> None:
        table_id = self._table_id(market)
        table = bigquery.Table(table_id, schema=SCHEMA)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="date",
        )
        table.clustering_fields = ["symbol"]
        self.client.create_table(table, exists_ok=True)

    def upsert_ohlcv(
        self, df: pd.DataFrame, market: str, symbol: str
    ) -> None:
        """Insert OHLCV data, replacing existing rows for the same symbol+date."""
        self._ensure_table(market)
        table_id = self._table_id(market)

        df = df.copy()
        df["symbol"] = symbol
        df["collected_at"] = datetime.now(timezone.utc)

        # Delete existing rows for this symbol in the date range
        min_date = df["date"].min()
        max_date = df["date"].max()
        delete_query = f"""
            DELETE FROM `{table_id}`
            WHERE symbol = @symbol
              AND date BETWEEN @min_date AND @max_date
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("symbol", "STRING", symbol),
                bigquery.ScalarQueryParameter("min_date", "DATE", min_date),
                bigquery.ScalarQueryParameter("max_date", "DATE", max_date),
            ]
        )
        self.client.query(delete_query, job_config=job_config).result()

        # Insert new rows
        job_config = bigquery.LoadJobConfig(
            schema=SCHEMA,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )
        self.client.load_table_from_dataframe(
            df[["symbol", "date", "open", "high", "low", "close", "volume", "collected_at"]],
            table_id,
            job_config=job_config,
        ).result()

    def query_ohlcv(
        self,
        market: str,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """Query OHLCV data from BigQuery."""
        table_id = self._table_id(market)

        query = f"""
            SELECT date, open, high, low, close, volume
            FROM `{table_id}`
            WHERE symbol = @symbol
        """
        params = [bigquery.ScalarQueryParameter("symbol", "STRING", symbol)]

        if start:
            query += " AND date >= @start"
            params.append(bigquery.ScalarQueryParameter("start", "DATE", start))
        if end:
            query += " AND date <= @end"
            params.append(bigquery.ScalarQueryParameter("end", "DATE", end))

        query += " ORDER BY date"

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        df = self.client.query(query, job_config=job_config).to_dataframe()

        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        return df

    def list_symbols(self, market: str) -> list[str]:
        """List all symbols in a market table."""
        table_id = self._table_id(market)

        query = f"SELECT DISTINCT symbol FROM `{table_id}` ORDER BY symbol"
        try:
            df = self.client.query(query).to_dataframe()
            return df["symbol"].tolist()
        except gcp_exceptions.NotFound:
            return []
