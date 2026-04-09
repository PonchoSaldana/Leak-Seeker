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
app.use(express.static(__dirname));

// Endpoint para recibir datos desde el MCU o un bridge
app.post('/api/data', (req, res) => {
    const data = req.body;
    
    // Aquí podrías correr tu modelo entrenado si es un modelo de JS/Python
    // O simplemente recibir la decisión ya tomada por el MCU
    
    // Emitir a todos los clientes web conectados
    io.emit('sensor-data', data);
    
    res.status(200).send({ status: 'ok' });
});

// Servir la página principal
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Servidor corriendo en puerto ${PORT}`);
});
