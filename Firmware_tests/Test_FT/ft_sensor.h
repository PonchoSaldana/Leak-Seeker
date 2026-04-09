// ============================================================
// ft_sensor.h — Módulo 3: Flujo YF-S201
// Los Tlaloques · SEG-01 · Genius Arena Hackathon 2026
//
// Hardware:   Arduino Uno Q / STM32U585 / Zephyr OS
// Pines:      D2=FT-01 INT0, D3=FT-02 INT1
// Divisor:    R1=10kΩ serie + R2=20kΩ a GND (5V→3.3V)
// Fórmula:    Q(L/min) = frecuencia_Hz / 7.5
//             Fuente: YF-S201 datasheet — 450 pulsos/litro
//                     → 7.5 pulsos/segundo por L/min
// Ventana:    1000ms — se actualiza cada segundo
// ============================================================

#pragma once

// ── Pines ─────────────────────────────────────────────────────
#define PIN_FT01  2    // D2 — INT0 — YF-S201 upstream
#define PIN_FT02  3    // D3 — INT1 — YF-S201 downstream

// ── Parámetros ────────────────────────────────────────────────
#define FT_VENTANA_MS        1000     // ms — ventana de conteo
#define FT_PULSOS_POR_LMIN   7.5f    // datasheet YF-S201
#define FT_DELTA_UMBRAL      0.3f    // L/min — umbral diferencial
                                     // ⚠️ provisional — calibrar en banco

// ── Contadores volátiles — modificados en ISR ─────────────────
volatile uint32_t _ft01_pulsos = 0;
volatile uint32_t _ft02_pulsos = 0;

// ── ISR — sin IRAM_ATTR (no es ESP32) ────────────────────────
void isr_ft01() { _ft01_pulsos++; }
void isr_ft02() { _ft02_pulsos++; }

// ── Variables de resultado ────────────────────────────────────
static float    _ft01_lmin     = 0.0f;
static float    _ft02_lmin     = 0.0f;
static uint32_t _ft_t_anterior = 0;

// ── Setup ─────────────────────────────────────────────────────
inline void ft_setup() {
    pinMode(PIN_FT01, INPUT);
    pinMode(PIN_FT02, INPUT);
    attachInterrupt(digitalPinToInterrupt(PIN_FT01), isr_ft01, RISING);
    attachInterrupt(digitalPinToInterrupt(PIN_FT02), isr_ft02, RISING);
    _ft_t_anterior = millis();
}

// ── Actualizar — llamar en loop() ────────────────────────────
// Devuelve true cada vez que completa una ventana de 1000ms
inline bool ft_actualizar() {
    uint32_t ahora = millis();
    if ((ahora - _ft_t_anterior) < FT_VENTANA_MS) return false;

    // Captura atómica — deshabilita interrupciones brevemente
    noInterrupts();
    uint32_t p01 = _ft01_pulsos;
    uint32_t p02 = _ft02_pulsos;
    _ft01_pulsos = 0;
    _ft02_pulsos = 0;
    interrupts();

    float dt_s = (ahora - _ft_t_anterior) / 1000.0f;
    _ft01_lmin = (p01 / dt_s) / FT_PULSOS_POR_LMIN;
    _ft02_lmin = (p02 / dt_s) / FT_PULSOS_POR_LMIN;
    _ft_t_anterior = ahora;
    return true;
}

// ── API pública ───────────────────────────────────────────────
inline float ft_leer_ft01()    { return _ft01_lmin; }
inline float ft_leer_ft02()    { return _ft02_lmin; }
inline float ft_delta_lmin()   { return _ft01_lmin - _ft02_lmin; }

inline bool ft_verificar_sobrevelocidad() {
    return (_ft01_lmin > 30.0f || _ft02_lmin > 30.0f);
}

inline bool ft_hay_fuga() {
    return (ft_delta_lmin() > FT_DELTA_UMBRAL);
}