"""Tests for BigQuery store."""

from unittest.mock import MagicMock, patch

import pandas as pd

from quant.core.data import OHLCV_COLUMNS


def _sample_ohlcv():
    return pd.DataFrame({
        "date": ["2024-01-02", "2024-01-03"],
        "open": [71000, 72000],
        "high": [72000, 73000],
        "low": [70500, 71000],
        "close": [71500, 72500],
        "volume": [1000000, 1200000],
    })


@patch("quant.core.data.bigquery.bigquery")
def test_init_creates_dataset(mock_bq):
    mock_client = MagicMock()
    mock_bq.Client.return_value = mock_client

    from quant.core.data.bigquery import BigQueryStore
    store = BigQueryStore(project_id="test-project", dataset_id="test_ds")

    assert store.project_id == "test-project"
    assert store.dataset_id == "test_ds"
    mock_client.create_dataset.assert_called_once()


@patch("quant.core.data.bigquery.bigquery")
def test_init_with_key_path(mock_bq):
    mock_client = MagicMock()
    mock_bq.Client.from_service_account_json.return_value = mock_client

    from quant.core.data.bigquery import BigQueryStore
    store = BigQueryStore(
        project_id="test-project",
        key_path="/path/to/key.json",
    )

    mock_bq.Client.from_service_account_json.assert_called_once_with(
        "/path/to/key.json", project="test-project"
    )
    assert store.project_id == "test-project"


@patch("quant.core.data.bigquery.bigquery")
def test_table_id(mock_bq):
    mock_bq.Client.return_value = MagicMock()

    from quant.core.data.bigquery import BigQueryStore
    store = BigQueryStore(project_id="proj", dataset_id="ds")

    assert store._table_id("krx") == "proj.ds.ohlcv_krx"
    assert store._table_id("crypto") == "proj.ds.ohlcv_crypto"
    assert store._table_id("us") == "proj.ds.ohlcv_us"


@patch("quant.core.data.bigquery.bigquery")
def test_upsert_ohlcv(mock_bq):
    mock_client = MagicMock()
    mock_bq.Client.return_value = mock_client
    mock_query_job = MagicMock()
    mock_client.query.return_value = mock_query_job
    mock_load_job = MagicMock()
    mock_client.load_table_from_dataframe.return_value = mock_load_job

    from quant.core.data.bigquery import BigQueryStore
    store = BigQueryStore(project_id="proj", dataset_id="ds")

    df = _sample_ohlcv()
    store.upsert_ohlcv(df, market="krx", symbol="005930")

    # Should create table, delete existing rows, then insert
    mock_client.create_table.assert_called()
    mock_query_job.result.assert_called_once()  # DELETE query
    mock_load_job.result.assert_called_once()   # INSERT


@patch("quant.core.data.bigquery.bigquery")
def test_query_ohlcv(mock_bq):
    mock_client = MagicMock()
    mock_bq.Client.return_value = mock_client

    result_df = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        "open": [71000, 72000],
        "high": [72000, 73000],
        "low": [70500, 71000],
        "close": [71500, 72500],
        "volume": [1000000, 1200000],
    })
    mock_query_job = MagicMock()
    mock_query_job.to_dataframe.return_value = result_df
    mock_client.query.return_value = mock_query_job

    from quant.core.data.bigquery import BigQueryStore
    store = BigQueryStore(project_id="proj", dataset_id="ds")
    df = store.query_ohlcv(market="krx", symbol="005930", start="2024-01-02")

    assert len(df) == 2
    # Dates should be formatted as strings
    assert df.iloc[0]["date"] == "2024-01-02"


@patch("quant.core.data.bigquery.bigquery")
def test_query_ohlcv_empty(mock_bq):
    mock_client = MagicMock()
    mock_bq.Client.return_value = mock_client

    mock_query_job = MagicMock()
    mock_query_job.to_dataframe.return_value = pd.DataFrame()
    mock_client.query.return_value = mock_query_job

    from quant.core.data.bigquery import BigQueryStore
    store = BigQueryStore(project_id="proj", dataset_id="ds")
    df = store.query_ohlcv(market="krx", symbol="NONE")

    assert df.empty


@patch("quant.core.data.bigquery.bigquery")
def test_list_symbols(mock_bq):
    mock_client = MagicMock()
    mock_bq.Client.return_value = mock_client

    symbols_df = pd.DataFrame({"symbol": ["005930", "000660", "035720"]})
    mock_query_job = MagicMock()
    mock_query_job.to_dataframe.return_value = symbols_df
    mock_client.query.return_value = mock_query_job

    from quant.core.data.bigquery import BigQueryStore
    store = BigQueryStore(project_id="proj", dataset_id="ds")
    symbols = store.list_symbols("krx")

    assert symbols == ["005930", "000660", "035720"]


@patch("quant.core.data.bigquery.bigquery")
def test_list_symbols_error(mock_bq):
    mock_client = MagicMock()
    mock_bq.Client.return_value = mock_client
    mock_client.query.side_effect = Exception("Table not found")

    from quant.core.data.bigquery import BigQueryStore
    store = BigQueryStore(project_id="proj", dataset_id="ds")
    symbols = store.list_symbols("nonexistent")

    assert symbols == []
