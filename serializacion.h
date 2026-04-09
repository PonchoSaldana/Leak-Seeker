// ============================================================
// serializacion.h — Módulo 5: UART MCU→MPU CSV
// Los Tlaloques · SEG-01 · Genius Arena Hackathon 2026
//
// Hardware:   Arduino Uno Q / STM32U585 / Zephyr OS
// Serial1:    UART interna MCU→MPU — datos para Edge Impulse
// Monitor:    Debug en PC — con etiquetas
// Formato:    pt01,pt02,vt01,vt02,ft_delta\n
//             5 canales, 50 Hz, sin etiquetas en Serial1
// ============================================================

#pragma once

// ── Parámetros ────────────────────────────────────────────────
#define SER_BAUD_SERIAL1   115200   // UART interna MCU→MPU
#define SER_INTERVALO_MS   20       // 1000ms / 50Hz = 20ms

// ── Timestamp interno ─────────────────────────────────────────
static uint32_t _ser_t_anterior = 0;

// ── Setup ─────────────────────────────────────────────────────
inline void ser_setup() {
    Serial1.begin(SER_BAUD_SERIAL1);
    _ser_t_anterior = millis();
}

// ── Enviar trama CSV — llamar en loop() ──────────────────────
// Devuelve true cuando envía una trama
inline bool ser_enviar(float pt01, float pt02,
                       int16_t vt01, int16_t vt02,
                       float ft_delta) {

    uint32_t ahora = millis();
    if ((ahora - _ser_t_anterior) < SER_INTERVALO_MS) return false;
    _ser_t_anterior = ahora;

    // Serial1 → MPU → edge-impulse-data-forwarder
    // Formato estricto: sin espacios, sin etiquetas, \n al final
    Serial1.print(pt01,    2); Serial1.print(',');
    Serial1.print(pt02,    2); Serial1.print(',');
    Serial1.print(vt01);       Serial1.print(',');
    Serial1.print(vt02);       Serial1.print(',');
    Serial1.println(ft_delta, 3);

    return true;
}

// ── Echo en Monitor — solo para debug ────────────────────────
inline void ser_debug(float pt01, float pt02,
                      int16_t vt01, int16_t vt02,
                      float ft_delta) {
    Serial.print("PT01:"); Serial.print(pt01, 2);
    Serial.print(" PT02:"); Serial.print(pt02, 2);
    Serial.print(" VT01:"); Serial.print(vt01);
    Serial.print(" VT02:"); Serial.print(vt02);
    Serial.print(" FT_D:"); Serial.println(ft_delta, 3);
}