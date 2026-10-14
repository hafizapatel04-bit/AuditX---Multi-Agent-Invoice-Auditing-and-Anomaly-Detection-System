from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Policy
from app.services.policy_check import check_policy

router = APIRouter(tags=["policies"])


@router.get("/policies")
def list_policies(db: Session = Depends(get_db)):
    return [
        {"name": p.name, "category": p.category, "min_amount": p.min_amount,
         "max_amount": p.max_amount, "approval_level": p.approval_level}
        for p in db.query(Policy).order_by(Policy.min_amount).all()
    ]


@router.get("/policies/check")
def policy_check(amount: float, category: str | None = None, db: Session = Depends(get_db)):
    return check_policy(db, amount, category)