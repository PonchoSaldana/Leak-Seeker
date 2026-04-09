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
app.use(express.static(path.join(__dirname, 'alert')));

// Configuración de WebSockets de alta velocidad
io.on('connection', (socket) => {
    console.log('Nueva conexión detectada:', socket.id);

    // Escuchar datos que vienen del MPU (como cliente socket)
    socket.on('sensor-data', (data) => {
        // Reenviar los datos a TODOS los navegadores abiertos
        io.emit('sensor-data', data);
    });

    socket.on('disconnect', () => {
        console.log('Conexión cerrada:', socket.id);
    });
});

// Servir la página principal
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'alert', 'index.html'));
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`Servidor corriendo en puerto ${PORT}`);
});
