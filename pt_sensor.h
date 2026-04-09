// ============================================================
// pt_sensor.h — Módulo 1: Presión MPX5700AP
// Los Tlaloques · SEG-01 · Genius Arena Hackathon 2026
//
// Hardware:   Arduino Uno Q / STM32U585 / Zephyr OS
// ADC:        12 bits, Vref 3.3V (NO 5V tolerante)
// Divisor:    R1=10kΩ serie + R2=20kΩ a GND
//             Vnode_max = 4.7V × (20/30) = 3.133V ✓
// Fuente TF:  NXP MPX5700AP datasheet, ec. (1)
//             Vout = Vs × (0.01293 × P_kPa + 0.04)
// ============================================================

#pragma once

// ── Pines ────────────────────────────────────────────────────
#define PIN_PT01  A0   // MPX5700AP upstream
#define PIN_PT02  A1   // MPX5700AP downstream

// ── Constantes de conversión ─────────────────────────────────
#define ADC_BITS        12
#define ADC_MAX         4095.0f          // 2^12 - 1
#define VREF            3.3f             // Volts — rail 3.3V del Uno Q
#define DIVISOR_FACTOR  (4.7f / 3.13f)  // Recupera Vsensor desde Vnode
#define VS              5.0f             // Alimentación del MPX5700AP
#define MPX_SLOPE       0.001293f         // V/kPa / Vs  (datasheet NXP)
#define MPX_OFFSET      0.04f            // offset adimensional (datasheet NXP)
#define MPX_PMIN_KPA    0.0f
#define MPX_PMAX_KPA    700.0f

// ── Setup ─────────────────────────────────────────────────────
inline void pt_setup() {
    analogReadResolution(ADC_BITS);   // 12 bits — STM32U585 lo soporta nativamente
}

// ── Raw → Voltaje en el nodo del divisor ─────────────────────
inline float pt_raw_a_vnodo(int raw) {
    return raw * (VREF / ADC_MAX);
}

// ── Voltaje nodo → Voltaje sensor (deshace el divisor) ───────
inline float pt_vnodo_a_vsensor(float vnodo) {
    return vnodo * DIVISOR_FACTOR;
}

// ── Voltaje sensor → Presión kPa (TF MPX5700AP, NXP DS) ─────
inline float pt_vsensor_a_kpa(float vsensor) {
    float p = (vsensor / VS - MPX_OFFSET) / MPX_SLOPE;
    // Clamp al rango del sensor
    if (p < MPX_PMIN_KPA) p = MPX_PMIN_KPA;
    if (p > MPX_PMAX_KPA) p = MPX_PMAX_KPA;
    return p;
}

// ── API pública principal ─────────────────────────────────────
inline float pt_leer_kpa(uint8_t pin) {
    int   raw     = analogRead(pin);
    float vnodo   = pt_raw_a_vnodo(raw);
    float vsensor = pt_vnodo_a_vsensor(vnodo);
    return pt_vsensor_a_kpa(vsensor);
}

// ── Diferencial upstream − downstream ────────────────────────
inline float pt_delta_kpa(float pt01, float pt02) {
    return pt01 - pt02;   // positivo = caída normal; negativo = anómalo
}