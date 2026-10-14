from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditResult, Invoice
from app.schemas import AuditOut
from app.services.audit import run_audit

router = APIRouter(tags=["audit"])


@router.post("/analyze-invoice/{invoice_id}", response_model=AuditOut)
def analyze_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return run_audit(db, invoice)


@router.get("/audit/{invoice_id}", response_model=AuditOut)
def get_audit(invoice_id: int, db: Session = Depends(get_db)):
    audit = db.query(AuditResult).filter(AuditResult.invoice_id == invoice_id).first()
    if not audit:
        raise HTTPException(status_code=404,
                            detail="No audit yet. Run POST /analyze-invoice/{id} first")
    return audit