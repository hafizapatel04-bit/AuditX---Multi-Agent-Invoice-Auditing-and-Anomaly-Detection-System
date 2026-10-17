from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditResult, Invoice
from app.schemas import AuditOut
from app.services.audit import run_audit

router = APIRouter(tags=["audit"])


@router.post("/analyze-invoice/{invoice_id}", response_model=AuditOut)
def analyze_invoice(invoice_id: int, llm: bool = False, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return run_audit(db, invoice, use_llm=llm)

@router.get("/audit/{invoice_id}", response_model=AuditOut)
def get_audit(invoice_id: int, db: Session = Depends(get_db)):
    audit = db.query(AuditResult).filter(AuditResult.invoice_id == invoice_id).first()
    if not audit:
        raise HTTPException(status_code=404,
                            detail="No audit yet. Run POST /analyze-invoice/{id} first")
    return audit

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    by_status = {s.value: 0 for s in InvoiceStatus}
    for i in invoices:
        by_status[i.status.value] += 1
    return {
        "total_invoices": len(invoices),
        "total_amount": round(sum(i.amount or 0 for i in invoices), 2),
        "flagged_amount": round(sum(i.amount or 0 for i in invoices
                                    if i.status == InvoiceStatus.flagged), 2),
        "by_status": by_status,
    }