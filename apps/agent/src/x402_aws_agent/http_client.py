"""HTTP client that handles the x402 402-pay-retry flow.

Uses the bedrock-agentcore SDK's PaymentManager.generate_payment_header to
convert a 402 response into an X-PAYMENT header value, then retries the
original request.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

# The merchant only advertises Arbitrum One in its accepts[] payload.
# Passing this explicitly avoids any ambiguity if AgentCore's default network
# preferences ever change.
ARBITRUM_ONE_NETWORK_PREFERENCES = ["eip155:42161"]


class PaymentRequiredError(RuntimeError):
    """Raised when the merchant still returns 402 after we submit a payment proof."""


class _PaymentManagerLike(Protocol):
    def generate_payment_header(
        self,
        *,
        payment_instrument_id: str,
        payment_session_id: str,
        payment_required_request: dict[str, Any],
        user_id: str | None = ...,
        network_preferences: list[str] | None = ...,
        client_token: str | None = ...,
    ) -> dict[str, str]: ...


@dataclass
class PaidResponse:
    status_code: int
    headers: dict[str, str]
    json_body: dict[str, Any]


def fetch_with_payment(
    *,
    client: httpx.Client,
    payment_manager: _PaymentManagerLike,
    url: str,
    user_id: str,
    payment_instrument_id: str,
    payment_session_id: str,
) -> PaidResponse:
    """GET the merchant URL, handle 402 with AgentCore, return the paid response.

    Flow:
      1. GET url -> if not 402, return.
      2. If 402, call payment_manager.generate_payment_header() with the 402
         response payload.
      3. Retry GET with the returned X-PAYMENT header.
      4. If still 402, raise PaymentRequiredError.
    """
    first = client.get(url)
    if first.status_code != 402:
        return PaidResponse(
            status_code=first.status_code,
            headers=dict(first.headers),
            json_body=first.json() if first.content else {},
        )

    payment_required_request = {
        "statusCode": 402,
        "headers": dict(first.headers),
        "body": first.text,
    }

    proof_headers = payment_manager.generate_payment_header(
        user_id=user_id,
        payment_instrument_id=payment_instrument_id,
        payment_session_id=payment_session_id,
        payment_required_request=payment_required_request,
        network_preferences=ARBITRUM_ONE_NETWORK_PREFERENCES,
        client_token=str(uuid.uuid4()),
    )

    second = client.get(url, headers=proof_headers)
    if second.status_code == 402:
        raise PaymentRequiredError(
            f"Merchant returned 402 even after submitting payment proof: {second.text}"
        )

    return PaidResponse(
        status_code=second.status_code,
        headers=dict(second.headers),
        json_body=second.json() if second.content else {},
    )
