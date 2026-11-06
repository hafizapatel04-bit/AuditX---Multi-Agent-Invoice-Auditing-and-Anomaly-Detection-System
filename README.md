AuditX
Intelligent Multi-Agent Invoice Auditing & Anomaly Detection System

Automating invoice verification. Detecting financial anomalies. Simplifying financial control.

AuditX is an AI-powered invoice auditing system that automates invoice data extraction, validation, duplicate detection, approval-policy verification, and anomaly detection.

Built using Python, FastAPI, local LLMs, and machine learning, AuditX processes PDF and image-based invoices through a multi-agent auditing pipeline and generates an explainable audit verdict with a detailed report.

01. Project Overview

AuditX transforms manual invoice verification into an automated, intelligent auditing workflow.

The system extracts invoice information using OCR and a locally hosted LLM, stores the extracted data, and evaluates each invoice against six independent audit checks.

Every invoice receives one of three final verdicts:

Verdict	Description
🟢 Approved	All audit checks have passed successfully.
🟡 Needs Review	Only the approval-policy check requires additional authorization.
🔴 Flagged	One or more other audit checks have identified an issue requiring manual review.
System Architecture
mermaid
flowchart TD
    U["Invoice Upload (PDF / Image)"]
    E["OCR + Local LLM Extraction"]
    S["FastAPI + SQLite Storage"]

    subgraph A["Multi-Agent Audit Engine"]
        V["Vendor Verification"]
        F["Required Fields"]
        T["Total Validation"]
        D["Duplicate Detection"]
        P["Approval Policy"]
        N["Anomaly Detection"]
    end

    R["Final Audit Verdict"]
    UI["Dashboard & Audit Report"]

    U --> E --> S --> A
    V --> R
    F --> R
    T --> R
    D --> R
    P --> R
    N --> R
    R --> UI

    style U fill:#172554,color:#fff
    style E fill:#1e3a8a,color:#fff
    style S fill:#334155,color:#fff
    style R fill:#14532d,color:#fff
    style UI fill:#312e81,color:#fff

Final Verdict Logic
Approved: All six audit checks pass.
Needs Review: The approval-policy check is the only flagged check.
Flagged: Any other audit check fails or identifies a potential issue.
02. Key Features
Feature	Description
Intelligent Extraction	Extracts invoice information using OCR and a local LLM.
Vendor Verification	Validates vendors using normalized names and fuzzy matching.
Required Field Validation	Checks essential invoice information for completeness.
Financial Validation	Verifies subtotal, tax, and invoice total consistency.
Duplicate Detection	Identifies exact and potential duplicate invoices.
Approval Policy Engine	Determines the required approval level based on invoice value.
ML-Based Anomaly Detection	Uses Isolation Forest and z-score analysis to identify unusual invoices.
Explainable Audit Reports	Provides audit verdicts, reasons, and readable reports.
Interactive Dashboard	Displays invoice information and audit results.
Local AI Processing	Runs the LLM locally through Ollama.
03. Technology Stack
Component	Technologies
Backend	Python, FastAPI, Uvicorn
Database	SQLite, SQLAlchemy 2.0
Data Validation	Pydantic
Document Processing	PyMuPDF, Tesseract OCR
Local LLM	Ollama – Llama 3.2 (3B)
Machine Learning	Scikit-learn, Isolation Forest, Z-score
Frontend	HTML5, CSS3, JavaScript
Testing	Pytest
Deployment	Docker, Docker Compose
04. Multi-Agent Audit Checks

AuditX evaluates every extracted invoice using six specialized validation modules.

1. Vendor Verification
Normalizes vendor names by handling capitalization, punctuation, and common company suffixes.
Uses fuzzy matching with an 85% similarity threshold.
Identifies vendors that are not present in the approved vendor database.
2. Required Field Validation

Verifies that the following information is available:

Vendor name
Invoice number
Invoice date
Invoice amount
3. Total Validation

Checks whether:

Subtotal + Tax = Invoice Total

A tolerance of ₹1.00 is allowed. Invoices containing shipping charges or discounts may require manual review because these are not currently included in the calculation.

4. Duplicate Detection

Two levels of duplicate detection are supported:

Exact Duplicate: Same vendor and invoice number, ignoring case and dashes.
Potential Duplicate: Same vendor and invoice amount with invoice dates within seven days.

Only previously recorded invoices are considered during comparison.

5. Approval Policy Verification

Invoice amounts determine the required approval level.

Invoice Amount	Approval Requirement
Below ₹60,000	Normal approval
₹60,000 – ₹149,999.99	Manager approval
₹150,000 and above	Finance review

Approval thresholds are stored in the database's policies table.

6. Anomaly Detection

Uses machine learning and statistical analysis to identify unusual invoice amounts.

Isolation Forest for detecting unusual patterns.
Z-score analysis for identifying deviations from category averages.
Currently processes INR invoices with an assigned category because the historical training data is INR-based.
05. Team & Responsibilities
Responsibility	Team Member	Project Directory
Document Intake & AI Extraction	To be assigned	extraction/
Backend, Database & Business Logic	Hafiza	app/, scripts/
Anomaly Detection, Reporting & Frontend	To be assigned	anomaly/, frontend/
06. Project Structure
text
AuditX/
│
├── app/
│   ├── routers/
│   ├── services/
│   ├── models/
│   ├── schemas/
│   ├── seed data
│   └── test/
│
├── extraction/
│   └── OCR and LLM extraction modules
│
├── anomaly/
│   ├── train_model.py
│   ├── anomaly detection
│   └── report generation
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── sample_data/
│   ├── sample invoices
│   ├── vendor list
│   ├── ground truth
│   └── historical data
│
├── scripts/
│   ├── run_ground_truth.py
│   └── report_ground_truth.py
│
├── requirements.txt
├── docker-compose.yml
└── README.md

07. Installation & Setup
Prerequisites

Install the following before running AuditX:

Python 3.12 or newer
Ollama
Tesseract OCR (required for scanned PDFs)
Git
Docker Desktop (optional, for containerized deployment)
Step 1 — Clone the Repository
powershell
git clone https://github.com/hafizapatel04-bit/AuditX---Multi-Agent-Invoice-Auditing-and-Anomaly-Detection-System.git AuditX

cd AuditX

Step 2 — Create a Virtual Environment
powershell
python -m venv venv

venv\Scripts\activate

Step 3 — Install Dependencies
powershell
pip install -r requirements.txt

Step 4 — Download the Local LLM

Install the required model using Ollama:

powershell
ollama pull llama3.2:3b

Step 5 — Train the Anomaly Detection Model

Run this once per machine because the trained model files are not included in Git.

powershell
python -m anomaly.train_model

Step 6 — Start the Backend

From the project root:

powershell
python -m uvicorn app.main:app


The API will be available at:

Application API: http://127.0.0.1:8000
Interactive API Documentation: http://127.0.0.1:8000/docs
Step 7 — Launch the Frontend

Open frontend/index.html using the VS Code Live Server extension.

The AuditX dashboard will be accessible through your local browser.

08. Docker Deployment

AuditX also supports containerized deployment using Docker Compose.

Build and Start Services
powershell
docker compose up -d --build

Download the LLM
powershell
docker compose exec ollama ollama pull llama3.2:3b

Access the Application

Open:

http://localhost:8000

The Docker setup runs the API and Ollama in separate containers.

Persistent storage:

Database
Uploaded invoice files
Local LLM model

These are maintained through Docker volumes and survive container restarts.

To inspect backend logs:

powershell
docker compose logs api


System requirements: Approximately 8 GB of RAM is recommended for running the local model.

Security note: The API currently does not implement authentication. Do not expose it to public networks without adding appropriate security controls.

09. API Documentation

AuditX provides REST API endpoints for invoice processing, auditing, vendor verification, and approval-policy management.

Method	Endpoint	Functionality
GET	/health	Check server health
POST	/upload-invoice	Upload, extract, and audit an invoice
GET	/invoices	Retrieve all invoices
GET	/invoice/{id}	Retrieve a specific invoice
GET	/invoice/{id}/duplicate-check	Execute duplicate detection
POST	/analyze-invoice/{id}	Re-run invoice auditing
GET	/audit/{id}	Retrieve audit results and report
GET	/vendors	Retrieve approved vendors
GET	/vendors/verify?name=...	Verify a vendor
GET	/policies	Retrieve approval policies
GET	/policies/check?amount=...	Determine approval requirements

Additional API functionality:

Append ?llm=true to /analyze-invoice/{id} to generate an AI-written summary.
If extraction fails, the invoice is stored with vendor UNKNOWN, status needs_review, and the failure reason in notes.
If database storage fails, the API returns HTTP 500 with the underlying error.
10. Testing & Validation

AuditX includes automated tests and a ground-truth evaluation workflow.

Run Unit Tests
powershell
python -m pytest app/test

End-to-End Evaluation

The project includes 16 labelled sample invoices to evaluate the accuracy of the final audit verdicts.

Step 1 — Start with a fresh database

powershell
del invoice_audit.db

python -m uvicorn app.main:app


Step 2 — Open a second terminal and execute

powershell
python scripts/run_ground_truth.py


Step 3 — Generate a report from existing results

powershell
python scripts/report_ground_truth.py

Ground-Truth Evaluation Results
Metric	Result
Total Sample Invoices	16
Expected Verdicts	16
Matching Verdicts	To be updated
Overall Accuracy	To be calculated

Latest result: FILL IN — X of 16 verdicts match the expected results.

11. Known Limitations

Although AuditX automates several important auditing tasks, some limitations remain:

OCR Accuracy: Poor-quality scanned invoices can produce incorrect extracted values. Some errors are flagged, but incorrect values may occasionally pass validation. For example, inv_11_poor.pdf.
Anomaly Detection: Invoices slightly above their category average may occasionally be flagged as unusual.
Currency Support: Anomaly and policy checks are currently designed around INR-based historical data. Other currencies require manual review.
Local LLM Performance: Invoice extraction can be slow on laptops with CPU-only processing.
Database Scalability: SQLite and local file storage are suitable for demonstrations and smaller workloads, but not designed for high-concurrency production environments.
Authentication: The current API does not include user authentication or role-based access control.
12. Future Enhancements

The following improvements are planned to make AuditX more robust and production-ready.

Priority	Enhancement	Objective
High	OCR Confidence Scoring	Improve extraction reliability and flag uncertain values.
High	User Authentication	Secure API access and introduce role-based permissions.
High	PostgreSQL Integration	Support scalable database operations.
Medium	Category-Based Approval Limits	Enable configurable approval thresholds by invoice category.
Medium	Advanced Anomaly Detection	Reduce false positives through improved historical analysis.
Medium	Multi-Currency Support	Extend auditing beyond INR invoices.
Medium	Improved Audit Dashboard	Enhance visualization and financial reporting.
13. Important Database Note

After pulling updates that modify the database schema:

Stop the running backend.
Delete invoice_audit.db.
Restart the application.

Vendors and approval policies are automatically seeded when the application initializes.

Note: Deleting the database removes existing invoice records. Back up any data you need before doing so.

14. Why AuditX?

Traditional invoice auditing often involves repetitive manual verification, making the process time-consuming and susceptible to human error.

AuditX combines document intelligence, rule-based validation, and machine learning to create a unified auditing workflow.

Its key objectives are to:

Reduce manual invoice verification effort.
Improve financial data consistency.
Identify duplicate and suspicious transactions.
Enforce predefined approval policies.
Provide transparent, explainable audit decisions.
Keep AI-based extraction locally hosted.
Project Information

Project Name: AuditX – Multi-Agent Invoice Auditing and Anomaly Detection System

Backend: Python + FastAPI

AI Engine: Ollama + Llama 3.2

Machine Learning: Scikit-learn

Database: SQLite

Deployment: Docker Compose

Repository: GitHub – AuditX

AuditX — Making invoice auditing smarter, faster, and more transparent.
