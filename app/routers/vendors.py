from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Vendor
from app.schemas import VendorOut
from app.services.vendor_check import verify_vendor

router = APIRouter(tags=["vendors"])


@router.get("/vendors", response_model=list[VendorOut])
def list_vendors(db: Session = Depends(get_db)):
    return db.query(Vendor).all()


@router.get("/vendors/verify")
def verify(name: str, db: Session = Depends(get_db)):
    return verify_vendor(db, name)