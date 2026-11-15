# Resilience (previa: R1, R5, F1, F3)

| ID | Requirement | Implementation | Status |
|---|---|---|---|
| R1 | Automatic reconnect | `ensureWifi()`: wait doubles from 1 s to 30 s and never blocks the loop; restart after 30 failed attempts. API errors use the same growing wait (2 s -> 60 s). | Implemented, untested on hardware |
| R2 | Store and resend | RAM ring buffer of 120 readings; the oldest is removed only after the API answers 200/201; stops at the first failure so order is kept. | Implemented (RAM only: lost on power cut) |
| R3 | Message identity | `device_id`, `seq` (saved in NVS every 10 readings, jumps +10 after a reboot), UTC `ts` from NTP. `UNIQUE(device_id, seq)` makes the API idempotent. | Implemented |
| R4 | Watchdog | Task watchdog, 30 s, reset inside the loop. | Implemented, untested |
| R5 | Sensor failure | NaN/out-of-range -> `null` in the JSON -> stored as invalid; serial prints `[R5] ALERT`; dashboard and app show "Sensor fault". | Implemented |
| R6 | Controlled degradation | `/latest` returns `stale: true`; UI shows "No data since HH:MM" instead of an old value as current. A ThingSpeak failure does not touch the API path. | Implemented |
| R7 | Observability | Every reading is a heartbeat; `last_contact` + online/offline (75 s); `/health`. | Partial (logs not centralized) |
| R8 | Cloud recovery | Docker `HEALTHCHECK`, `restart: unless-stopped`; managed backup not set up. | Pending (final) |

## Test procedures and results (fill in with REAL measurements)

### F1 - network drop (hotspot off for 60 s)
1. Note the last `seq` on the serial monitor. 2. Turn the hotspot off for 60 s. 3. Turn it on.
4. Run the "gaps" query in `database/queries.sql`. Pass: reconnects within 30 s and **0 rows** returned.

| Date | Reconnect time (s) | Missing seq | Result |
|---|---|---|---|
| 16/11 | | | |

### F3 - sensor failure (unplug the DHT22 data wire)
Pass: serial prints `INVALID` + `[R5] ALERT`, the dashboard shows the alert, and the newest row has `temp_valid = false` with `temperature_c IS NULL`.

| Date | Alert visible | Invalid stored as valid? | Result |
|---|---|---|---|
| 16/11 | | | |
