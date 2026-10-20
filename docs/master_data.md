# Victory Crest ONE — Shared Master Data Architecture

## 1. Canonical Customer Master

The Customer Master centralizes client identity across CRM, POS, Commerce, Hotel Folios, and Accounts Receivable:
- **`code`:** Unique business customer code (e.g. `CUST-CORP-001`, `CUST-VIP-002`).
- **`customer_type`:** `INDIVIDUAL` or `CORPORATE`.
- **Deduplication Engine:** Prevents duplicate account creation through automatic verification of unique email, phone number, and tax identification numbers per organization.
- **Credit Limits & Loyalty:** Manages credit limit balances and loyalty points earned across dining, stays, and purchases.

---

## 2. Supplier & Vendor Master

The Supplier Master provides canonical vendor profiles for ERP, Procurement, and Accounts Payable:
- **`code`:** Unique supplier code (e.g. `SUPP-TXT-101`, `SUPP-FNB-202`).
- **`payment_terms_days`:** Standard credit terms (e.g. 15, 30, 45, 60 days).
- **`lead_time_days`:** Expected supply delivery turnaround.
- **`rating`:** Vendor performance score (1.00 to 5.00).

---

## 3. Product & Service Master

A unified catalog shared by Hospitality, Dining, Commerce, Point of Sale, and Inventory:
- **`sku` & `barcode`:** Globally unique stock keeping units and GS1/UPC barcodes.
- **`item_type`:**
  - `PHYSICAL` — Inventory tracked goods.
  - `SERVICE` — Intangible services (room nights, spa treatments, labour).
  - `RAW_MATERIAL` — Manufacturing ingredients and supplies.
  - `RECIPE_DISH` — Restaurant menu culinary items composed of ingredients.
- **`tax_rate_percent`:** Jurisdictional tax rates (e.g. 5.00%, 12.00%, 18.00%, 28.00%).

---

## 4. Secure Document Vault

Central document vault linking files and digital attachments to business records:
- **Storage Directory:** Encrypted and partitioned under `local_data/documents/`.
- **Categories:** `INVOICE`, `CONTRACT`, `ID_PROOF`, `REPORT`, `GENERAL`.
- **Record Linking:** Binds files to `Organization`, `Property`, `Customer`, `Reservation`, or `Invoice`.
- **Version Control:** Auto-incrementing version headers with uploader email and audit logging.

---

## 5. In-App Notifications

- **Types:** `INFO`, `WARNING`, `ALERT`, `APPROVAL`.
- **Targeting:** Broadcast to specific `user_id` or `target_role` (e.g., alert Finance Managers of pending large credit limits).
- **Unread Tracking:** Synchronized real-time badge counters in the desktop top toolbar.
