import enum
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VendorStatus(str, enum.Enum):
    approved = "approved"
    blocked = "blocked"
    unknown = "unknown"


class InvoiceStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    needs_review = "needs_review"
    flagged = "flagged"


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    status: Mapped[VendorStatus] = mapped_column(Enum(VendorStatus), default=VendorStatus.approved)
    category: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    invoices: Mapped[list["Invoice"]] = relationship(back_populates="vendor")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"))
    vendor_name: Mapped[str] = mapped_column(String(200), index=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), index=True)
    invoice_date: Mapped[date | None] = mapped_column(Date)
    amount: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    category: Mapped[str | None] = mapped_column(String(100))
    line_items: Mapped[list | None] = mapped_column(JSON)
    file_path: Mapped[str | None] = mapped_column(String(500))
    raw_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vendor: Mapped[Vendor | None] = relationship(back_populates="invoices")
    audit: Mapped["AuditResult | None"] = relationship(back_populates="invoice", uselist=False)


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    min_amount: Mapped[float] = mapped_column(Float, default=0)
    max_amount: Mapped[float | None] = mapped_column(Float)
    approval_level: Mapped[str] = mapped_column(String(50))


class AuditResult(Base):
    __tablename__ = "audit_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), unique=True)
    vendor_check: Mapped[str | None] = mapped_column(String(50))
    policy_check: Mapped[str | None] = mapped_column(String(50))
    duplicate_check: Mapped[str | None] = mapped_column(String(50))
    anomaly_score: Mapped[float | None] = mapped_column(Float)
    final_status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus))
    reasons: Mapped[list | None] = mapped_column(JSON)
    report: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    invoice: Mapped[Invoice] = relationship(back_populates="audit")