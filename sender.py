import serial
import socketio
import time
import re

# === CONFIGURACIÓN ULTRA-REALTIME LEAK-SEEKER ===
URL_RENDER = "https://leak-seeker.onrender.com"
PUERTO_SERIAL = "/dev/ttyHS1"
BAUD_RATE = 115200

# Creamos el cliente de Socket.io (Mantiene el túnel abierto)
sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=1)

def clean_value(val):
    return re.sub(r'^[768]+', '', val)

@sio.event
def connect():
    print("🚀 ¡SISTEMA EN LÍNEA! Conectado a Render en tiempo real.")

@sio.event
def disconnect():
    print("🔌 Conexión perdida. Reintentando...")

def start_bridge():
    arduino = None
    try:
        # Intentar conectar al servidor de Render
        print(f"🔗 Intentando conectar a {URL_RENDER}...")
        sio.connect(URL_RENDER)
        
        # Abrir puerto Serial
        print(f"📡 Abriendo puerto {PUERTO_SERIAL}...")
        arduino = serial.Serial(PUERTO_SERIAL, BAUD_RATE, timeout=0.1)
        arduino.reset_input_buffer()
        
        while True:
            if arduino.in_waiting > 0:
                try:
                    line = arduino.readline().decode('utf-8', errors='ignore').strip()
                    parts = line.split(',')
                    
                    if len(parts) >= 5:
                        p = float(clean_value(parts[0]))
                        v = float(clean_value(parts[2]))
                        f = float(clean_value(parts[4]))
                        valve = (int(parts[5]) == 1) if len(parts) == 6 else False
                        
                        data = {
                            "pressure": p,
                            "vibration": v,
                            "flow": f,
                            "alertVib": v > 700,
                            "valveClosed": valve
                        }
                        
                        # EMITIR POR WEBSOCKET (Sin esperas, sin headers, tiempo real puro)
                        sio.emit('sensor-data', data)
                        print(f"⚡ Live: P:{p} | V:{v} | Valve: {'OFF' if valve else 'ON'}")
                except Exception as e:
                    # Ignorar errores de parseo puntuales
                    pass
            
            time.sleep(0.001)

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        time.sleep(2)
        start_bridge()
    finally:
        if arduino:
            arduino.close()

if __name__ == "__main__":
    start_bridge()
