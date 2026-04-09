#include <Arduino_RouterBridge.h>
#define Serial Monitor

#include "pt_sensor.h"
#include "vt_sensor.h"
#include "ft_sensor.h"
#include "serializacion.h"

void setup() {
    Serial.begin(115200);
    while (!Serial);
    analogReadResolution(12);
    pt_setup();
    vt_setup();
    ft_setup();
    ser_setup();
    Serial.println("=== TEST M5 — SERIALIZACION CSV ===");
    Serial.println("PT01 | PT02 | VT01 | VT02 | FT_DELTA");
    Serial.println("--------------------------------------");
}

void loop() {
    // Leer sensores
    float   pt01     = pt_leer_kpa(PIN_PT01);
    float   pt02     = pt_leer_kpa(PIN_PT02);
    int16_t vt01     = vt_leer_raw(PIN_VT01);
    int16_t vt02     = vt_leer_raw(PIN_VT02);
    ft_actualizar();
    float   ft_delta = ft_delta_lmin();

    // Enviar a MPU si toca la ventana de 20ms
    if (ser_enviar(pt01, pt02, vt01, vt02, ft_delta)) {
        // Echo en Monitor para verificar
        ser_debug(pt01, pt02, vt01, vt02, ft_delta);
    }
}