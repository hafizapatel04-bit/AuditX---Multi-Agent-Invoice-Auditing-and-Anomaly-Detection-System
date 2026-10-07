from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models import InvoiceStatus, VendorStatus


class LineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float | None = None
    total: float | None = None


class ExtractedInvoice(BaseModel):
    vendor_name: str
    invoice_number: str | None = None
    invoice_date: date | None = None
    amount: float | None = None
    currency: str = "INR"
    category: str | None = None
    line_items: list[LineItem] = []


class InvoiceOut(ExtractedInvoice):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: InvoiceStatus
    created_at: datetime


class VendorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    status: VendorStatus
    category: str | None = None


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    invoice_id: int
    vendor_check: str | None
    policy_check: str | None
    duplicate_check: str | None
    anomaly_score: float | None
    final_status: InvoiceStatus
    reasons: list[str] | None
    report: str | None