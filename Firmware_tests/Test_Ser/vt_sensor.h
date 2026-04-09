// ============================================================
// vt_sensor.h — Módulo 2: Acústico Piezo + LM386
// Los Tlaloques · SEG-01 · Genius Arena Hackathon 2026
//
// Hardware:   Arduino Uno Q / STM32U585 / Zephyr OS
// ADC:        12 bits, Vref 3.3V
// Bias DC:    ~1.64V salida LM386 → ~1.09V en pin MCU
// Detección:  amplitud = max - min en ventana N muestras
//             Inmune al bias DC — no depende del set-point
// Umbral:     VT_UMBRAL_AMP = 30 counts (PROVISIONAL)
//             ⚠️ Ajustar con banco con agua antes de captura
// ============================================================

#pragma once

// ── Pines ────────────────────────────────────────────────────
#define PIN_VT01  A2   // Piezo + LM386 upstream  (referencia)
#define PIN_VT02  A3   // Piezo + LM386 downstream (zona fuga)

// ── Parámetros de ventana ────────────────────────────────────
#define VT_N_MUESTRAS     100     // Muestras por ventana
#define VT_DELAY_US       200     // µs entre muestras → ventana ~20ms
                                  // Intuición técnica — no hay norma
                                  // para este sensor en PVC DN15

// ── Umbral de detección ──────────────────────────────────────
#define VT_UMBRAL_AMP     50      // counts — PROVISIONAL
                                  // ⚠️ Calibrar en banco con agua

// ── Setup ─────────────────────────────────────────────────────
inline void vt_setup() {
    analogReadResolution(12);
}

// ── Leer raw instantáneo ──────────────────────────────────────
inline int16_t vt_leer_raw(uint8_t pin) {
    return (int16_t)analogRead(pin);
}

// ── Amplitud pico a pico en ventana N muestras ───────────────
inline uint16_t vt_amplitud(uint8_t pin) {
    int16_t vmax = -32768;
    int16_t vmin =  32767;
    for (uint16_t i = 0; i < VT_N_MUESTRAS; i++) {
        int16_t v = (int16_t)analogRead(pin);
        if (v > vmax) vmax = v;
        if (v < vmin) vmin = v;
        delayMicroseconds(VT_DELAY_US);
    }
    return (uint16_t)(vmax - vmin);
}

// ── Detección binaria sobre umbral ───────────────────────────
inline bool vt_hay_senal(uint8_t pin) {
    return vt_amplitud(pin) > VT_UMBRAL_AMP;
}