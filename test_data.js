const axios = require('axios');

const API_URL = 'http://localhost:3000/api/data';

function sendMockData() {
    const data = {
        vibration: Math.random() * 0.1,
        pressure: 40 + Math.random() * 10,
        flow: 10 + Math.random() * 5,
        alertVib: false,
        alertPres: false,
        alertFlow: false,
        valveClosed: false
    };

    // Simular alerta aleatoria cada cierto tiempo
    if (Math.random() > 0.8) {
        data.vibration = 2.5 + Math.random();
        data.alertVib = true;
    }

    if (Math.random() > 0.9) {
        data.valveClosed = true;
    }

    console.log('Enviando datos al servidor:', data);

    axios.post(API_URL, data)
        .catch(err => console.error('Error enviando datos (¿está el servidor encendido?):', err.message));
}

console.log('Iniciando simulador de datos real-time...');
setInterval(sendMockData, 2000);
