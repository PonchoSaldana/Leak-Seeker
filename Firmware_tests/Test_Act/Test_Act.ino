#include <Arduino_RouterBridge.h>
#define Serial Monitor

#include "actuadores.h"

void setup() {
    Serial.begin(115200);
    while (!Serial);
    actuadores_setup();
    Serial.println("=== TEST M4 — ACTUADORES JOG ===");
    Serial.println("b → Bomba  |  1 → HV-01  |  2 → HV-02  |  x → TODO OFF");
    Serial.println("------------------------------------------------");
}

void loop() {
    if (Serial.available()) {
        char tecla = Serial.read();
        jog_procesar(tecla);

        // Feedback inmediato en Monitor
        Serial.print("CMD: "); Serial.print(tecla);
        Serial.print(" → B:");
        // Leer estado actual de pines para confirmar
        Serial.print(digitalRead(PIN_BOMBA) == RELAY_ON ? "ON " : "OFF");
        Serial.print(" HV01:");
        Serial.print(digitalRead(PIN_HV01)  == RELAY_ON ? "ON " : "OFF");
        Serial.print(" HV02:");
        Serial.println(digitalRead(PIN_HV02) == RELAY_ON ? "ON " : "OFF");
    }
}