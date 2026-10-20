# Victory Crest ONE — Security & RBAC Architecture

## 1. Authentication & Cryptography

### Argon2 Password Hashing
Victory Crest ONE enforces Argon2id password hashing using the following OWASP-compliant parameter configuration:
- **Algorithm:** Argon2id (`argon2-cffi`)
- **Memory Cost:** 65,536 KiB (64 MiB)
- **Time Cost:** 2 iterations
- **Parallelism:** 2 threads
- **Salt Length:** 16 bytes (cryptographically randomized per hash)
- **Hash Length:** 32 bytes

Plaintext passwords are never logged, persisted in plaintext, or transmitted unencrypted.

### JWT Access Tokens
Authenticated sessions issue signed JSON Web Tokens (RFC 7519):
- **Signing Algorithm:** HMAC-SHA256 (`HS256`)
- **Claims:** `sub` (user UUID), `username`, `email`, `role`, `org_id`, `prop_id`, `iss` (`victory-crest-one`), `iat`, `exp` (configurable expiration, default 480 minutes).
- **Validation:** Every protected endpoint verifies signature, issuer, and expiration before processing requests.

---

## 2. Role-Based Access Control (RBAC) & Separation of Duties

### The 30 Enterprise Roles
1. `System Administrator` — Full platform configuration and tenant access.
2. `Organisation Owner` — Top-level enterprise owner.
3. `Group General Manager` — Cross-property executive oversight.
4. `General Manager` — Single property operational management.
5. `Finance Manager` — Financial approval, GL postings, disbursements.
6. `Accountant` — Journal preparation, invoicing, reconciliation.
7. `Sales Manager` — Sales pipeline, commissions, and team targets.
8. `Sales Representative` — Lead qualification, opportunities, quotes.
9. `Marketing Manager` — Campaigns, segmentation, attribution.
10. `E-commerce Manager` — Web storefront, digital catalog, shipping.
11. `Store Manager` — Retail store inventory and sales.
12. `POS Cashier` — Register operations, transactions, shift closing.
13. `Customer Service Manager` — Support escalations, SLA rules.
14. `Service Technician` — Field job cards, repair checklists.
15. `ERP Manager` — End-to-end supply chain orchestration.
16. `Procurement Manager` — Supplier POs and vendor contracts.
17. `Inventory Manager` — Multi-warehouse transfers, lot tracking.
18. `Manufacturing Manager` — BOM recipes, production runs.
19. `HR Manager` — Employee lifecycle, policies, recruitment.
20. `HR Staff` — Onboarding checklists, document verification.
21. `Payroll Administrator` — Salary components, deductions, payslips.
22. `Business Intelligence Analyst` — Star-schema cubes, reports.
23. `Data Analyst` — ETL pipelines, analytical exports.
24. `Project Manager` — Portfolios, milestones, resource allocation.
25. `Hotel Manager` — Front desk, room inventory, guest folios.
26. `Receptionist` — Check-in/out, folio postings.
27. `Housekeeping Manager` — Room cleaning, inspection assignments.
28. `Restaurant Manager` — Dining tables, KDS kitchen orders, billing.
29. `Auditor` — Read-only compliance and audit log access.
30. `Read-Only User` — Restricted view and export.

### Separation of Duties (SoD) Rules
- **Journal Approvals:** An `Accountant` can create, edit, and submit financial journals, but **cannot** approve their own postings. Only a `Finance Manager` or `Organisation Owner` may approve financial entries.
- **Transaction Deletions:** Operational roles (`POS Cashier`, `Receptionist`) cannot delete transactions or modify posted accounting ledger items.
- **Audit Neutrality:** An `Auditor` possesses system-wide view and audit log access, but is strictly prohibited from creating, modifying, or deleting operational records.

---

## 3. Immutable Audit Trail

Every security-sensitive operation is recorded in the `audit_logs` store:
- `LOGIN_SUCCESS` / `LOGIN_FAILED`
- `USER_CREATED` / `USER_DEACTIVATED`
- `PERMISSION_DENIED`
- `ROLE_CHANGED`
- `JOURNAL_POSTED` / `JOURNAL_APPROVED`
- Context captured: `user_id`, `user_email`, `action`, `entity_type`, `entity_id`, `ip_address`, `timestamp_utc`.
