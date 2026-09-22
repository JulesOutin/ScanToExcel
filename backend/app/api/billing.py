"""Routes Stripe : création de session de paiement, portail client, webhook."""
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import CurrentUser, get_current_user
from app.models.document import Subscription
from app.services import billing
from app.services import usage as usage_service

router = APIRouter(prefix="/billing", tags=["billing"])
settings = get_settings()


class CheckoutIn(BaseModel):
    plan: str  # "personal" | "pro"


class CheckoutOut(BaseModel):
    url: str


class SubscriptionOut(BaseModel):
    plan: str
    status: str

    model_config = {"from_attributes": True}


class UsageOut(BaseModel):
    period: str
    pages_used: int
    limit: int
    unlimited: bool


PLAN_TO_PRICE = {
    "personal": settings.STRIPE_PRICE_ID_PERSONAL,
    "pro": settings.STRIPE_PRICE_ID_PRO,
}


@router.get("/usage", response_model=UsageOut)
def get_usage(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    local_sub = usage_service.get_subscription(db, user.id)
    counter = usage_service.get_or_create_counter(db, user.id)
    db.commit()
    return UsageOut(
        period=counter.period,
        pages_used=counter.pages_used,
        limit=settings.FREE_PLAN_PAGES_PER_MONTH,
        unlimited=usage_service.is_unlimited(local_sub),
    )


@router.get("/subscription", response_model=SubscriptionOut)
def get_my_subscription(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    sub = billing.get_or_create_local_subscription(db, user.id)
    db.commit()
    return sub


@router.post("/checkout", response_model=CheckoutOut)
def create_checkout(
    payload: CheckoutIn,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    price_id = PLAN_TO_PRICE.get(payload.plan)
    if not price_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Plan inconnu.")
    url = billing.create_checkout_session(db, user.id, user.email, price_id)
    return {"url": url}


@router.post("/portal", response_model=CheckoutOut)
def create_portal(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    try:
        url = billing.create_billing_portal_session(db, user.id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return {"url": url}


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Webhook invalide.") from exc

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        billing.sync_subscription_from_stripe_object(db, data)
    elif event_type == "customer.subscription.deleted":
        billing.downgrade_to_free(db, data["customer"])
    elif event_type == "checkout.session.completed" and data.get("mode") == "subscription":
        # La subscription elle-même arrive via customer.subscription.created juste après ;
        # on ne fait rien ici de plus que logger côté Stripe dashboard.
        pass

    return {"received": True}
