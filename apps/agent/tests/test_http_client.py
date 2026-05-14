from unittest.mock import MagicMock

import httpx
import pytest

from x402_aws_agent.http_client import (
    PaidResponse,
    PaymentRequiredError,
    fetch_with_payment,
)


def _http_response(
    status_code: int,
    body: dict | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    request = httpx.Request("GET", "https://example.test/report")
    return httpx.Response(
        status_code,
        request=request,
        json=body,
        headers=headers or {},
    )


def test_fetch_returns_immediately_when_already_paid() -> None:
    transport_calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        transport_calls.append(request)
        return _http_response(200, body={"resource": "premium-market-data"})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    payment_mgr = MagicMock()

    result = fetch_with_payment(
        client=client,
        payment_manager=payment_mgr,
        url="https://example.test/report",
        user_id="u",
        payment_instrument_id="pi",
        payment_session_id="ps",
    )

    assert isinstance(result, PaidResponse)
    assert result.status_code == 200
    assert result.json_body == {"resource": "premium-market-data"}
    assert len(transport_calls) == 1
    payment_mgr.generate_payment_header.assert_not_called()


def test_fetch_pays_on_402_and_retries() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if "x-payment" in {k.lower() for k in request.headers.keys()}:
            return _http_response(
                200,
                body={"resource": "premium-market-data", "txHash": "0xabc"},
            )
        return _http_response(
            402,
            body={
                "x402Version": 2,
                "accepts": [{"scheme": "exact", "network": "eip155:42161"}],
                "error": None,
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    payment_mgr = MagicMock()
    payment_mgr.generate_payment_header.return_value = {
        "X-PAYMENT": "base64-encoded-proof-here"
    }

    result = fetch_with_payment(
        client=client,
        payment_manager=payment_mgr,
        url="https://example.test/report",
        user_id="u",
        payment_instrument_id="pi",
        payment_session_id="ps",
    )

    assert isinstance(result, PaidResponse)
    assert result.status_code == 200
    assert result.json_body["txHash"] == "0xabc"
    assert len(calls) == 2
    payment_mgr.generate_payment_header.assert_called_once()
    second = calls[1]
    assert second.headers["X-PAYMENT"] == "base64-encoded-proof-here"


def test_fetch_raises_when_second_request_still_402() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _http_response(
            402,
            body={"x402Version": 2, "accepts": [], "error": "still no"},
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    payment_mgr = MagicMock()
    payment_mgr.generate_payment_header.return_value = {"X-PAYMENT": "proof"}

    with pytest.raises(PaymentRequiredError):
        fetch_with_payment(
            client=client,
            payment_manager=payment_mgr,
            url="https://example.test/report",
            user_id="u",
            payment_instrument_id="pi",
            payment_session_id="ps",
        )
