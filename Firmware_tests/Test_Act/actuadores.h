// ============================================================
// actuadores.h — Módulo 4: Bomba + Solenoides + Jog
// Los Tlaloques · SEG-01 · Genius Arena Hackathon 2026
//
// Hardware:   Arduino Uno Q / STM32U585 / Zephyr OS
// Actuadores: Relay 8 canales — lógica ACTIVA EN LOW
// Pines:      D4=bomba, D9=HV-01 solenoide, D10=HV-02 solenoide
// Fuente:     12V → solenoides/bomba vía relay
// ============================================================

#pragma once

// ── Pines ─────────────────────────────────────────────────────
#define PIN_BOMBA   4    // D4 — relay K1 — P-01
#define PIN_HV01    9    // D9 — relay K2 — solenoide entrada
#define PIN_HV02    10   // D10 — relay K3 — solenoide salida

// ── Lógica del relay ──────────────────────────────────────────
// Módulo relay de 8 canales: activa con LOW, desactiva con HIGH
#define RELAY_ON    LOW
#define RELAY_OFF   HIGH

// ── Setup ─────────────────────────────────────────────────────
inline void actuadores_setup() {
    pinMode(PIN_BOMBA, OUTPUT);
    pinMode(PIN_HV01,  OUTPUT);
    pinMode(PIN_HV02,  OUTPUT);
    // Estado inicial — todo apagado
    digitalWrite(PIN_BOMBA, RELAY_OFF);
    digitalWrite(PIN_HV01,  RELAY_OFF);
    digitalWrite(PIN_HV02,  RELAY_OFF);
}

// ── Control individual ────────────────────────────────────────
inline void bomba_on()  { digitalWrite(PIN_BOMBA, RELAY_ON);  }
inline void bomba_off() { digitalWrite(PIN_BOMBA, RELAY_OFF); }
inline void hv01_on()   { digitalWrite(PIN_HV01,  RELAY_ON);  }
inline void hv01_off()  { digitalWrite(PIN_HV01,  RELAY_OFF); }
inline void hv02_on()   { digitalWrite(PIN_HV02,  RELAY_ON);  }
inline void hv02_off()  { digitalWrite(PIN_HV02,  RELAY_OFF); }

// ── Jog — procesa tecla desde Monitor ────────────────────────
// Comandos:
//   b → bomba ON/OFF toggle
//   1 → HV-01 ON/OFF toggle
//   2 → HV-02 ON/OFF toggle
//   x → todo OFF (emergencia)
inline void jog_procesar(char tecla) {
    static bool estado_bomba = false;
    static bool estado_hv01  = false;
    static bool estado_hv02  = false;

    switch (tecla) {
        case 'b':
            estado_bomba = !estado_bomba;
            estado_bomba ? bomba_on() : bomba_off();
            break;
        case '1':
            estado_hv01 = !estado_hv01;
            estado_hv01 ? hv01_on() : hv01_off();
            break;
        case '2':
            estado_hv02 = !estado_hv02;
            estado_hv02 ? hv02_on() : hv02_off();
            break;
        case 'x':
            estado_bomba = false;
            estado_hv01  = false;
            estado_hv02  = false;
            bomba_off(); hv01_off(); hv02_off();
            break;
        default:
            break;
    }
}