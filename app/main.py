from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import invoices

app = FastAPI(title="Invoice Audit")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for a college project
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(invoices.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"ok": True}