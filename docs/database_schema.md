# Victory Crest ONE — Database Schema Foundation

## 1. Central PostgreSQL Database Schema

### Table: `organizations`
- `id` (VARCHAR(36), PK, UUID)
- `code` (VARCHAR(20), Unique, Indexed)
- `name` (VARCHAR(150), Not Null)
- `legal_name` (VARCHAR(200), Not Null)
- `currency` (VARCHAR(3), Default 'INR')
- `tax_identifier` (VARCHAR(50), Nullable)
- `is_active` (BOOLEAN, Default True)
- `is_simulated` (BOOLEAN, Default False)
- `created_at` (TIMESTAMP, Default UTC)
- `updated_at` (TIMESTAMP, Default UTC)
- `is_deleted` (BOOLEAN, Default False, Indexed)

### Table: `properties`
- `id` (VARCHAR(36), PK, UUID)
- `organization_id` (VARCHAR(36), FK -> `organizations.id`, Indexed)
- `code` (VARCHAR(20), Not Null, Indexed)
- `name` (VARCHAR(150), Not Null)
- `property_type` (VARCHAR(50), Not Null) — hotel, resort, restaurant, retail_store, corporate_office
- `status` (VARCHAR(50), Default 'active')
- `city` (VARCHAR(100), Not Null)
- `state` (VARCHAR(100), Not Null)
- `country` (VARCHAR(100), Default 'India')
- `rooms_count` (INTEGER, Default 0)
- `is_simulated` (BOOLEAN, Default False)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)
- `is_deleted` (BOOLEAN)

### Table: `departments`
- `id` (VARCHAR(36), PK, UUID)
- `organization_id` (VARCHAR(36), FK -> `organizations.id`, Indexed)
- `code` (VARCHAR(20), Not Null)
- `name` (VARCHAR(100), Not Null)
- `is_active` (BOOLEAN, Default True)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Table: `users`
- `id` (VARCHAR(36), PK, UUID)
- `email` (VARCHAR(255), Unique, Indexed)
- `username` (VARCHAR(100), Unique, Indexed)
- `hashed_password` (VARCHAR(255), Argon2 Hash)
- `full_name` (VARCHAR(150), Not Null)
- `is_active` (BOOLEAN, Default True)
- `is_superuser` (BOOLEAN, Default False)
- `primary_organization_id` (VARCHAR(36), FK -> `organizations.id`)
- `primary_property_id` (VARCHAR(36), FK -> `properties.id`)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Table: `audit_logs`
- `id` (VARCHAR(36), PK, UUID)
- `organization_id` (VARCHAR(36), Indexed)
- `property_id` (VARCHAR(36), Indexed)
- `user_id` (VARCHAR(36), Indexed)
- `user_email` (VARCHAR(255))
- `action` (VARCHAR(50), Indexed) — LOGIN, CREATE, UPDATE, DELETE, EXPORT
- `entity_type` (VARCHAR(50), Indexed)
- `entity_id` (VARCHAR(36), Indexed)
- `details` (TEXT)
- `ip_address` (VARCHAR(45))
- `user_agent` (VARCHAR(255))
- `created_at` (TIMESTAMP)

---

## 2. Local SQLite Database Schema (Offline Mode)

Located at: `local_data/victory_crest_local.db`

Contains local caching and durable operation queue:
- `local_operation_queue`: Queued offline transactions (operation_id, module, payload, retry_count, idempotency_key, created_at, status).
- `cached_catalog`: Local replica of active organization and module settings.
- `sync_state`: Last sync timestamp, conflict detection hashes.
