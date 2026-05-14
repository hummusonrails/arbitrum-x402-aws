"""Configuration loader for the x402-aws agent.

Reads from the repo-root .env file. Validates everything up front so failures
surface before any AWS API call.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# AgentCore payments preview regions
SUPPORTED_REGIONS = {"us-east-1", "us-west-2", "eu-central-1", "ap-southeast-2"}
SUPPORTED_PROVIDERS = {"CoinbaseCDP", "StripePrivy"}


def _repo_root() -> Path:
    """Resolve the repo root from this file's location."""
    # src/x402_aws_agent/config.py -> repo root is four levels up
    return Path(__file__).resolve().parents[4]


def _repo_root_env() -> Path:
    """Resolve the repo-root .env from this file's location."""
    return _repo_root() / ".env"


def resolve_repo_relative(path_str: str) -> Path:
    """Resolve a path string against the repo root if it is relative.

    Absolute paths are returned as-is. Relative paths are anchored to the
    repo root rather than the cwd, so callers behave the same whether
    invoked from the repo root, apps/agent, or anywhere else.
    """
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (_repo_root() / p).resolve()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} is required in .env but is missing or empty")
    return value


@dataclass(frozen=True)
class SetupConfig:
    """Inputs for bootstrap (setup-agent). No PAYMENT_* IDs required."""

    region: str
    user_id: str
    provider: str
    linked_email: str
    max_spend_usd: str
    session_expiry_minutes: int
    cdp_api_key_file: str


@dataclass(frozen=True)
class AgentConfig:
    """Inputs for run-agent. All PAYMENT_* IDs required."""

    region: str
    user_id: str
    resource_url: str
    payment_manager_arn: str
    payment_instrument_id: str
    payment_session_id: str


def load_setup_config(env_path: Path | None = None) -> SetupConfig:
    """Load and validate the setup-time config."""
    path = env_path or _repo_root_env()
    load_dotenv(dotenv_path=path, override=True)

    region = _require("AGENTCORE_REGION")
    if region not in SUPPORTED_REGIONS:
        raise ValueError(
            f"AGENTCORE_REGION must be one of {sorted(SUPPORTED_REGIONS)}; got {region!r}"
        )

    provider = _require("AGENTCORE_PROVIDER")
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"AGENTCORE_PROVIDER must be one of {sorted(SUPPORTED_PROVIDERS)}; got {provider!r}"
        )

    user_id = _require("AGENTCORE_USER_ID")
    linked_email = _require("AGENTCORE_LINKED_EMAIL")
    max_spend_usd = _require("AGENTCORE_MAX_SPEND_USD")
    expiry_raw = _require("AGENTCORE_SESSION_EXPIRY_MINUTES")
    try:
        expiry = int(expiry_raw)
    except ValueError as exc:
        raise ValueError(
            f"AGENTCORE_SESSION_EXPIRY_MINUTES must be an integer; got {expiry_raw!r}"
        ) from exc
    cdp_api_key_file = _require("CDP_API_KEY_FILE")

    return SetupConfig(
        region=region,
        user_id=user_id,
        provider=provider,
        linked_email=linked_email,
        max_spend_usd=max_spend_usd,
        session_expiry_minutes=expiry,
        cdp_api_key_file=cdp_api_key_file,
    )


def load_run_config(env_path: Path | None = None) -> AgentConfig:
    """Load and validate the run-time config (post-setup)."""
    path = env_path or _repo_root_env()
    load_dotenv(dotenv_path=path, override=True)

    region = _require("AGENTCORE_REGION")
    user_id = _require("AGENTCORE_USER_ID")
    resource_url = _require("RESOURCE_URL")
    payment_manager_arn = _require("PAYMENT_MANAGER_ARN")
    payment_instrument_id = _require("PAYMENT_INSTRUMENT_ID")
    payment_session_id = _require("PAYMENT_SESSION_ID")

    return AgentConfig(
        region=region,
        user_id=user_id,
        resource_url=resource_url,
        payment_manager_arn=payment_manager_arn,
        payment_instrument_id=payment_instrument_id,
        payment_session_id=payment_session_id,
    )
