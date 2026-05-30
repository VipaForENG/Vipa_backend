from typing import Any
from html import escape

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.schemas.payment import (
    KakaoPayApproveRequest,
    KakaoPayCancelRequest,
    KakaoPayReadyRequest,
    KakaoPaySubscriptionChargeRequest,
    KakaoPaySubscriptionManageRequest,
)
from app.services.payment_service import (
    KakaoPayClient,
    PaymentProviderError,
    handle_provider_error,
)

router = APIRouter()


def _kakao_redirect_page(title: str, body: str) -> str:
    return f"""
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(title)}</title>
    <style>
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background: #f6f8fb;
        color: #1f2937;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }}
      main {{
        width: min(680px, calc(100% - 32px));
        padding: 28px;
        border-radius: 12px;
        background: #fff;
        box-shadow: 0 12px 30px rgba(31, 41, 55, 0.08);
      }}
      h1 {{ margin: 0 0 12px; font-size: 24px; }}
      p {{ margin: 0 0 16px; color: #526174; line-height: 1.6; }}
      code {{
        display: block;
        overflow-wrap: anywhere;
        padding: 14px;
        border-radius: 8px;
        background: #101828;
        color: #f8fafc;
      }}
    </style>
  </head>
  <body>
    <main>
      {body}
    </main>
  </body>
</html>
"""


@router.get("/kakao/redirect/success", response_class=HTMLResponse)
async def kakao_redirect_success(pg_token: str) -> str:
    safe_token = escape(pg_token)
    return _kakao_redirect_page(
        "KakaoPay payment approved",
        f"""
        <h1>카카오페이 결제 승인 준비 완료</h1>
        <p>아래 pg_token 값을 앱의 결제 승인 입력창에 붙여넣어 주세요.</p>
        <code>{safe_token}</code>
        """,
    )


@router.get("/kakao/redirect/cancel", response_class=HTMLResponse)
async def kakao_redirect_cancel() -> str:
    return _kakao_redirect_page(
        "KakaoPay payment canceled",
        """
        <h1>카카오페이 결제가 취소되었습니다</h1>
        <p>앱으로 돌아가 다시 결제를 시도해 주세요.</p>
        """,
    )


@router.get("/kakao/redirect/fail", response_class=HTMLResponse)
async def kakao_redirect_fail() -> str:
    return _kakao_redirect_page(
        "KakaoPay payment failed",
        """
        <h1>카카오페이 결제에 실패했습니다</h1>
        <p>앱으로 돌아가 결제 정보를 확인한 뒤 다시 시도해 주세요.</p>
        """,
    )


@router.post("/kakao/ready")
async def ready_kakao_payment(payload: KakaoPayReadyRequest) -> dict[str, Any]:
    try:
        return await KakaoPayClient().ready(payload.model_dump())
    except PaymentProviderError as exc:
        raise handle_provider_error(exc)


@router.post("/kakao/approve")
async def approve_kakao_payment(payload: KakaoPayApproveRequest) -> dict[str, Any]:
    try:
        return await KakaoPayClient().approve(payload.model_dump())
    except PaymentProviderError as exc:
        raise handle_provider_error(exc)


@router.post("/kakao/cancel")
async def cancel_kakao_payment(payload: KakaoPayCancelRequest) -> dict[str, Any]:
    try:
        return await KakaoPayClient().cancel(payload.model_dump())
    except PaymentProviderError as exc:
        raise handle_provider_error(exc)


@router.post("/kakao/subscriptions/ready")
async def ready_kakao_subscription(payload: KakaoPayReadyRequest) -> dict[str, Any]:
    try:
        return await KakaoPayClient().ready(payload.model_dump(), subscription=True)
    except PaymentProviderError as exc:
        raise handle_provider_error(exc)


@router.post("/kakao/subscriptions/approve")
async def approve_kakao_subscription(payload: KakaoPayApproveRequest) -> dict[str, Any]:
    try:
        return await KakaoPayClient().approve(payload.model_dump(), subscription=True)
    except PaymentProviderError as exc:
        raise handle_provider_error(exc)


@router.post("/kakao/subscriptions/charge")
async def charge_kakao_subscription(
    payload: KakaoPaySubscriptionChargeRequest,
) -> dict[str, Any]:
    try:
        return await KakaoPayClient().subscription_charge(payload.model_dump())
    except PaymentProviderError as exc:
        raise handle_provider_error(exc)


@router.post("/kakao/subscriptions/status")
async def get_kakao_subscription_status(
    payload: KakaoPaySubscriptionManageRequest,
) -> dict[str, Any]:
    try:
        return await KakaoPayClient().subscription_status(payload.sid)
    except PaymentProviderError as exc:
        raise handle_provider_error(exc)


@router.post("/kakao/subscriptions/inactive")
async def inactive_kakao_subscription(
    payload: KakaoPaySubscriptionManageRequest,
) -> dict[str, Any]:
    try:
        return await KakaoPayClient().subscription_inactive(payload.sid)
    except PaymentProviderError as exc:
        raise handle_provider_error(exc)
