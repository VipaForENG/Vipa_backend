from typing import Any

from fastapi import APIRouter

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
