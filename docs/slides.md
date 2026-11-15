# Pitch deck (max 6 slides, English) and 2-minute script

1. **Problem + persona** - people can't be where the sensor is, and most sensors fail silently.
2. **Solution** - ESP32 + DHT22 + LDR -> HTTPS API -> dashboard and mobile app that says *how old* each value is.
3. **Architecture** - diagram from the README; two paths: API (must not lose data) and ThingSpeak (best effort).
4. **Resilience** - buffer + ordered resend, idempotent API, an invalid sensor is never stored as valid. F1 and F3 live.
5. **Evidence** - CI green, 21 tests, 95 % coverage, top STRIDE risk, baseline MAE (use the real number once there is data).
6. **Next steps** - TLS validation on the board, cloud backup, AI model on `/predict`, push alerts, SUS test with 5 users.

## 2-minute pitch (say it out loud, don't memorize it word for word)
"Good evening. Our project is an environment monitor. Think of someone who needs to know the temperature,
humidity and light of a place while they're away. Most solutions show a number, but they don't tell you when that
number is old, or when a sensor has died. Our board reads three variables and sends each reading to a cloud API.
Every reading carries an identifier, a sequence number and a UTC timestamp, so we can show that nothing was lost
or duplicated. If the Wi-Fi drops, the board keeps the readings and sends them in order when it comes back.
If a sensor fails, the dashboard says so instead of showing a made-up value. In the next minutes we will trace one
physical event from the sensor to the phone, and then we will break things on purpose."
