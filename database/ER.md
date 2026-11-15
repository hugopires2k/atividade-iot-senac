# Entity-relationship diagram

```mermaid
erDiagram
    USERS ||--o{ DEVICES : owns
    DEVICES ||--o{ READINGS : produces
    USERS { int id PK  string email UK  string password_hash  string role }
    DEVICES { string id PK  int owner_id FK  string name  string api_key_hash  int interval_s  datetime last_seen_at }
    READINGS { int id PK  string device_id FK  int seq  datetime ts  float temperature_c  float humidity_pct  float light_pct  bool temp_valid  bool hum_valid  bool light_valid  string origin }
```

`UNIQUE (device_id, seq)` is what makes the ingestion idempotent: the same message sent twice leaves one row.
Sample queries for the live SQL step of the traceability demo are in `database/queries.sql`.
