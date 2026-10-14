from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Policy


def check_policy(db: Session, amount: float | None, category: str | None = None) -> dict:
    if amount is None:
        return {"result": "unchecked", "reason": "Amount missing, cannot apply approval policy"}

    rules = (
        db.query(Policy)
        .filter(Policy.min_amount <= amount)
        .filter(or_(Policy.max_amount.is_(None), amount < Policy.max_amount))
        .all()
    )
    # a category-specific rule beats a general one
    rule = (next((r for r in rules if r.category == category), None)
            or next((r for r in rules if r.category is None), None))

    if rule is None:
        return {"result": "unchecked", "reason": "No policy covers this amount"}

    return {
        "result": rule.approval_level,
        "reason": f"{rule.name}: amount {amount:,.2f} requires '{rule.approval_level}'",
    }