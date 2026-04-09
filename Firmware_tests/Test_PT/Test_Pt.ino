#include <Arduino_RouterBridge.h>
#define Serial Monitor

#include "pt_sensor.h"

void setup() {
    Serial.begin(115200);
    while (!Serial);
    pt_setup();
    Serial.println("=== TEST M1 — PT-01 / PT-02 ===");
    Serial.println("raw01 | Vnodo01 | Vsens01 | kPa01 || raw02 | kPa02 | Delta");
}

void loop() {
    // Lecturas raw para diagnóstico
    int   raw01   = analogRead(PIN_PT01);
    int   raw02   = analogRead(PIN_PT02);

    // Conversión paso a paso PT-01
    float vn01    = pt_raw_a_vnodo(raw01);
    float vs01    = pt_vnodo_a_vsensor(vn01);
    float kpa01   = pt_vsensor_a_kpa(vs01);

    // Conversión directa PT-02
    float kpa02   = pt_leer_kpa(PIN_PT02);
    float delta   = pt_delta_kpa(kpa01, kpa02);

    Serial.print(raw01);   Serial.print(" | ");
    Serial.print(vn01, 3); Serial.print("V | ");
    Serial.print(vs01, 3); Serial.print("V | ");
    Serial.print(kpa01, 1);Serial.print(" kPa || ");
    Serial.print(raw02);   Serial.print(" | ");
    Serial.print(kpa02, 1);Serial.print(" kPa | Delta: ");
    Serial.print(delta, 1);Serial.println(" kPa");

    delay(200);
}