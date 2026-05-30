from pydantic import BaseModel, Field


class KakaoPayReadyRequest(BaseModel):
    partner_order_id: str
    partner_user_id: str
    item_name: str
    quantity: int = Field(default=1, gt=0)
    total_amount: int = Field(gt=0)
    tax_free_amount: int = Field(default=0, ge=0)
    vat_amount: int | None = Field(default=None, ge=0)
    approval_url: str
    cancel_url: str
    fail_url: str
    item_code: str | None = None


class KakaoPayApproveRequest(BaseModel):
    tid: str
    partner_order_id: str
    partner_user_id: str
    pg_token: str


class KakaoPayCancelRequest(BaseModel):
    tid: str
    cancel_amount: int = Field(gt=0)
    cancel_tax_free_amount: int = Field(default=0, ge=0)
    cancel_vat_amount: int | None = Field(default=None, ge=0)


class KakaoPaySubscriptionChargeRequest(BaseModel):
    sid: str
    partner_order_id: str
    partner_user_id: str
    item_name: str
    quantity: int = Field(default=1, gt=0)
    total_amount: int = Field(gt=0)
    tax_free_amount: int = Field(default=0, ge=0)
    vat_amount: int | None = Field(default=None, ge=0)


class KakaoPaySubscriptionManageRequest(BaseModel):
    sid: str
