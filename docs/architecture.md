# Architecture and data flow

See the diagram and port table in the root `README.md`. Traceability steps used in the demo:

| Step | Where | What is shown |
|---|---|---|
| P1 | Serial monitor | `[P1] seq=… ts=… temp=…` |
| P2 | Serial + ThingSpeak + API | `[P2] ThingSpeak OK entry=…` and `[P2] API seq=… -> http=201` |
| P3 | API | request accepted (log line / `/docs`) |
| P4 | SQL | `database/queries.sql` first query: same `seq`, value and timestamp |
| P5 | Dashboard and app | same value, same `seq` |
| P6 | BI indicator / AI | `/stats` indicators on the dashboard; AI result pending until the final |

> The P1-P6 split above is our reading of the enunciado. Confirm it with the professor.
