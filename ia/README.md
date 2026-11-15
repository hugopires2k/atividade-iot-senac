# AI (previa)

- **Problem:** forecast the temperature ~5 minutes ahead so the user is warned before a threshold is crossed.
- **Baseline:** persistence (next value = current value), MAE in °C. Computed by `baseline.py` on a **temporal** split.
- **Status:** baseline script ready. The baseline *number* must come from real data collected by the board (>= 48 h);
  `--demo` only proves the script runs.
- **Final delivery:** model that beats the baseline on the temporal test set, served on `/predict`,
  shown on the dashboard and in the app, with a model card (limitations included).

Export data for the script (any user token): `GET /api/v1/devices/{id}/readings?limit=500&offset=...` and save as CSV
with columns `ts,temperature_c,humidity_pct,light_pct` (or use the SQL export from `database/`).
