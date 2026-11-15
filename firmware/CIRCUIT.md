# Circuit and parts (previa)

| Part | Qty | Connection |
|---|---|---|
| ESP32 dev board | 1 | USB power |
| DHT22 (AM2302) | 1 | VCC -> 3V3, GND -> GND, DATA -> GPIO 4, 10 kΩ between DATA and 3V3 |
| LDR (photoresistor) | 1 | 3V3 -> LDR -> GPIO 34 -> 10 kΩ -> GND |
| Breadboard + jumpers | - | fixed mounting |

```
3V3 ──┬─────────── DHT22 VCC            3V3 ── LDR ──┬── GPIO34
      └─[10k]─┐                                       └─[10k]── GND
GPIO4 ────────┴── DHT22 DATA
GND ──────────── DHT22 GND
```

GPIO 34 is input-only and on ADC1, so it keeps working while Wi-Fi is active.
**TODO before delivery:** export the same circuit from Wokwi (`firmware/wokwi/diagram.json`) and add a photo of the real assembly.
