# Test plan (previa)

Goal: prove the main routes behave as specified (ISO/IEC 25010: reliability, security, functional suitability).

| Area | Case | Expected | Automated |
|---|---|---|---|
| Auth | No token / garbage token | 401 | yes |
| Auth | Wrong password | 401 | yes |
| Authorization | Token of another user on `/latest`, `/readings`, `/stats` | 403 | yes |
| Device key | Missing / wrong key | 401, nothing stored | yes |
| Device key | Key of device A posting as device B | 403, nothing stored | yes |
| Validation | Out-of-range value, malformed body, future timestamp | 400, nothing stored | yes |
| R5 | Null sensor value | stored with `valid = false`, `sensor_fault = true` | yes |
| R3 / F5 | Same `seq` twice | 200 `duplicate`, 1 row | yes |
| Pagination | `limit`, `offset`, order, `limit` too large | correct page / 400 | yes |
| R6/R7 | Device silent for 10 min | `online=false`, `stale=true` | yes |
| Health | `/health` | 200 + db ok | yes |
| F1, F3 | Hotspot off / sensor unplugged | see `RESILIENCIA.md` | manual (hardware) |

Run: `cd backend && pytest --cov=app` (currently 21 tests, 95 % coverage). CI runs the same on every push and fails under 60 %.
