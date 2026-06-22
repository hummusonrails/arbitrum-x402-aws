"""Tests for setup reuse/create decision logic (no AWS calls)."""

from __future__ import annotations

import importlib

import pytest

setup = importlib.import_module("x402_aws_agent.setup")


@pytest.mark.parametrize(
    "force_new,manager_arn,instrument_id,expected",
    [
        # Both ids present and not forcing -> reuse the existing wallet.
        (False, "arn:aws:...:payment-manager/x", "payment-instrument-y", True),
        # --force-new always creates fresh, even with ids present.
        (True, "arn:aws:...:payment-manager/x", "payment-instrument-y", False),
        # First run: no ids yet -> create.
        (False, None, None, False),
        # Partial state (manager but no instrument) -> create, don't half-reuse.
        (False, "arn:aws:...:payment-manager/x", None, False),
        (False, None, "payment-instrument-y", False),
    ],
)
def test_should_reuse(force_new, manager_arn, instrument_id, expected):
    assert setup.should_reuse(force_new, manager_arn, instrument_id) is expected


def test_existing_ids_reads_env(monkeypatch):
    monkeypatch.setenv("PAYMENT_MANAGER_ARN", "arn:aws:...:payment-manager/x")
    monkeypatch.setenv("PAYMENT_INSTRUMENT_ID", "payment-instrument-y")
    assert setup._existing_ids() == (
        "arn:aws:...:payment-manager/x",
        "payment-instrument-y",
    )


def test_existing_ids_blank_is_none(monkeypatch):
    monkeypatch.setenv("PAYMENT_MANAGER_ARN", "   ")
    monkeypatch.setenv("PAYMENT_INSTRUMENT_ID", "")
    assert setup._existing_ids() == (None, None)
