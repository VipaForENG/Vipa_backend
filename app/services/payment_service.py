from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


class PaymentProviderError(RuntimeError):
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self.payload = payload
        super().__init__(str(payload))


def _drop_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


async def _request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    json: dict[str, Any] | None = None,
    timeout: float = 15.0,
) -> Any:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(method, url, headers=headers, json=json)

    response.encoding = "utf-8"

    if response.status_code >= 400:
        try:
            payload = response.json()
        except ValueError:
            payload = {"message": response.text}
        raise PaymentProviderError(response.status_code, payload)

    if response.status_code == status.HTTP_204_NO_CONTENT or not response.content:
        return {"ok": True}
    return response.json()


class KakaoPayClient:
    def __init__(self) -> None:
        if not settings.KAKAO_PAY_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="KAKAO_PAY_SECRET_KEY is not configured.",
            )

        self.base_url = settings.KAKAO_PAY_API_BASE_URL.rstrip("/")
        self.cid = settings.KAKAO_PAY_CID
        self.subscription_cid = settings.KAKAO_PAY_SUBSCRIPTION_CID
        self.headers = {
            "Authorization": f"SECRET_KEY {settings.KAKAO_PAY_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    async def ready(self, payload: dict[str, Any], *, subscription: bool = False) -> Any:
        request_payload = _drop_none(
            {
                "cid": self.subscription_cid if subscription else self.cid,
                **payload,
            }
        )
        return await _request_json(
            "POST",
            f"{self.base_url}/online/v1/payment/ready",
            headers=self.headers,
            json=request_payload,
        )

    async def approve(self, payload: dict[str, Any], *, subscription: bool = False) -> Any:
        request_payload = _drop_none(
            {
                "cid": self.subscription_cid if subscription else self.cid,
                **payload,
            }
        )
        return await _request_json(
            "POST",
            f"{self.base_url}/online/v1/payment/approve",
            headers=self.headers,
            json=request_payload,
        )

    async def cancel(self, payload: dict[str, Any]) -> Any:
        request_payload = _drop_none({"cid": self.cid, **payload})
        return await _request_json(
            "POST",
            f"{self.base_url}/online/v1/payment/cancel",
            headers=self.headers,
            json=request_payload,
        )

    async def subscription_charge(self, payload: dict[str, Any]) -> Any:
        request_payload = _drop_none({"cid": self.subscription_cid, **payload})
        return await _request_json(
            "POST",
            f"{self.base_url}/online/v1/payment/subscription",
            headers=self.headers,
            json=request_payload,
        )

    async def subscription_status(self, sid: str) -> Any:
        return await _request_json(
            "POST",
            f"{self.base_url}/online/v1/payment/manage/subscription/status",
            headers=self.headers,
            json={"cid": self.subscription_cid, "sid": sid},
        )

    async def subscription_inactive(self, sid: str) -> Any:
        return await _request_json(
            "POST",
            f"{self.base_url}/online/v1/payment/manage/subscription/inactive",
            headers=self.headers,
            json={"cid": self.subscription_cid, "sid": sid},
        )


def handle_provider_error(exc: PaymentProviderError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"provider_error": exc.payload},
    )
