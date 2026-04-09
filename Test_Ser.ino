#include <Arduino_RouterBridge.h>

#define PIN_VALVULA 12

#include "pt_sensor.h"
#include "vt_sensor.h"
#include "ft_sensor.h"
#include "serializacion.h"

void setup() {
    Serial1.begin(115200); 
    pinMode(PIN_VALVULA, INPUT); 
    
    analogReadResolution(12);
    pt_setup();
    vt_setup();
    ft_setup();
}

void loop() {
    float   pt01     = pt_leer_kpa(PIN_PT01);
    float   pt02     = pt_leer_kpa(PIN_PT02);
    int16_t vt01     = vt_leer_raw(PIN_VT01);
    int16_t vt02     = vt_leer_raw(PIN_VT02);
    ft_actualizar();
    float   ft_delta = ft_delta_lmin();

    bool valveStatus = digitalRead(PIN_VALVULA);

    Serial1.print(pt01, 2);    Serial1.print(",");
    Serial1.print(pt02, 2);    Serial1.print(",");
    Serial1.print(vt01);       Serial1.print(",");
    Serial1.print(vt02);       Serial1.print(",");
    Serial1.print(ft_delta, 3); Serial1.print(",");
    Serial1.println(valveStatus);

    // Muestreo a 100Hz (10ms) para fluidez absoluta
    delay(10); 
}
