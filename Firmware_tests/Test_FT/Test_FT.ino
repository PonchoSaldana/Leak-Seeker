#include <Arduino_RouterBridge.h>
#define Serial Monitor

#include "ft_sensor.h"

void setup() {
    Serial.begin(115200);
    while (!Serial);
    ft_setup();
    Serial.println("=== TEST M3 — FT-01 / FT-02 ===");
    Serial.println("p01 | p02 | FT01 L/min | FT02 L/min | Delta | Estado");
    Serial.println("-------------------------------------------------------");
    Serial.println("TEST EN SECO: toca D2/D3 con cable 3.3V para simular pulsos");
}

void loop() {
    if (ft_actualizar()) {
        // Mostrar conteos raw para diagnóstico en seco
        Serial.print("FT01: "); Serial.print(_ft01_lmin, 2);
        Serial.print(" L/min | FT02: "); Serial.print(_ft02_lmin, 2);
        Serial.print(" L/min | Delta: "); Serial.print(ft_delta_lmin(), 2);
        Serial.print(" L/min");
        if (ft_verificar_sobrevelocidad()) Serial.print(" *** SOBREVELOCIDAD ***");
        if (ft_hay_fuga())                 Serial.print(" *** FUGA DETECTADA ***");
        Serial.println();
    }
}