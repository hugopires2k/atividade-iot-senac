# UC requirements matrix (previa v0.9)

Status is **Atendido** only when there is observable evidence. Everything else is Parcial or Pendente.

| ID | UC | Requirement | Where it is implemented | Evidence | Status |
|---|---|---|---|---|---|
| IOT-01 | IoT | Board with >= 2 sensors reading with physical units | `firmware/previa/previa.ino` | Serial monitor `[P1]` lines (DHT22 °C/%, LDR %) | Parcial |
| IOT-02 | IoT | R1 reconnect + R5 invalid sensor handling | `previa.ino` (`ensureWifi`, `sample`) | Tests F1 and F3 in the demo | Parcial |
| IOT-03 | IoT | ThingSpeak receiving real data, interval >= 15 s, HTTP response checked | `previa.ino` (`sendThingSpeak`) | Channel feed | Parcial |
| IOT-04 | IoT | >= 48 h of collected data with descriptive stats | `/stats`, `database/queries.sql` | Export + summary | Pendente |
| CLD-01 | Cloud | API on HTTPS, config by environment variables | `infra/Dockerfile`, `backend/.env.example` | Public URL + CI log | Pendente |
| CLD-02 | Cloud | Dockerfile, secrets outside the code | `infra/Dockerfile`, `.gitignore` | Image builds in CI | Parcial |
| SEG-01 | Security | STRIDE threat model of the main flow | `docs/seguranca/STRIDE.md` | Document | Atendido |
| SEG-02 | Security | JWT auth; user only reaches own devices | `backend/app/security.py` | `test_other_users_device_is_403`, `test_no_token_is_401` | Atendido |
| SEG-03 | Security | A device key cannot be used to impersonate another device | `device_from_key`, `ingest` | `test_key_of_one_device_cannot_write_as_another` | Atendido |
| QUA-01 | Quality | Test plan | `docs/qualidade/TEST_PLAN.md` | Document | Atendido |
| QUA-02 | Quality | Automated tests of main routes in GitHub Actions | `backend/tests`, `.github/workflows/ci.yml` | Green run after push | Parcial |
| IA-01 | AI | Problem defined and baseline computed | `ia/baseline.py`, `ia/README.md` | MAE of the baseline on real data | Parcial |
| MOB-01 | UE Mobile | Navigable prototype (Figma) | - | Figma link | Pendente |
| MOB-02 | UE Mobile | App authenticates and lists real readings | `mobile/` (PWA) | Demo on a phone | Parcial |
| CON-01 | Consumer | Persona, journey, value proposition backed by research (>= 5 interviews or >= 20 answers) | `docs/ux/` | Raw answers | Pendente |
| ENG-01 | Tech English | README and API docs in English | `README.md`, `/docs` | Files | Atendido |
| ENG-02 | Tech English | 2-minute pitch in English | `docs/slides.md` | Rehearsal | Parcial |

Every Parcial/Pendente item goes into `PLANO_ACAO.md`.
