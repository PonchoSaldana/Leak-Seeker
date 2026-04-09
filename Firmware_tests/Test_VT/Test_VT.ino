#include <Arduino_RouterBridge.h>
#define Serial Monitor

#include "vt_sensor.h"

// ── Modo de operación ─────────────────────────────────────────
// Fase A: imprime raw + amplitud sin umbral → para calibrar pot
//         y observar counts al golpear el tubo
// Fase B: cuando VT_UMBRAL_AMP esté ajustado, observar [SEÑAL]

void setup() {
    Serial.begin(115200);
    while (!Serial);
    vt_setup();
    Serial.println("=== TEST M2 — VT-01 / VT-02 ===");
    Serial.println("raw01 | bias01 | amp01 | VT01 || raw02 | bias02 | amp02 | VT02");
    Serial.println("--------------------------------------------------------------");
}

void loop() {
    // Raw instantáneo (una muestra — para ver bias DC)
    int16_t raw01 = vt_leer_raw(PIN_VT01);
    int16_t raw02 = vt_leer_raw(PIN_VT02);

    // Amplitud ventana completa (bloquea ~20ms cada canal)
    uint16_t amp01 = vt_amplitud(PIN_VT01);
    uint16_t amp02 = vt_amplitud(PIN_VT02);

    // VT01
    Serial.print(raw01); Serial.print(" | ");
    Serial.print(raw01 * (3300.0f / 4095.0f), 0); Serial.print("mV | ");
    Serial.print(amp01); Serial.print(" cts | ");
    Serial.print(amp01 > VT_UMBRAL_AMP ? "[SEÑAL]" : "[quiet]");
    Serial.print(" || ");

    // VT02
    Serial.print(raw02); Serial.print(" | ");
    Serial.print(raw02 * (3300.0f / 4095.0f), 0); Serial.print("mV | ");
    Serial.print(amp02); Serial.print(" cts | ");
    Serial.println(amp02 > VT_UMBRAL_AMP ? "[SEÑAL]" : "[quiet]");

    delay(100);
}