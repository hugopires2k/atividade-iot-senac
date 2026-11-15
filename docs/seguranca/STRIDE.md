# Threat model (STRIDE) - main flow: sensor -> API -> database -> dashboard/app

Assets: reading integrity, user accounts, device keys, availability of the data flow.
Trust boundaries: (1) board <-> internet, (2) browser/app <-> internet, (3) API <-> database.

| | Threat | Where | Risk | Control (status) |
|---|---|---|---|---|
| **S**poofing | Someone sends fake readings pretending to be a device | Boundary 1 | High | Per-device key in `X-Device-Key`, stored as SHA-256; a valid key for device A cannot write as device B (403). **Done** |
| **S** | Stolen user session | Boundary 2 | Medium | JWT HS256 with expiry (60 min); wrong/expired token -> 401. **Done** |
| **T**ampering | Reading modified in transit | Boundary 1 | High | HTTPS to the API. The board does **not yet validate the certificate** unless `API_ROOT_CA` is set. **Partial** |
| **T** | Malformed or absurd values poison the data | Boundary 1 | Medium | Validation: out-of-range -> 400 and nothing stored. **Done** |
| **R**epudiation | Nobody can tell which device sent what | API | Low | `device_id`, `seq`, `ts`, `received_at` on every row; `origin` field. **Done** |
| **I**nfo disclosure | User reads another user's device | API | High | Object-level check on every `/devices/{id}/...` route (403). **Done** |
| **I** | Secrets in git | Repo | High | `.env` and `config.h` in `.gitignore`; only `.env.example` / `config.h.example` committed. **Done** (revoke at once if a key leaks) |
| **D**enial of service | Flooding the API | Boundary 1/2 | Medium | Request rate limit. **Pending (final)** |
| **D** | Wi-Fi/API outage loses data | Board | Medium | RAM buffer + ordered resend + idempotency. **Done** (RAM only) |
| **E**levation | Normal user acts as admin | API | Medium | Role stored server-side; ownership never trusts the token's role claim. **Done** |

Highest risk to fix first: certificate validation on the board (Tampering).
Mitigation: set `API_ROOT_CA` to the host's root CA and remove `setInsecure()`.
