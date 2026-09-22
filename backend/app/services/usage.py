"""
Application des limites d'usage du plan gratuit.

Un utilisateur sans abonnement actif (ou en plan "free") est limité à
`FREE_PLAN_PAGES_PER_MONTH` pages traitées par mois civil. Les plans
payants (personal/pro) ne sont pas limités ici — à affiner en Phase 3
selon les paliers réels si besoin.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Subscription, SubscriptionPlan, SubscriptionStatus, UsageCounter

settings = get_settings()


def current_period() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year:04d}-{now.month:02d}"


class UsageLimitExceeded(Exception):
    def __init__(self, used: int, limit: int):
        self.used = used
        self.limit = limit
        super().__init__(f"Limite mensuelle atteinte ({used}/{limit} pages).")


def get_subscription(db: Session, user_id: str) -> Subscription | None:
    return db.query(Subscription).filter(Subscription.user_id == user_id).one_or_none()


def is_unlimited(sub: Subscription | None) -> bool:
    if sub is None:
        return False
    return sub.plan in (SubscriptionPlan.PERSONAL, SubscriptionPlan.PRO) and sub.status == SubscriptionStatus.ACTIVE


def get_or_create_counter(db: Session, user_id: str) -> UsageCounter:
    period = current_period()
    counter = (
        db.query(UsageCounter)
        .filter(UsageCounter.user_id == user_id, UsageCounter.period == period)
        .one_or_none()
    )
    if counter is None:
        counter = UsageCounter(user_id=user_id, period=period, pages_used=0)
        db.add(counter)
        db.flush()
    return counter


def check_and_reserve_pages(db: Session, user_id: str, page_count: int) -> None:
    """
    Vérifie que l'utilisateur peut traiter `page_count` pages de plus ce mois-ci,
    et incrémente le compteur immédiatement (réservation optimiste : évite qu'un
    upload concurrent dépasse la limite entre la vérification et l'écriture).
    Lève UsageLimitExceeded si la limite serait dépassée. Les plans payants actifs
    ne sont pas comptés.
    """
    sub = get_subscription(db, user_id)
    if is_unlimited(sub):
        return

    counter = get_or_create_counter(db, user_id)
    if counter.pages_used + page_count > settings.FREE_PLAN_PAGES_PER_MONTH:
        raise UsageLimitExceeded(counter.pages_used, settings.FREE_PLAN_PAGES_PER_MONTH)

    counter.pages_used += page_count
    db.flush()


def release_pages(db: Session, user_id: str, page_count: int) -> None:
    """En cas d'échec après réservation (ex. type de fichier finalement invalide côté worker), rend les pages."""
    sub = get_subscription(db, user_id)
    if is_unlimited(sub):
        return
    counter = get_or_create_counter(db, user_id)
    counter.pages_used = max(0, counter.pages_used - page_count)
    db.flush()
