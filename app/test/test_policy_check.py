from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Policy
from app.services.policy_check import check_policy


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all([
        Policy(name="Auto", min_amount=0, max_amount=60000, approval_level="normal"),
        Policy(name="Manager", min_amount=60000, max_amount=150000,
               approval_level="manager_approval_required"),
        Policy(name="Finance", min_amount=150000, max_amount=None,
               approval_level="finance_review"),
    ])
    db.commit()
    return db


def test_small_amount_is_normal():
    assert check_policy(make_db(), 4006.96)["result"] == "normal"


def test_just_below_limit():
    assert check_policy(make_db(), 59999)["result"] == "normal"


def test_boundary_goes_to_manager():
    assert check_policy(make_db(), 60000)["result"] == "manager_approval_required"


def test_huge_amount_goes_to_finance():
    assert check_policy(make_db(), 240000)["result"] == "finance_review"


def test_missing_amount():
    assert check_policy(make_db(), None)["result"] == "unchecked"