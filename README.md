# 🚀 MediStock — Intelligent Medical Store & Pharmacy Management Platform

> ### 🌐 Live Cloud Deployment
> - **Production URL**: **[https://medistock-0irl.onrender.com](https://medistock-0irl.onrender.com)**
> - **Swagger API Documentation**: **[https://medistock-0irl.onrender.com/api/v1/schema/swagger-ui/](https://medistock-0irl.onrender.com/api/v1/schema/swagger-ui/)**
> - **Demo Credentials**: 
>   - **Admin**: `admin` / `admin123`
>   - **Pharmacist**: `pharmacist` / `pharma123`
>   - **Inventory**: `inventory` / `inv123`
>   - *(Or use the 1-click Role Switcher inside the UI)*

[![Live Demo](https://img.shields.io/badge/Live_Demo-medistock--0irl.onrender.com-success.svg?style=for-the-badge&logo=render)](https://medistock-0irl.onrender.com)
[![Swagger](https://img.shields.io/badge/API_Docs-Interactive_Swagger-85EA2D.svg?style=for-the-badge&logo=swagger)](https://medistock-0irl.onrender.com/api/v1/schema/swagger-ui/)

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-092E20.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/Django_REST_Framework-3.14+-red.svg)](https://www.django-rest-framework.org/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg)](https://react.dev/)
[![Tests](https://img.shields.io/badge/Pytest-21%20Passed%20(100%25)-brightgreen.svg)](https://pytest.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)](https://www.docker.com/)

MediStock is an enterprise-grade medical store and pharmacy operations platform engineered with **Django REST Framework**, **MySQL/Django ORM**, and **React.js**. It features a **transactional FEFO (First Expiry, First Out) allocation algorithm**, multi-batch pharmaceutical tracking, real-time expiry classification, POS billing with invoice generation, prescription verification workflows, supplier purchasing, and an analytical KPI telemetry dashboard.

---

## 🏛️ System Architecture

```mermaid
graph TD
    subgraph Frontend["Frontend Layer (React.js SPA)"]
        UI["React 18 SPA (Tailwind CSS)"]
        POS_UI["Point-of-Sale Terminal"]
        EXP_UI["Expiry Monitor & Alerts"]
        RX_UI["Prescription Queue"]
        DASH_UI["Operational KPI Dashboard"]
    end

    subgraph API["REST API Layer (Django REST Framework v1)"]
        AUTH["/api/v1/auth/ (JWT & RBAC)"]
        MED["/api/v1/medicines/"]
        INV["/api/v1/inventory/ (FEFO Engine)"]
        SALES["/api/v1/sales/ (Transactional Checkout)"]
        PUR["/api/v1/purchases/"]
        RX["/api/v1/prescriptions/"]
        ANL["/api/v1/analytics/ (Telemetry)"]
        DOCS["/api/v1/schema/swagger-ui/"]
    end

    subgraph DB["Persistence Layer (MySQL / Django ORM)"]
        M_MED["Medicine Catalog & Batches"]
        M_SUP["Suppliers & Purchase Orders"]
        M_SALE["Sales & Invoice Items"]
        M_ALLOC["SaleItem Batch Allocations"]
        M_AUDIT["Inventory Audit Ledger"]
    end

    UI -->|"HTTP / REST API (JWT Authenticated)"| AUTH
    AUTH --> MED
    AUTH --> INV
    AUTH --> SALES
    AUTH --> PUR
    AUTH --> RX
    AUTH --> ANL
    SALES --> M_SALE
    SALES --> M_ALLOC
    INV --> M_ALLOC
    PUR --> M_SUP
    MED --> M_MED
    M_ALLOC --> M_AUDIT
```

---

## 🗄️ Relational Database Schema (ER Diagram)

```mermaid
erDiagram
    CATEGORY ||--o{ MEDICINE : classifies
    MEDICINE ||--o{ BATCH : contains_multiple
    SUPPLIER ||--o{ BATCH : supplies
    SUPPLIER ||--o{ PURCHASE_ORDER : receives_from
    PURCHASE_ORDER ||--o{ PURCHASE_ITEM : contains
    MEDICINE ||--o{ PURCHASE_ITEM : references
    CUSTOMER ||--o{ SALE : purchases
    USER ||--o{ SALE : cashiers
    SALE ||--o{ SALE_ITEM : bills
    MEDICINE ||--o{ SALE_ITEM : sold_as
    SALE_ITEM ||--o{ SALE_ITEM_BATCH_ALLOCATION : fefo_deducts
    BATCH ||--o{ SALE_ITEM_BATCH_ALLOCATION : sourced_from
    MEDICINE ||--o{ INVENTORY_AUDIT_LOG : tracks
    BATCH ||--o{ INVENTORY_AUDIT_LOG : audits
    CUSTOMER ||--o{ PRESCRIPTION : submits
    PRESCRIPTION ||--o{ PRESCRIPTION_ITEM : prescribes
    MEDICINE ||--o{ PRESCRIPTION_ITEM : references
    PRESCRIPTION ||--o{ SALE : clears

    MEDICINE {
        int id PK
        string name
        string generic_name
        string brand
        string dosage_form
        string strength
        boolean prescription_required
        int reorder_level
        int maximum_stock
    }

    BATCH {
        int id PK
        string batch_number
        int medicine_id FK
        date manufacturing_date
        date expiry_date
        decimal purchase_price
        decimal selling_price
        int quantity
        boolean is_active
    }

    SALE {
        int id PK
        string invoice_number
        int customer_id FK
        int cashier_id FK
        decimal subtotal
        decimal discount_amount
        decimal tax_amount
        decimal total_amount
        string payment_method
        datetime created_at
    }

    SALE_ITEM_BATCH_ALLOCATION {
        int id PK
        int sale_item_id FK
        int batch_id FK
        int allocated_quantity
        decimal unit_price
        decimal subtotal
    }
```

---

## 🔬 Core Algorithms & Technical Highlights

### 1. FEFO (First Expiry, First Out) Inventory Engine
Unlike basic CRUD systems that randomly reduce stock, MediStock utilizes a mathematically deterministic algorithm prioritizing batches expiring earliest:
- **Filtering**: Ignores already expired stock (`expiry_date <= today`).
- **Sorting**: Evaluates non-expired batches sorted by `expiry_date ASC, id ASC`.
- **Concurrency Locking**: Employs row-level database locking with `select_for_update()` inside `transaction.atomic()`.
- **Multi-Batch Splitting**: If Batch A has 20 units and the customer requires 25 units, the algorithm automatically consumes 20 units from Batch A (reducing it to 0) and 5 units from Batch B (reducing it to 45), leaving Batch C intact.
- **Traceability**: Records individual `SaleItemBatchAllocation` records linking every dispensed box to its originating batch for regulatory audit compliance.

### 2. Multi-tier Expiry Classification Matrix
The platform continuously classifies stock across 4 discrete healthcare tiers:
| Tier | Condition | System Action |
|---|---|---|
| **Expired** | `expiry_date < today` | Quarantined; strictly blocked from POS checkout |
| **Critical** | `today <= expiry_date <= today + 7d` | Red Alert; prioritized by FEFO; discount suggested |
| **Warning** | `today + 7d < expiry_date <= today + 30d` | Amber Alert; monitored in telemetry queue |
| **Normal** | `expiry_date > today + 30d` | Standard operational shelf-life |

### 3. Smart Inventory Telemetry
- **Low Stock Detection**: `total_non_expired_stock <= reorder_level`.
- **Overstock Prevention**: `total_stock > maximum_stock`.
- **Dead-Stock Heuristic**: Scans medicines with zero sales transactions in the past configurable period (e.g. 60 or 90 days).

---

## 🔐 Role-Based Access Control (RBAC) Matrix

| Action | Admin | Pharmacist | Inventory Manager | Customer |
|---|:---:|:---:|:---:|:---:|
| Manage Users & Roles | ✅ | ❌ | ❌ | ❌ |
| Conduct POS Sales | ✅ | ✅ | ❌ | ❌ |
| Manage Inventory & Batches | ✅ | Read Only | ✅ | ❌ |
| Manage Suppliers & POs | ✅ | ❌ | ✅ | ❌ |
| Verify Prescriptions | ✅ | ✅ | ❌ | ❌ |
| Upload & View Prescriptions | ✅ | ✅ | ❌ | ✅ |
| View Own Purchase History | ✅ | ❌ | ❌ | ✅ |

---

## 🧪 Comprehensive Pytest Test Suite

MediStock includes 21 unit, integration, and API tests:
```bash
# Run pytest test suite
pytest -v --tb=short
```

### Test Coverage Highlights:
- **`test_fefo_allocation_exact_example`**: Validates 25-unit multi-batch split across Batch A, B, and C.
- **`test_fefo_skips_expired_batches`**: Guarantees expired batches are bypassed even if older.
- **`test_complete_pharmacy_lifecycle`**: End-to-end integration (PO -> Receive -> Batch -> Sale -> FEFO -> Ledger).
- **`test_negative_sell_expired_batch`**: Negative test preventing expired item dispensing.
- **`test_negative_rx_required_without_prescription`**: Negative test rejecting prescription drugs sold without an approved prescription.
- **`test_negative_role_based_permission_denied`**: Negative test validating customer role rejection on staff endpoints (403 Forbidden).

---

## ⚡ API Endpoints Quick Reference (v1)

All endpoints are versioned under `/api/v1/`:

| Module | Method | Endpoint | Description |
|---|---|---|---|
| **Auth** | `POST` | `/api/v1/auth/login/` | Obtain JWT token pair with user role payload |
| **Medicines** | `GET, POST` | `/api/v1/medicines/` | Catalog listing with computed stock levels |
| **Batches** | `GET, POST` | `/api/v1/inventory/batches/` | Multi-batch inventory tracking |
| **FEFO** | `POST` | `/api/v1/inventory/fefo-preview/` | Simulate FEFO deduction breakdown |
| **Alerts** | `GET` | `/api/v1/inventory/alerts/` | Expiry monitor & low-stock alerts |
| **Sales** | `POST` | `/api/v1/sales/` | Transactional POS checkout |
| **Purchases** | `POST` | `/api/v1/purchases/{id}/receive/` | Receive PO & instantiate inventory batches |
| **Prescriptions** | `POST` | `/api/v1/prescriptions/{id}/verify/` | Verify prescription (APPROVE / REJECT) |
| **Analytics** | `GET` | `/api/v1/analytics/kpis/` | Sales & inventory operational metrics |
| **Swagger** | `GET` | `/api/v1/schema/swagger-ui/` | OpenAPI 3.0 Interactive Documentation |

---

## 🚀 Getting Started

### Local Setup
```bash
# 1. Clone repository
git clone https://github.com/your-username/medistock.git
cd medistock

# 2. Activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations & seed realistic data
python manage.py migrate
python seed_data.py

# 5. Start development server
python manage.py runserver
```
Visit **http://localhost:8000** to access the complete application!

### Docker Setup
```bash
docker compose up --build
```
