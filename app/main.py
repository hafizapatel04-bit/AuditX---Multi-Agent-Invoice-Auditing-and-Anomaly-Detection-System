from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import audit, invoices, policies, vendors

from app.database import init_db
from app.routers import invoices, policies, vendors
from app.seed import seed_policies, seed_vendors

app = FastAPI(title="Invoice Audit")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(invoices.router)
app.include_router(vendors.router)
app.include_router(policies.router)
app.include_router(audit.router)

@app.on_event("startup")
def startup():
    init_db()
    seed_vendors()
    seed_policies()


@app.get("/health")
def health():
    return {"ok": True}