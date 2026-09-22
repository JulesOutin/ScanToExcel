"""Tests de l'application des limites du plan gratuit, sans dépendre d'une vraie base."""
from unittest.mock import MagicMock

import pytest

from app.models.document import Subscription, SubscriptionPlan, SubscriptionStatus, UsageCounter
from app.services import usage


def make_db(counter=None, subscription=None):
    db = MagicMock()

    def query_side_effect(model):
        q = MagicMock()
        if model is UsageCounter:
            q.filter.return_value.one_or_none.return_value = counter
        elif model is Subscription:
            q.filter.return_value.one_or_none.return_value = subscription
        return q

    db.query.side_effect = query_side_effect
    return db


def test_new_user_can_upload_within_limit():
    db = make_db(counter=None, subscription=None)
    usage.check_and_reserve_pages(db, "user-1", 3)
    added = db.add.call_args[0][0]
    assert isinstance(added, UsageCounter)
    assert added.pages_used == 3


def test_upload_exceeding_free_limit_raises():
    existing = UsageCounter(
        user_id="user-1",
        period=usage.current_period(),
        pages_used=usage.settings.FREE_PLAN_PAGES_PER_MONTH - 1,
    )
    db = make_db(counter=existing, subscription=None)
    with pytest.raises(usage.UsageLimitExceeded):
        usage.check_and_reserve_pages(db, "user-1", 5)
    # le compteur n'a pas dû être incrémenté puisque la réservation a échoué
    assert existing.pages_used == usage.settings.FREE_PLAN_PAGES_PER_MONTH - 1


def test_active_paid_plan_is_unlimited():
    sub = Subscription(user_id="user-1", plan=SubscriptionPlan.PRO, status=SubscriptionStatus.ACTIVE)
    db = make_db(counter=None, subscription=sub)
    usage.check_and_reserve_pages(db, "user-1", 10_000)
    db.add.assert_not_called()


def test_canceled_paid_plan_is_not_unlimited():
    sub = Subscription(user_id="user-1", plan=SubscriptionPlan.PRO, status=SubscriptionStatus.CANCELED)
    assert usage.is_unlimited(sub) is False


def test_release_pages_floors_at_zero():
    existing = UsageCounter(user_id="user-1", period=usage.current_period(), pages_used=2)
    db = make_db(counter=existing, subscription=None)
    usage.release_pages(db, "user-1", 5)
    assert existing.pages_used == 0


def test_crossing_80_percent_returns_true_once():
    # limite par défaut = 20 pages/mois → le seuil (80 %) est 16 pages
    existing = UsageCounter(user_id="user-1", period=usage.current_period(), pages_used=14, near_limit_notified=False)
    db = make_db(counter=existing, subscription=None)

    just_crossed = usage.check_and_reserve_pages(db, "user-1", 3, user_email="a@example.com")  # -> 17 pages

    assert just_crossed is True
    assert existing.near_limit_notified is True
    assert existing.user_email == "a@example.com"


def test_already_notified_does_not_trigger_again():
    existing = UsageCounter(user_id="user-1", period=usage.current_period(), pages_used=17, near_limit_notified=True)
    db = make_db(counter=existing, subscription=None)

    just_crossed = usage.check_and_reserve_pages(db, "user-1", 1)

    assert just_crossed is False


def test_staying_under_threshold_does_not_trigger():
    existing = UsageCounter(user_id="user-1", period=usage.current_period(), pages_used=2, near_limit_notified=False)
    db = make_db(counter=existing, subscription=None)

    just_crossed = usage.check_and_reserve_pages(db, "user-1", 1)  # -> 3 pages, largement sous 80 %

    assert just_crossed is False
