# KakaoPay Payment Test API

## Environment

Add these values to `backend/.env`.

```env
KAKAO_PAY_SECRET_KEY=...
KAKAO_PAY_CID=TC0ONETIME
KAKAO_PAY_SUBSCRIPTION_CID=TCSEQUENCE
```

`KAKAO_PAY_API_BASE_URL` defaults to `https://open-api.kakaopay.com`.

## Postman

Import these files into Postman.

- `backend/postman/vipa-kakaopay-test.postman_collection.json`
- `backend/postman/vipa-kakaopay-local.postman_environment.json`

Provider secret keys are not stored in Postman. Keep them in `backend/.env`.

## KakaoPay

- `POST /api/v1/payments/kakao/ready`
- `POST /api/v1/payments/kakao/approve`
- `POST /api/v1/payments/kakao/cancel`
- `POST /api/v1/payments/kakao/subscriptions/ready`
- `POST /api/v1/payments/kakao/subscriptions/approve`
- `POST /api/v1/payments/kakao/subscriptions/charge`
- `POST /api/v1/payments/kakao/subscriptions/status`
- `POST /api/v1/payments/kakao/subscriptions/inactive`

### Ready

```json
{
  "partner_order_id": "subscription-order-1",
  "partner_user_id": "user-1",
  "item_name": "VIPA Monthly",
  "quantity": 1,
  "total_amount": 9900,
  "tax_free_amount": 0,
  "approval_url": "http://localhost:8000/api/v1/payments/kakao/redirect/success",
  "cancel_url": "http://localhost:8000/api/v1/payments/kakao/redirect/cancel",
  "fail_url": "http://localhost:8000/api/v1/payments/kakao/redirect/fail"
}
```

### Approve

```json
{
  "tid": "T1234567890123456789",
  "partner_order_id": "subscription-order-1",
  "partner_user_id": "user-1",
  "pg_token": "pg-token-from-redirect"
}
```

### Cancel

```json
{
  "tid": "T1234567890123456789",
  "cancel_amount": 9900,
  "cancel_tax_free_amount": 0
}
```

### Subscription charge

```json
{
  "sid": "S1234567890987654321",
  "partner_order_id": "subscription-charge-1",
  "partner_user_id": "user-1",
  "item_name": "VIPA Monthly",
  "quantity": 1,
  "total_amount": 9900,
  "tax_free_amount": 0
}
```
