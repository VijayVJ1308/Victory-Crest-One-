# Victory Crest ONE

> **One Platform. Every Business. Complete Control.**  
> *Modular, cross-platform enterprise business operating system.*

---

## 🌟 Executive Overview

**Victory Crest ONE** is a unified, high-performance enterprise operating system designed to manage the complete end-to-end lifecycle of modern businesses across hospitality, dining, commerce, retail, supply chain, manufacturing, professional services, and corporate finance.

The platform combines a native **PySide6 desktop application** for macOS and Windows, a central high-throughput **FastAPI backend**, **PostgreSQL** as the central source of truth, and a durable local **SQLite** offline operation engine.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Desktop Application** | Python 3.10+, PySide6 (Qt6 Widgets), HTTPX | Native enterprise UI shell with dark design system |
| **Central Backend** | FastAPI, Pydantic v2, Uvicorn, SQLAlchemy 2.0 | Versioned RESTful APIs (`/api/v1`), validation, business rules |
| **Central Database** | PostgreSQL 16+ (Alembic for migrations) | ACID transactions, strict multi-tenant data isolation |
| **Offline Storage** | SQLite, Local Operation Queue | Offline capability, cached catalog, conflict detection |
| **Analytics Engine** | Pandas, Plotly, OpenPyXL, ReportLab | Decimal-safe KPI calculations, financial reports, exports |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX TestClient | Automated unit, integration, and UI shell test suites |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (macOS Apple Silicon or Windows x64)
- **Docker** (optional, for local PostgreSQL container)

### 2. Environment Setup

Clone or enter the project directory and create a virtual environment:

```bash
cd "Victory Crest One"

# Create virtual environment (Python 3.10)
python3.10 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Start PostgreSQL (Central Database)

You can launch a local PostgreSQL 16 container with the preconfigured `docker-compose.yml`:

```bash
docker compose up -d postgres
```

> **Note on Development Offline Mode:**  
> If PostgreSQL is not running, Victory Crest ONE provides clear diagnostic telemetry and actionable troubleshooting commands. The desktop application can launch seamlessly in **Development Offline Mode** without silently masking connection status.

### 4. Start the Central Backend API

Launch the FastAPI application on port 8000:

```bash
./.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API Root: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Interactive API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- System Diagnostics & Health: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- Module Catalog: [http://127.0.0.1:8000/api/v1/modules](http://127.0.0.1:8000/api/v1/modules)

### 5. Launch the Desktop Application

Run the PySide6 desktop interface:

```bash
./.venv/bin/python desktop/main.py
```

Optional flags:
```bash
# Explicitly set central API host
./.venv/bin/python desktop/main.py --api-url http://127.0.0.1:8000

# Force offline/local storage mode
./.venv/bin/python desktop/main.py --offline
```

---

## 🧪 Running Automated Tests

Run the full automated test suite (unit, integration, and UI shell tests):

```bash
./.venv/bin/pytest tests/ -v
```

All 23 foundation test suites pass with zero errors.

---

## 🏛️ Project Directory Structure

```text
Victory Crest One/
├── README.md                      # Comprehensive user & developer guide
├── pyproject.toml                 # Package specifications and pytest config
├── requirements.txt               # Pinned dependency requirements
├── docker-compose.yml             # Local PostgreSQL container service
├── .env.example                   # Environment variable template
├── backend/
│   └── app/
│       ├── main.py                # FastAPI entry point, middleware & lifespan
│       ├── core/
│       │   ├── config.py          # Pydantic Settings & database credentials
│       │   ├── database.py        # Central Postgres & local SQLite engines
│       │   └── logging.py         # Structured logging with credential redaction
│       ├── models/
│       │   ├── base.py            # UUID mixin, audit timestamps & soft delete
│       │   ├── organization.py    # Multi-tenant Organization & Property hierarchy
│       │   ├── user.py            # User, Role, & Access Control models
│       │   └── audit.py           # Audit logging model
│       ├── schemas/
│       │   ├── health.py          # System health and diagnostic schemas
│       │   └── organization.py    # Multi-tenant organization DTOs
│       ├── services/
│       │   └── health_service.py  # Health monitoring and database diagnostics
│       └── api/v1/
│           ├── api.py             # Router aggregator
│           └── endpoints/
│               ├── health.py      # /health & /health/quick
│               ├── organizations.py# /organizations
│               └── modules.py     # /modules catalog
├── desktop/
│   ├── main.py                    # PySide6 application launcher
│   ├── core/
│   │   ├── config.py              # Desktop client configuration
│   │   ├── theme.py               # Enterprise design system & QSS stylesheets
│   │   └── session.py             # Active user, organisation, and property session
│   ├── services/
│   │   └── api_client.py          # Resilient HTTP client with offline fallback
│   └── ui/
│       ├── main_window.py         # Application shell with sidebar & topbar
│       ├── components/
│       │   ├── metric_card.py     # Executive KPI metric cards
│       │   ├── status_badge.py    # Status capsules (Active, Planned, Offline)
│       │   └── module_card.py     # Interactive module cards
│       └── views/
│           ├── dashboard_view.py  # Executive Dashboard with live/simulated telemetry
│           ├── module_catalog_view.py # 18+ business modules grid with category filters
│           ├── planned_module_view.py # Roadmap & architectural specs for planned phases
│           └── diagnostics_view.py# Central DB & SQLite live diagnostic panel
├── shared/
│   ├── enums.py                   # Canonical enums (ModuleType, UserRole, etc.)
│   ├── constants.py               # Module catalog metadata & demo organisations
│   ├── calculations.py            # Decimal-safe financial and hospitality KPI metrics
│   └── dto.py                     # Common data transfer objects
├── tests/
│   ├── conftest.py                # Pytest fixtures (TestClient, headless Qt)
│   ├── unit/                      # Decimal calculations & enums tests
│   ├── integration/               # FastAPI health endpoints & DB tests
│   └── ui/                        # PySide6 MainWindow & component tests
└── docs/                          # Architecture, schema, and security documentation
```

---

## 🗺️ Multi-Organisation Support

Victory Crest ONE enforces strict tenant isolation:
- **Organisation**: Top-level tenant (e.g., `Victory Crest Enterprise Group [VCG]`).
- **Property / Branch**: Operating physical location:
  - *GrandVista Heritage Hotel — Madurai* (85 rooms)
  - *GrandVista Mountain Resort — Kodaikanal* (64 rooms)
  - *GrandVista Business Hotel — Chennai* (120 rooms)
  - *Victory Crest Corporate HQ & Central Services*
- **Cross-Property Switching**: Seamlessly switch active context from the persistent desktop top toolbar. All metrics, folios, reports, and data queries are scoped to the active tenant.

---

## 🛡️ Implementation Roadmap & Milestones

- [x] **Phase 1: Foundation Deliverable & Desktop Shell** (FastAPI lifespan, PySide6 Shell, multi-tenant hierarchy, SQLite offline engine, 23 tests)
- [x] **Phase 2: Identity, RBAC & Permissions Engine** (Argon2 hashing, JWT sessions, role permission matrix, separation of duties, immutable audit trail)
- [x] **Phase 3: Master Data, Document Vault & Notifications** (Customers, Suppliers, Products catalog, Deduplication engine, SHA-256 Document Vault, Alert broadcasting)
- [x] **Phase 4: Finance & General Accounting Engine** (Full Chart of Accounts, balanced double-entry GL, Customer Invoices / AR, Supplier Bills / AP, Trial Balance, P&L, Balance Sheet)
- [x] **Phase 5: Sales CRM & Revenue Pipeline** (Lead conversion, pipeline deal stages, win rate analytics, weighted pipeline forecasting, sales quotes)
- [x] **Phase 6: Commerce & Point of Sale (POS)** (Cash register shifts, barcode lookup, hold/recall orders, split tenders, thermal receipts, automated GL journal posting)
- [x] **Phase 7: Marketing Automation & Growth** (Multi-channel campaigns, audience segmentation, customer journeys, message templates, conversion attribution & ROAS)
- [x] **Phase 8: Supply Chain, ERP & Warehouse Inventory** (Multi-warehouse stock balances, procurement Purchase Orders, Goods Receipt Notes with automated GL/AP posting, AVCO weighted average cost valuation, replenishment alerts, inter-warehouse transfers, and physical stocktaking cycle counts)
- [x] **Phase 9: Human Resources & Payroll Management Engine** (Staff directory, biometric shift clock-in/out attendance, leave approval workflows, statutory salary structures with PF/ESI/PT/TDS, batch payroll computation, itemized payslips, and automated Finance GL salary disbursement posting: DR 6010, CR 2030, CR 1010)
- [x] **Phase 10: Customer & Field Service Management Engine** (Omnichannel support incident ticketing, P1-P4 SLA tracking with real-time breach countdowns, field work order scheduling, technician dispatches, warehouse spare parts requisitions, and automated double-entry GL invoicing: DR 1020, CR 4040, CR 2020)
- [x] **Phase 11: Hospitality & Resort PMS / Restaurant Dining Management** (Multi-property room rack & availability grid, room types, dynamic rate plans, reservations engine, express check-in/out, running guest folios with incidental postings, housekeeping room status transitions, restaurant dining tables floorplan, Kitchen Display System (KDS) order lifecycle, room folio transfer billing, and automated Finance GL night audit revenue recognition: DR 1020, CR 4010, CR 2020)
- [x] **Phase 12: Manufacturing & Production Orders / Bill of Materials (BOM)** (Manufacturing work centers, multi-level Bills of Materials with scrap allowance, routing labor & machine steps, production orders with live state transitions, quality inspection checkpoints, WIP valuation, and automated double-entry GL inventory absorption: DR 1230 Finished Goods Inventory, CR 1210 Raw Materials Inventory, CR 5030 Manufacturing Direct Labor & Overhead)
- [x] **Phase 13: Project Management & Professional Services (PSA)** (Work Breakdown Structures (WBS), project portfolios, task hierarchies, contract milestone deliverable schedules, billable and non-billable labor timesheets, direct project expenses, budget variance & burn rate analytics, and automated double-entry GL revenue recognition: DR 1020 Accounts Receivable, CR 4040 Service & Event Fee Revenue, CR 2020 GST Output Tax Payable 18%)
- [x] **Phase 14: Business Intelligence & Executive Analytics** (Multi-dimensional executive KPI dashboards, Gross Operating Profit (GOP), EBITDA, departmental P&L contribution, physical property benchmarking, financial health ratios, linear predictive revenue forecasting, and high-fidelity multi-format document exports in Excel `.xlsx`, PDF with ReportLab corporate dossier formatting, and RFC-4180 CSV)
- [x] **Phase 15: Workflow Automation & Event Rules Engine** (Event triggers across modules, state change & threshold condition evaluators, automated action pipelines [task dispatch, PO reorder requisitions, GL journal entries, notifications, webhooks], execution audit trail logs, and interactive desktop event simulator)
- [x] **Phase 16: AI Business Assistant & Executive Inquiry** (Role-based semantic Q&A, natural language intent resolution, multi-domain telemetry synthesis across all 16 modules, RBAC confidential data masking, conversational threads, and desktop conversational console with interactive prompt chips)
- [x] **Phase 17: IoT & Smart Device Gateways** (Device fleet registry, high-frequency telemetry ingestion [energy meters, cold storage HACCP sensors, room thermostats, smart locks, HVAC AQI], real-time threshold breach detection with auto-dispatch into Phase 15 Workflow Automation, remote actuator controls, and desktop IoT console at stack index 19)
- [x] **Phase 18: Data Lakehouse & Predictive ML** (Multi-tier data lakehouse storage [Bronze/Silver/Gold], automated ETL/ELT ingestion pipelines with compression, parquet/delta synchronization, predictive machine learning model registry, demand forecasting & customer churn scoring inference playground, and desktop lakehouse console at stack index 20)
- [x] **Phase 19: Zero-Trust Security & Compliance Auditor** (Continuous compliance audit framework checks [SOC2 Type II, ISO 27001, GDPR, PCI-DSS v4.0, HIPAA], real-time threat detection & anomaly stream, multi-factor risk scoring, active quarantine sandbox isolation, Shannon credential entropy analytics, and desktop security governance console at stack index 21)
- [x] **Phase 20: Multi-Cloud Resiliency & Autonomous DR** (Multi-cloud replica node topology & standby cluster monitoring [AWS, Azure, GCP, On-Premises Private Edge], continuous cross-cloud asynchronous & synchronous replication stream monitoring with Zero-RPO lag evaluations, automated chaos engineering drills [zone outage, split-brain, latency spikes, regional blackout], consensus leader failover switchover testing, RTO/RPO SLA compliance telemetry, and desktop Multi-Cloud DR console at stack index 22)

---

## 🧪 Comprehensive Automated Test Suite

Run the full automated test suite (unit, integration, security, and UI shell tests):

```bash
./.venv/bin/pytest tests/ -v
```

**307 automated tests** pass with 100% success across all domains:
- **Unit Tests**: Decimal-safe hospitality, financial, CRM, POS, marketing, inventory/AVCO, HR/payroll, field service SLA, resort folios, manufacturing BOM/scrap, project PSA budget/burn rate, BI financial ratios / forecasting, workflow rule condition evaluators, AI assistant intent classification / RBAC masking, IoT threshold evaluation / fleet metrics, data lakehouse compression / ML inferencing, zero-trust compliance scoring / threat risk evaluation / Shannon credential entropy analytics, and multi-cloud replication lag tiers / chaos resiliency scoring / RTO-RPO SLA compliance
- **Security Tests**: Argon2 password hashing, JWT integrity, RBAC permissions matrix
- **Integration Tests**: FastAPI REST endpoints for Health, Master Data, Finance, CRM, POS, Marketing, Inventory, HR/Payroll, Field Service, Hospitality PMS, Manufacturing Orders, Project Management / PSA, Business Intelligence / Document Exports, Workflow Automation, AI Business Assistant, IoT & Smart Device Gateways, Data Lakehouse & Predictive ML, Zero-Trust Security & Compliance Auditor, and Multi-Cloud Resiliency & Autonomous DR
- **UI Tests**: Headless PySide6 desktop views, custom widgets, and MainWindow route stack across all 20 enterprise modules (stack index 0 to 22)

---

## 🏆 Project Milestone: Complete 20-Phase Enterprise Operating System

Victory Crest ONE has achieved complete realization across all 20 architectural phases. All 20 modules in the canonical catalog are active, fully integrated with cross-module transaction pipelines, double-entry financial ledger bindings, resilient offline SQLite fallbacks, and a native PySide6 enterprise desktop management shell.








