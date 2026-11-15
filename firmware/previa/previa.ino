/*
  IoT Environment Monitor - firmware v0.9 (previa)
  Board: ESP32 | Sensors: DHT22 (temperature, humidity) + LDR (light)

  What this covers from the spec:
    R1  Wi-Fi/server reconnect with growing wait (capped) - never blocks the loop
    R2  RAM ring buffer, resend in order after reconnect   (desirable in previa)
    R3  device_id + sequence number + UTC timestamp (NTP)  (seq persisted in NVS)
    R4  Task watchdog                                      (desirable in previa)
    R5  NaN / missing / out-of-range reading -> sent as null, never as a valid value
    R7  every reading doubles as a heartbeat
  Libraries (Library Manager): "DHT sensor library" + "Adafruit Unified Sensor", "ArduinoJson" (v7)
*/
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include <esp_task_wdt.h>
#include "config.h"

// ---------- tuning ----------
const size_t   BUF_SIZE        = 120;        // 120 readings x 20 s = 40 min of offline storage
const uint32_t WDT_SECONDS     = 30;
const uint32_t WIFI_BACKOFF_MIN = 1000;      // ms
const uint32_t WIFI_BACKOFF_MAX = 30000;     // ms
const uint8_t  WIFI_MAX_FAILS  = 30;         // ~15 min without Wi-Fi -> restart as last resort
const uint32_t API_BACKOFF_MIN = 2000;
const uint32_t API_BACKOFF_MAX = 60000;
const uint8_t  FLUSH_PER_LOOP  = 5;
const uint32_t SEQ_SAVE_EVERY  = 10;         // NVS write every N readings (flash wear)
const time_t   MIN_VALID_EPOCH = 1735689600; // 2025-01-01: anything earlier means NTP not synced

// physical ranges (same limits the API enforces)
const float T_MIN = -40, T_MAX = 80, H_MIN = 0, H_MAX = 100;

DHT dht(DHT_PIN, DHT22);
Preferences prefs;

struct Reading {
  uint32_t seq; time_t ts;
  float temp, hum, light;          // NAN = invalid
};
Reading ring[BUF_SIZE];
size_t ringHead = 0, ringCount = 0;
uint32_t droppedReadings = 0;

uint32_t seqCounter = 0;
unsigned long lastSample = 0;
unsigned long lastWifiTry = 0, wifiBackoff = WIFI_BACKOFF_MIN;
uint8_t wifiFails = 0;
unsigned long nextApiTry = 0, apiBackoff = API_BACKOFF_MIN;

// ---------- ring buffer ----------
void ringPush(const Reading &r) {
  if (ringCount == BUF_SIZE) {            // full: drop the oldest, and say so
    ringHead = (ringHead + 1) % BUF_SIZE; ringCount--; droppedReadings++;
    Serial.printf("[WARN] buffer full, dropped oldest (total dropped=%u)\n", droppedReadings);
  }
  ring[(ringHead + ringCount) % BUF_SIZE] = r; ringCount++;
}
Reading &ringFront() { return ring[ringHead]; }
void ringPop() { ringHead = (ringHead + 1) % BUF_SIZE; ringCount--; }

// ---------- helpers ----------
String isoUtc(time_t t) {
  struct tm tmv; gmtime_r(&t, &tmv);
  char b[25]; strftime(b, sizeof b, "%Y-%m-%dT%H:%M:%SZ", &tmv);
  return String(b);
}
bool timeSynced() { return time(nullptr) > MIN_VALID_EPOCH; }

// ---------- R1: Wi-Fi reconnect, non-blocking ----------
void ensureWifi() {
  if (WiFi.status() == WL_CONNECTED) { wifiBackoff = WIFI_BACKOFF_MIN; wifiFails = 0; return; }
  if (millis() - lastWifiTry < wifiBackoff) return;
  lastWifiTry = millis();
  if (++wifiFails > WIFI_MAX_FAILS) { Serial.println("[R1] too many Wi-Fi failures, restarting"); delay(200); ESP.restart(); }
  Serial.printf("[R1] Wi-Fi down, attempt %u (next wait %lu ms)\n", wifiFails, wifiBackoff);
  WiFi.disconnect(); WiFi.begin(WIFI_SSID, WIFI_PASS);
  wifiBackoff = min(wifiBackoff * 2, (unsigned long)WIFI_BACKOFF_MAX);
}

// ---------- sensors (R5) ----------
Reading sample() {
  Reading r; r.seq = ++seqCounter; r.ts = time(nullptr);
  float t = dht.readTemperature(), h = dht.readHumidity();
  r.temp = (!isnan(t) && t >= T_MIN && t <= T_MAX) ? t : NAN;
  r.hum  = (!isnan(h) && h >= H_MIN && h <= H_MAX) ? h : NAN;
  // LDR in a voltage divider: a floating/unplugged pin tends to sit at a rail (0 or 4095).
  int raw = analogRead(LDR_PIN);
  r.light = (raw > 0 && raw < 4095) ? (raw * 100.0f / 4095.0f) : NAN;
  if (seqCounter % SEQ_SAVE_EVERY == 0) { prefs.putUInt("seq", seqCounter); }
  return r;
}
void logSerial(const Reading &r) {   // P1 in the traceability script: what the board measured
  Serial.printf("[P1] seq=%u ts=%s temp=%s hum=%s light=%s\n", r.seq, isoUtc(r.ts).c_str(),
    isnan(r.temp) ? "INVALID" : String(r.temp, 1).c_str(),
    isnan(r.hum) ? "INVALID" : String(r.hum, 1).c_str(),
    isnan(r.light) ? "INVALID" : String(r.light, 1).c_str());
  if (isnan(r.temp) || isnan(r.hum) || isnan(r.light)) Serial.println("[R5] ALERT: sensor failure, value NOT stored as valid");
}

// ---------- ThingSpeak (best effort, latest reading only) ----------
void sendThingSpeak(const Reading &r) {
  WiFiClientSecure c; c.setInsecure();   // telemetry channel only; the API path is the one we secure
  HTTPClient http; http.setTimeout(5000);
  String url = String("https://api.thingspeak.com/update?api_key=") + TS_WRITE_KEY;
  if (!isnan(r.temp))  url += "&field1=" + String(r.temp, 1);
  if (!isnan(r.hum))   url += "&field2=" + String(r.hum, 1);
  if (!isnan(r.light)) url += "&field3=" + String(r.light, 1);
  if (!http.begin(c, url)) { Serial.println("[P2] ThingSpeak: begin failed"); return; }
  int code = http.GET();
  String body = code > 0 ? http.getString() : "";
  http.end();
  // ThingSpeak answers the new entry id; "0" means the update was rejected (e.g. under 15 s).
  if (code == 200 && body != "0") Serial.printf("[P2] ThingSpeak OK entry=%s\n", body.c_str());
  else Serial.printf("[P2] ThingSpeak FAILED http=%d body=%s (ignored, API path continues)\n", code, body.c_str());
}

// ---------- API (the path that must not lose data) ----------
enum SendResult { SENT, RETRY_LATER, DROP };

SendResult postReading(const Reading &r) {
  JsonDocument doc;
  doc["device_id"] = DEVICE_ID; doc["seq"] = r.seq; doc["ts"] = isoUtc(r.ts); doc["origin"] = "device";
  if (isnan(r.temp))  doc["temperature_c"] = nullptr; else doc["temperature_c"] = r.temp;
  if (isnan(r.hum))   doc["humidity_pct"]  = nullptr; else doc["humidity_pct"]  = r.hum;
  if (isnan(r.light)) doc["light_pct"]     = nullptr; else doc["light_pct"]     = r.light;
  String body; serializeJson(doc, body);

  WiFiClientSecure c;
#ifdef API_ROOT_CA
  c.setCACert(API_ROOT_CA);
#else
  c.setInsecure();
#endif
  HTTPClient http; http.setTimeout(6000);
  if (!http.begin(c, API_URL)) return RETRY_LATER;
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Key", DEVICE_KEY);
  int code = http.POST(body);
  http.end();

  Serial.printf("[P2] API seq=%u -> http=%d\n", r.seq, code);
  if (code == 200 || code == 201) return SENT;      // 200 = duplicate, also fine (idempotent)
  if (code == 400) { Serial.println("[WARN] API rejected payload (400), dropping it"); return DROP; }
  return RETRY_LATER;                                // 401/403 (config), 5xx, timeouts (-1...)
}

// Resend buffered readings in order (R2). Stops at the first failure so order is preserved.
void flushBuffer() {
  if (ringCount == 0 || millis() < nextApiTry) return;
  for (uint8_t i = 0; i < FLUSH_PER_LOOP && ringCount > 0; i++) {
    esp_task_wdt_reset();
    SendResult res = postReading(ringFront());
    if (res == SENT || res == DROP) { ringPop(); apiBackoff = API_BACKOFF_MIN; }
    else {
      nextApiTry = millis() + apiBackoff;
      Serial.printf("[R1] API unreachable, retry in %lu ms (buffered=%u)\n", apiBackoff, (unsigned)ringCount);
      apiBackoff = min(apiBackoff * 2, (unsigned long)API_BACKOFF_MAX);
      return;
    }
  }
}

// ---------- setup / loop ----------
void startWatchdog() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  esp_task_wdt_config_t cfg = { .timeout_ms = WDT_SECONDS * 1000, .idle_core_mask = 0, .trigger_panic = true };
  esp_task_wdt_reconfigure(&cfg);
#else
  esp_task_wdt_init(WDT_SECONDS, true);
#endif
  esp_task_wdt_add(NULL);   // watch the Arduino loop task
}

void setup() {
  Serial.begin(115200); delay(300);
  Serial.println("\n== IoT Environment Monitor v0.9 ==");
  prefs.begin("iot", false);
  // After a reboot, jump ahead so we never reuse a sequence number the API already has.
  seqCounter = prefs.getUInt("seq", 0) + SEQ_SAVE_EVERY;
  Serial.printf("[R3] starting at seq=%u\n", seqCounter);
  dht.begin();
  analogReadResolution(12);
  WiFi.mode(WIFI_STA); WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  configTime(0, 0, "pool.ntp.org", "time.google.com");   // UTC
  startWatchdog();
}

void loop() {
  esp_task_wdt_reset();
  ensureWifi();
  bool online = WiFi.status() == WL_CONNECTED;

  if (millis() - lastSample >= SEND_INTERVAL_MS) {
    lastSample = millis();
    if (!timeSynced()) {
      Serial.println("[R3] waiting for NTP, skipping this sample (no fake timestamps)");
    } else {
      Reading r = sample();
      logSerial(r);
      ringPush(r);                       // always buffer first; flush removes it once the API confirms
      if (online) sendThingSpeak(r);
    }
  }
  if (online) flushBuffer();
  delay(50);
}
