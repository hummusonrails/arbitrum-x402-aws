import os
from pathlib import Path

import pytest

from x402_aws_agent.config import (
    AgentConfig,
    SetupConfig,
    load_run_config,
    load_setup_config,
)


@pytest.fixture
def env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "AGENTCORE_REGION=us-east-1\n"
        "AGENTCORE_USER_ID=test-user\n"
        "AGENTCORE_PROVIDER=CoinbaseCDP\n"
        "AGENTCORE_LINKED_EMAIL=test@example.com\n"
        "AGENTCORE_MAX_SPEND_USD=1.50\n"
        "AGENTCORE_SESSION_EXPIRY_MINUTES=30\n"
        "CDP_API_KEY_FILE=./cdp_api_key.json\n"
        "RESOURCE_URL=https://example.cloudfront.net/report\n"
        "PAYMENT_MANAGER_ARN=arn:aws:bedrock-agentcore:us-east-1:111122223333:payment-manager/test\n"
        "PAYMENT_INSTRUMENT_ID=payment-instrument-abc123\n"
        "PAYMENT_SESSION_ID=payment-session-def456\n"
    )
    monkeypatch.chdir(tmp_path)
    # Clear any env vars from outer process so .env is the source of truth
    for var in [
        "AGENTCORE_REGION",
        "AGENTCORE_USER_ID",
        "AGENTCORE_PROVIDER",
        "AGENTCORE_LINKED_EMAIL",
        "AGENTCORE_MAX_SPEND_USD",
        "AGENTCORE_SESSION_EXPIRY_MINUTES",
        "CDP_API_KEY_FILE",
        "RESOURCE_URL",
        "PAYMENT_MANAGER_ARN",
        "PAYMENT_INSTRUMENT_ID",
        "PAYMENT_SESSION_ID",
    ]:
        monkeypatch.delenv(var, raising=False)
    return env_path


def test_load_setup_config_succeeds(env_file: Path) -> None:
    cfg = load_setup_config(env_path=env_file)
    assert cfg.region == "us-east-1"
    assert cfg.user_id == "test-user"
    assert cfg.provider == "CoinbaseCDP"
    assert cfg.linked_email == "test@example.com"
    assert cfg.max_spend_usd == "1.50"
    assert cfg.session_expiry_minutes == 30
    assert cfg.cdp_api_key_file.endswith("cdp_api_key.json")


def test_load_run_config_succeeds(env_file: Path) -> None:
    cfg = load_run_config(env_path=env_file)
    assert cfg.resource_url == "https://example.cloudfront.net/report"
    assert cfg.payment_manager_arn.startswith("arn:aws:bedrock-agentcore:")
    assert cfg.payment_instrument_id == "payment-instrument-abc123"
    assert cfg.payment_session_id == "payment-session-def456"


def test_load_run_config_rejects_missing_arn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "AGENTCORE_REGION=us-east-1\n"
        "AGENTCORE_USER_ID=test-user\n"
        "RESOURCE_URL=https://example.cloudfront.net/report\n"
    )
    for var in [
        "PAYMENT_MANAGER_ARN",
        "PAYMENT_INSTRUMENT_ID",
        "PAYMENT_SESSION_ID",
    ]:
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValueError, match="PAYMENT_MANAGER_ARN"):
        load_run_config(env_path=env_path)


def test_load_setup_config_rejects_unsupported_region(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "AGENTCORE_REGION=us-east-2\n"
        "AGENTCORE_USER_ID=test-user\n"
        "AGENTCORE_PROVIDER=CoinbaseCDP\n"
        "AGENTCORE_LINKED_EMAIL=test@example.com\n"
        "AGENTCORE_MAX_SPEND_USD=1.00\n"
        "AGENTCORE_SESSION_EXPIRY_MINUTES=60\n"
        "CDP_API_KEY_FILE=./cdp_api_key.json\n"
    )
    monkeypatch.setenv("AGENTCORE_REGION", "us-east-2")
    with pytest.raises(ValueError, match="AGENTCORE_REGION"):
        load_setup_config(env_path=env_path)
