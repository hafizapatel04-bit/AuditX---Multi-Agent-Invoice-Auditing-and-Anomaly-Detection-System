from pathlib import Path
from uuid import uuid4
import shutil
import logging

from app.models import Invoice, InvoiceStatus
from extraction.extractor import extract_invoice

log = logging.getLogger(__name__)


from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Invoice
from app.schemas import InvoiceOut

router = APIRouter(tags=["invoices"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload-invoice", response_model=InvoiceOut)
def upload_invoice(file: UploadFile, db: Session = Depends(get_db)):
    if not file.filename.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Only PDF or image files allowed")

    save_path = UPLOAD_DIR / f"{uuid4().hex}_{file.filename}"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        data = extract_invoice(str(save_path))
        invoice = Invoice(
            vendor_name=data.vendor_name,
            invoice_number=data.invoice_number,
            invoice_date=data.invoice_date,
            due_date=data.due_date,
            subtotal=data.subtotal,
            tax_amount=data.tax_amount,
            amount=data.amount,
            currency=data.currency,
            category=data.category,
            line_items=[li.model_dump() for li in data.line_items],
            file_path=str(save_path),
        )
    except Exception as e:  # ValueError = bad extraction; others = Ollama down or timeout
        log.warning("Extraction failed for %s: %s", file.filename, e)
        invoice = Invoice(
            vendor_name="UNKNOWN",
            line_items=[],
            file_path=str(save_path),
            status=InvoiceStatus.needs_review,
        )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).order_by(Invoice.id.desc()).all()


@router.get("/invoice/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.post("/upload-invoice", response_model=InvoiceOut)
def upload_invoice(file: UploadFile, db: Session = Depends(get_db)):
    if not file.filename.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Only PDF or image files allowed")

    save_path = UPLOAD_DIR / f"{uuid4().hex}_{Path(file.filename).name}"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        data = extract_invoice(str(save_path))
        invoice = Invoice(
            vendor_name=data.vendor_name,
            invoice_number=data.invoice_number,
            invoice_date=data.invoice_date,
            due_date=data.due_date,
            subtotal=data.subtotal,
            tax_amount=data.tax_amount,
            amount=data.amount,
            currency=data.currency,
            category=data.category,
            line_items=[li.model_dump() for li in data.line_items],
            file_path=str(save_path),
        )
    except Exception as e:  # ValueError = bad extraction; others = Ollama down or timeout
        log.warning("Extraction failed for %s: %s", file.filename, e)
        invoice = Invoice(
            vendor_name="UNKNOWN",
            line_items=[],
            file_path=str(save_path),
            status=InvoiceStatus.needs_review,
        )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).order_by(Invoice.id.desc()).all()


@router.get("/invoice/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice