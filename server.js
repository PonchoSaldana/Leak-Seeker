const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: "*",
    }
});

app.use(express.json());

// ── Umbrales de alerta ────────────────────────────────────────
const THRESHOLDS = {
    vibrationHigh: 200,   // counts — umbral vibración
    pressureHigh: 500,    // kPa — presión alta
    pressureLow: 10,      // kPa — presión baja
    flowDeltaHigh: 0.3,   // L/min — diferencial de flujo
};

// ── Estado global ─────────────────────────────────────────────
let lastData = null;
let lastTimestamp = null;
let connectedClients = 0;

// ── Función para procesar datos crudos del MCU CSV ────────────
// Formato CSV del MCU: pt01,pt02,vt01,vt02,ft_delta,valveStatus
function parseCSV(csvLine) {
    const parts = csvLine.split(',').map(s => s.trim());
    if (parts.length < 6) return null;

    const pt01 = parseFloat(parts[0]);
    const pt02 = parseFloat(parts[1]);
    const vt01 = parseInt(parts[2], 10);
    const vt02 = parseInt(parts[3], 10);
    const ftDelta = parseFloat(parts[4]);
    const valveStatus = parseInt(parts[5], 10);

    if ([pt01, pt02, vt01, vt02, ftDelta].some(isNaN)) return null;

    const vibration = Math.max(Math.abs(vt01), Math.abs(vt02));
    const pressure = (pt01 + pt02) / 2;
    const flow = Math.abs(ftDelta);

    return {
        // Valores procesados para el dashboard
        vibration,
        pressure,
        flow,
        // Valores crudos para debug
        pt01, pt02, vt01, vt02, ftDelta,
        // Alertas
        alertVib: vibration > THRESHOLDS.vibrationHigh,
        alertPres: pressure > THRESHOLDS.pressureHigh || pressure < THRESHOLDS.pressureLow,
        alertFlow: Math.abs(ftDelta) > THRESHOLDS.flowDeltaHigh,
        // Estado de válvula (1 = cerrada por IA)
        valveClosed: valveStatus === 1,
        // Timestamp
        timestamp: Date.now(),
    };
}

// ── WebSockets ────────────────────────────────────────────────
io.on('connection', (socket) => {
    connectedClients++;
    console.log(`[WS] Conexión #${connectedClients}: ${socket.id}`);

    // Enviar último dato conocido para que el cliente no arranque vacío
    if (lastData) {
        socket.emit('sensor-data', lastData);
    }

    // Escuchar datos del bridge (MPU)
    socket.on('sensor-data', (data) => {
        lastData = { ...data, timestamp: Date.now() };
        lastTimestamp = Date.now();
        // Reenviar a TODOS los navegadores
        io.emit('sensor-data', lastData);
    });

    // Escuchar datos CSV crudos del bridge
    socket.on('sensor-csv', (csvLine) => {
        const parsed = parseCSV(csvLine);
        if (parsed) {
            lastData = parsed;
            lastTimestamp = Date.now();
            io.emit('sensor-data', parsed);
        }
    });

    socket.on('disconnect', () => {
        connectedClients--;
        console.log(`[WS] Desconexión: ${socket.id} (quedan ${connectedClients})`);
    });
});

// ── API Routes ────────────────────────────────────────────────
app.post('/api/sensor-data', (req, res) => {
    const data = req.body;
    if (!data) return res.status(400).json({ error: 'No data' });

    // Si viene como CSV string
    if (typeof data.csv === 'string') {
        const parsed = parseCSV(data.csv);
        if (!parsed) return res.status(400).json({ error: 'Invalid CSV' });
        lastData = parsed;
        lastTimestamp = Date.now();
        io.emit('sensor-data', parsed);
        return res.json({ ok: true });
    }

    // Si viene como JSON estructurado
    lastData = { ...data, timestamp: Date.now() };
    lastTimestamp = Date.now();
    io.emit('sensor-data', lastData);
    res.json({ ok: true });
});

app.get('/api/status', (req, res) => {
    res.json({
        clients: connectedClients,
        lastTimestamp,
        uptime: process.uptime(),
        lastData,
    });
});

// ── Servir archivos estáticos ────────────────────────────────
// Corregimos la ruta para incluir la carpeta 'web'
const WEB_PATH = path.join(__dirname, 'web', 'alert');
app.use(express.static(WEB_PATH));

// ── Servir la página principal (Fallback) ───────────────────
app.get('/', (req, res) => {
    res.sendFile(path.join(WEB_PATH, 'index.html'));
});

// ── Simulación — para probar sin hardware ─────────────────────
if (process.env.SIMULATE === 'true' || process.argv.includes('--simulate')) {
    console.log('[SIM] Modo simulación activado — generando datos ficticios');
    let t = 0;
    setInterval(() => {
        t += 0.12;
        const simData = {
            vibration: 80 + Math.sin(t * 2.1) * 60 + Math.random() * 20,
            pressure: 250 + Math.sin(t * 0.7) * 100 + Math.random() * 15,
            flow: 5 + Math.sin(t * 1.3) * 3 + Math.random() * 0.5,
            pt01: 260 + Math.sin(t * 0.7) * 100,
            pt02: 240 + Math.sin(t * 0.7) * 100,
            vt01: Math.floor(80 + Math.sin(t * 2.1) * 60),
            vt02: Math.floor(70 + Math.sin(t * 2.3) * 50),
            ftDelta: 0.1 + Math.sin(t * 1.3) * 0.15,
            alertVib: false,
            alertPres: false,
            alertFlow: false,
            valveClosed: false,
            timestamp: Date.now(),
        };
        // Simular alerta esporádica
        if (Math.random() < 0.02) simData.alertVib = true;
        if (Math.random() < 0.01) simData.valveClosed = true;

        lastData = simData;
        lastTimestamp = Date.now();
        io.emit('sensor-data', simData);
    }, 120); // ~8 Hz como el MCU real
}

const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`[SERVER] Leak-Seeker corriendo en puerto ${PORT}`);
    console.log(`[SERVER] Dashboard: http://localhost:${PORT}`);
});
