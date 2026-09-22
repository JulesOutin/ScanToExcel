"""Intégration Stripe : session de paiement, portail client, synchronisation d'abonnement."""
import stripe
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Subscription, SubscriptionPlan, SubscriptionStatus

settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

PRICE_TO_PLAN = {
    settings.STRIPE_PRICE_ID_PERSONAL: SubscriptionPlan.PERSONAL,
    settings.STRIPE_PRICE_ID_PRO: SubscriptionPlan.PRO,
}

STRIPE_STATUS_MAP = {
    "active": SubscriptionStatus.ACTIVE,
    "trialing": SubscriptionStatus.ACTIVE,
    "past_due": SubscriptionStatus.PAST_DUE,
    "canceled": SubscriptionStatus.CANCELED,
    "unpaid": SubscriptionStatus.PAST_DUE,
    "incomplete": SubscriptionStatus.INCOMPLETE,
    "incomplete_expired": SubscriptionStatus.CANCELED,
}


def get_or_create_local_subscription(db: Session, user_id: str) -> Subscription:
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).one_or_none()
    if sub is None:
        sub = Subscription(user_id=user_id, plan=SubscriptionPlan.FREE, status=SubscriptionStatus.ACTIVE)
        db.add(sub)
        db.flush()
    return sub


def create_checkout_session(db: Session, user_id: str, user_email: str | None, price_id: str) -> str:
    """Crée une session Stripe Checkout et retourne son URL de redirection."""
    sub = get_or_create_local_subscription(db, user_id)

    customer_id = sub.stripe_customer_id
    if customer_id is None:
        customer = stripe.Customer.create(email=user_email, metadata={"user_id": user_id})
        customer_id = customer.id
        sub.stripe_customer_id = customer_id
        db.commit()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.FRONTEND_URL}/facturation?checkout=success",
        cancel_url=f"{settings.FRONTEND_URL}/facturation?checkout=cancel",
        metadata={"user_id": user_id},
    )
    return session.url


def create_billing_portal_session(db: Session, user_id: str) -> str:
    sub = get_or_create_local_subscription(db, user_id)
    if not sub.stripe_customer_id:
        raise ValueError("Aucun client Stripe pour cet utilisateur — pas encore d'abonnement.")
    portal = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/facturation",
    )
    return portal.url


def sync_subscription_from_stripe_object(db: Session, stripe_sub: dict) -> None:
    """Met à jour la ligne locale `Subscription` à partir d'un objet subscription Stripe (webhook)."""
    customer_id = stripe_sub["customer"]
    local = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).one_or_none()
    if local is None:
        user_id = (stripe_sub.get("metadata") or {}).get("user_id")
        if not user_id:
            return  # abonnement Stripe sans utilisateur local associable — on ignore
        local = Subscription(user_id=user_id, stripe_customer_id=customer_id)
        db.add(local)

    price_id = stripe_sub["items"]["data"][0]["price"]["id"] if stripe_sub.get("items", {}).get("data") else None
    local.plan = PRICE_TO_PLAN.get(price_id, SubscriptionPlan.FREE)
    local.status = STRIPE_STATUS_MAP.get(stripe_sub["status"], SubscriptionStatus.INCOMPLETE)
    local.stripe_subscription_id = stripe_sub["id"]
    if stripe_sub.get("current_period_end"):
        from datetime import datetime, timezone
        local.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"], tz=timezone.utc)

    db.commit()


def downgrade_to_free(db: Session, stripe_customer_id: str) -> None:
    local = db.query(Subscription).filter(Subscription.stripe_customer_id == stripe_customer_id).one_or_none()
    if local:
        local.plan = SubscriptionPlan.FREE
        local.status = SubscriptionStatus.CANCELED
        db.commit()
