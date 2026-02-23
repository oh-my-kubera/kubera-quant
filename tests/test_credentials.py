"""Tests for credentials module."""

from quant.core.credentials import (
    get_credential,
    load_credentials,
    remove_credential,
    save_credential,
)


def test_save_and_load(quant_dir):
    save_credential({"provider": "bigquery", "project_id": "test-project"})
    credentials = load_credentials()
    assert len(credentials) == 1
    assert credentials[0]["provider"] == "bigquery"
    assert credentials[0]["project_id"] == "test-project"


def test_save_replaces_existing(quant_dir):
    save_credential({"provider": "bigquery", "project_id": "old"})
    save_credential({"provider": "bigquery", "project_id": "new"})
    credentials = load_credentials()
    assert len(credentials) == 1
    assert credentials[0]["project_id"] == "new"


def test_get_credential(quant_dir):
    save_credential({"provider": "bigquery", "project_id": "test"})
    cred = get_credential("bigquery")
    assert cred is not None
    assert cred["project_id"] == "test"


def test_get_credential_missing(quant_dir):
    assert get_credential("nonexistent") is None


def test_remove_credential(quant_dir):
    save_credential({"provider": "bigquery", "project_id": "test"})
    assert remove_credential("bigquery") is True
    assert get_credential("bigquery") is None


def test_remove_credential_missing(quant_dir):
    assert remove_credential("nonexistent") is False


def test_multiple_providers(quant_dir):
    save_credential({"provider": "bigquery", "project_id": "proj"})
    save_credential({"provider": "upbit", "access_key": "key"})
    credentials = load_credentials()
    assert len(credentials) == 2
    assert get_credential("bigquery")["project_id"] == "proj"
    assert get_credential("upbit")["access_key"] == "key"
