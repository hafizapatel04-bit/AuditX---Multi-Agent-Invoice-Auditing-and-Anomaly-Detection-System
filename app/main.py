from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import invoices
from app.seed import seed_vendors


app = FastAPI(title="Invoice Audit")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for a college project
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(invoices.router)
app.include_router(vendors.router)


@app.on_event("startup")
def startup():
    init_db()
    seed_vendors()


@app.get("/health")
def health():
    return {"ok": True}