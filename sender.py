import serial
import requests
import time
import re

# === CONFIGURACIÓN FINAL LEAK-SEEKER ===
URL_RENDER = "https://leak-seeker.onrender.com/api/data"
PUERTO_SERIAL = "/dev/ttyHS1"
BAUD_RATE = 115200 # Velocidad alta para tiempo real

# Usamos Session para mantener la conexión abierta (Ultra-latencia baja)
session = requests.Session()

def clean_value(val):
    # Elimina ruidos de inicio de línea (como los 7s o 6s vistos anteriormente)
    return re.sub(r'^[768]+', '', val)

def start_bridge():
    while True:
        arduino = None
        try:
            print(f"🚀 Puente Leak-Seeker Activo en {PUERTO_SERIAL} ({BAUD_RATE} bps)")
            arduino = serial.Serial(PUERTO_SERIAL, BAUD_RATE, timeout=0.1)
            arduino.reset_input_buffer()
            
            last_send_time = 0
            
            while True:
                if arduino.in_waiting > 0:
                    try:
                        line = arduino.readline().decode('utf-8', errors='ignore').strip()
                        parts = line.split(',')
                        
                        if len(parts) == 6:
                            current_time = time.time()
                            # Solo enviamos a la web cada 0.1s para evitar saturación,
                            # permitiendo una visualización fluida de 10 FPS
                            if current_time - last_send_time > 0.1:
                                try:
                                    p = float(clean_value(parts[0]))
                                    v = float(clean_value(parts[2]))
                                    f = float(clean_value(parts[4]))
                                    valve = int(parts[5]) == 1 # 1 = Cerrada, 0 = Abierta
                                    
                                    payload = {
                                        "pressure": p,
                                        "vibration": v,
                                        "flow": f,
                                        "alertVib": v > 700,
                                        "valveClosed": valve
                                    }
                                    
                                    # Envío ultra-rápido por Keep-Alive
                                    session.post(URL_RENDER, json=payload, timeout=2)
                                    last_send_time = current_time
                                    status = "CERRADA" if valve else "ABIERTA"
                                    print(f"⚡ Live: P:{p} | V:{v} | Valve: {status}")
                                except:
                                    pass
                    except:
                        pass
                time.sleep(0.005) # Ciclo de alta frecuencia

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if arduino: arduino.close()
        
        print("⏳ Reintentando conexión...")
        time.sleep(2)

if __name__ == "__main__":
    start_bridge()
