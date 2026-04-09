// ============================================================
// bridge.js — Puente Serial → Socket.IO
// Lee datos CSV del MCU vía Serial y los envía al servidor
// Ejecutar en el MPU (Raspberry Pi / Linux SBC)
//
// Uso:
//   node bridge.js --port COM3
//   node bridge.js --port /dev/ttyACM0 --server https://mi-server.onrender.com
// ============================================================

const { io } = require('socket.io-client');

// ── Argumentos ────────────────────────────────────────────────
const args = process.argv.slice(2);
function getArg(flag, fallback) {
    const idx = args.indexOf(flag);
    return idx !== -1 && args[idx + 1] ? args[idx + 1] : fallback;
}

const SERIAL_PORT = getArg('--port', process.env.SERIAL_PORT || 'COM3');
const BAUD_RATE = parseInt(getArg('--baud', '9600'), 10);
const SERVER_URL = getArg('--server', process.env.SERVER_URL || 'http://localhost:3000');

console.log(`[BRIDGE] Puerto serial: ${SERIAL_PORT} @ ${BAUD_RATE} baud`);
console.log(`[BRIDGE] Servidor destino: ${SERVER_URL}`);

// ── Conexión Socket.IO al servidor ────────────────────────────
const socket = io(SERVER_URL, {
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: Infinity,
});

socket.on('connect', () => {
    console.log(`[BRIDGE] Conectado al servidor: ${socket.id}`);
});

socket.on('disconnect', () => {
    console.log('[BRIDGE] Desconectado del servidor — reintentando...');
});

socket.on('connect_error', (err) => {
    console.error(`[BRIDGE] Error de conexión: ${err.message}`);
});

// ── Lectura del puerto serial ─────────────────────────────────
let serialConnected = false;

async function initSerial() {
    try {
        const { SerialPort } = require('serialport');
        const { ReadlineParser } = require('@serialport/parser-readline');

        const port = new SerialPort({
            path: SERIAL_PORT,
            baudRate: BAUD_RATE,
            autoOpen: false,
        });

        const parser = port.pipe(new ReadlineParser({ delimiter: '\n' }));

        port.open((err) => {
            if (err) {
                console.error(`[SERIAL] Error abriendo ${SERIAL_PORT}: ${err.message}`);
                console.log('[SERIAL] Reintentando en 3 segundos...');
                setTimeout(initSerial, 3000);
                return;
            }
            serialConnected = true;
            console.log(`[SERIAL] Puerto ${SERIAL_PORT} abierto exitosamente`);
        });

        parser.on('data', (line) => {
            const trimmed = line.trim();
            if (!trimmed) return;

            // Enviar CSV crudo — el servidor lo parsea
            if (socket.connected) {
                socket.emit('sensor-csv', trimmed);
            }
        });

        port.on('error', (err) => {
            console.error(`[SERIAL] Error: ${err.message}`);
            serialConnected = false;
        });

        port.on('close', () => {
            console.log('[SERIAL] Puerto cerrado — reintentando en 3 segundos...');
            serialConnected = false;
            setTimeout(initSerial, 3000);
        });

    } catch (e) {
        console.error(`[SERIAL] No se pudo cargar 'serialport': ${e.message}`);
        console.log('[SERIAL] Instala con: npm install serialport');
        process.exit(1);
    }
}

initSerial();

// ── Heartbeat ─────────────────────────────────────────────────
setInterval(() => {
    const status = serialConnected ? '✓ Serial OK' : '✗ Serial OFF';
    const ws = socket.connected ? '✓ WS OK' : '✗ WS OFF';
    console.log(`[HEARTBEAT] ${status} | ${ws}`);
}, 10000);
