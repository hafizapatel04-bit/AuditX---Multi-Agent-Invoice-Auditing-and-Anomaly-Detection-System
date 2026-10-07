from pathlib import Path
from uuid import uuid4
import shutil

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

    # Person A's extraction fills in the real values later
    invoice = Invoice(vendor_name="UNKNOWN", file_path=str(save_path), line_items=[])
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