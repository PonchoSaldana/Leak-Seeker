#!/usr/bin/env python3
"""
============================================================
bridge.py — Puente Serial MCU → Servidor Web (Socket.IO)
Los Tlaloques · SEG-01 · Genius Arena Hackathon 2026

Lee datos CSV del MCU por Serial y los envía al servidor
Leak-Seeker en tiempo real vía WebSocket (Socket.IO).

Uso en el MPU (Raspberry Pi / Linux SBC):
    python3 bridge.py
    python3 bridge.py --port /dev/ttyACM0 --server https://leak-seeker.onrender.com

Dependencias:
    pip install pyserial python-socketio[client] websocket-client
============================================================
"""

import argparse
import sys
import time
import threading
import serial
import serial.tools.list_ports
import socketio

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN POR DEFECTO
# ══════════════════════════════════════════════════════════════
DEFAULT_PORT   = "/dev/ttyACM0"   # Puerto serial del MCU
DEFAULT_BAUD   = 9600             # Baudrate (debe coincidir con Test_Ser.ino)
DEFAULT_SERVER = "https://leak-seeker.onrender.com"  # URL del servidor

# Umbrales de alerta (deben coincidir con server.js)
UMBRAL_VIB   = 200    # counts
UMBRAL_PRES_H = 500   # kPa
UMBRAL_PRES_L = 10    # kPa
UMBRAL_FLOW  = 0.3    # L/min

# ══════════════════════════════════════════════════════════════
# ARGUMENTOS CLI
# ══════════════════════════════════════════════════════════════
parser = argparse.ArgumentParser(
    description="Puente Serial → Socket.IO para Leak-Seeker"
)
parser.add_argument(
    "-p", "--port",
    default=DEFAULT_PORT,
    help=f"Puerto serial del MCU (default: {DEFAULT_PORT})"
)
parser.add_argument(
    "-b", "--baud",
    type=int,
    default=DEFAULT_BAUD,
    help=f"Velocidad del puerto serial (default: {DEFAULT_BAUD})"
)
parser.add_argument(
    "-s", "--server",
    default=DEFAULT_SERVER,
    help=f"URL del servidor Leak-Seeker (default: {DEFAULT_SERVER})"
)
parser.add_argument(
    "--raw",
    action="store_true",
    help="Enviar CSV crudo sin parsear (el servidor lo parsea)"
)
parser.add_argument(
    "--list-ports",
    action="store_true",
    help="Listar puertos seriales disponibles y salir"
)
args = parser.parse_args()

# ══════════════════════════════════════════════════════════════
# LISTAR PUERTOS
# ══════════════════════════════════════════════════════════════
if args.list_ports:
    print("\n📡 Puertos seriales disponibles:")
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("   (ninguno detectado)")
    for p in ports:
        print(f"   {p.device} — {p.description}")
    sys.exit(0)

# ══════════════════════════════════════════════════════════════
# BANNER
# ══════════════════════════════════════════════════════════════
print("""
╔══════════════════════════════════════════════════╗
║          💧 Leak-Seeker Bridge v1.0             ║
║          Serial MCU → Servidor Web              ║
╚══════════════════════════════════════════════════╝
""")
print(f"  Puerto serial : {args.port} @ {args.baud} baud")
print(f"  Servidor      : {args.server}")
print(f"  Modo          : {'CSV crudo' if args.raw else 'JSON parseado'}")
print()

# Mostrar puertos disponibles
print("📡 Puertos detectados:")
for p in serial.tools.list_ports.comports():
    marker = " ← SELECCIONADO" if p.device == args.port else ""
    print(f"   {p.device} — {p.description}{marker}")
print()

# ══════════════════════════════════════════════════════════════
# ESTADÍSTICAS
# ══════════════════════════════════════════════════════════════
stats = {
    "enviados": 0,
    "errores_parse": 0,
    "errores_ws": 0,
    "inicio": time.time(),
}

# ══════════════════════════════════════════════════════════════
# SOCKET.IO — Conexión al servidor
# ══════════════════════════════════════════════════════════════
sio = socketio.Client(
    reconnection=True,
    reconnection_delay=1,
    reconnection_delay_max=5,
    logger=False,
)

ws_connected = False

@sio.event
def connect():
    global ws_connected
    ws_connected = True
    print("✅ Conectado al servidor")

@sio.event
def disconnect():
    global ws_connected
    ws_connected = False
    print("❌ Desconectado del servidor — reintentando...")

@sio.event
def connect_error(data):
    print(f"⚠️  Error de conexión: {data}")

def conectar_servidor():
    """Intenta conectar al servidor con reintentos."""
    while True:
        try:
            print(f"🔄 Conectando a {args.server}...")
            sio.connect(args.server, transports=["websocket"])
            break
        except Exception as e:
            print(f"⚠️  No se pudo conectar: {e}")
            print("   Reintentando en 3 segundos...")
            time.sleep(3)

# ══════════════════════════════════════════════════════════════
# PARSEO CSV → JSON
# ══════════════════════════════════════════════════════════════
def parse_csv(line):
    """
    Parsea una línea CSV del MCU.
    Formato: pt01,pt02,vt01,vt02,ft_delta,valveStatus
    Retorna dict o None si hay error.
    """
    try:
        parts = line.strip().split(",")
        if len(parts) < 6:
            return None

        pt01   = float(parts[0])
        pt02   = float(parts[1])
        vt01   = int(parts[2])
        vt02   = int(parts[3])
        ft_delta = float(parts[4])
        valve  = int(parts[5])

        vibration = max(abs(vt01), abs(vt02))
        pressure  = (pt01 + pt02) / 2.0
        flow      = abs(ft_delta)

        return {
            # Valores procesados
            "vibration": vibration,
            "pressure": pressure,
            "flow": flow,
            # Valores crudos
            "pt01": pt01,
            "pt02": pt02,
            "vt01": vt01,
            "vt02": vt02,
            "ftDelta": ft_delta,
            # Alertas
            "alertVib": vibration > UMBRAL_VIB,
            "alertPres": pressure > UMBRAL_PRES_H or pressure < UMBRAL_PRES_L,
            "alertFlow": abs(ft_delta) > UMBRAL_FLOW,
            # Válvula (1 = cerrada)
            "valveClosed": valve == 1,
            # Timestamp
            "timestamp": int(time.time() * 1000),
        }
    except (ValueError, IndexError) as e:
        return None

# ══════════════════════════════════════════════════════════════
# HEARTBEAT — imprime estadísticas cada 10s
# ══════════════════════════════════════════════════════════════
def heartbeat():
    while True:
        time.sleep(10)
        elapsed = time.time() - stats["inicio"]
        freq = stats["enviados"] / elapsed if elapsed > 0 else 0
        ws_status = "✅ WS" if ws_connected else "❌ WS"
        print(
            f"[HEARTBEAT] {ws_status} | "
            f"Enviados: {stats['enviados']} | "
            f"Errores: {stats['errores_parse']} parse, {stats['errores_ws']} ws | "
            f"Freq: {freq:.1f} pkt/s | "
            f"Uptime: {int(elapsed)}s"
        )

heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
heartbeat_thread.start()

# ══════════════════════════════════════════════════════════════
# CONEXIÓN SERIAL + LOOP PRINCIPAL
# ══════════════════════════════════════════════════════════════
def main():
    # 1. Conectar al servidor WebSocket
    ws_thread = threading.Thread(target=conectar_servidor, daemon=True)
    ws_thread.start()

    # 2. Esperar brevemente a que se conecte
    time.sleep(2)

    # 3. Loop: abrir serial → leer → enviar
    while True:
        try:
            print(f"🔌 Abriendo puerto serial {args.port}...")
            ser = serial.Serial(
                port=args.port,
                baudrate=args.baud,
                timeout=1,
            )
            print(f"✅ Puerto serial abierto: {args.port}")

            while True:
                raw = ser.readline()
                if not raw:
                    continue

                try:
                    line = raw.decode("utf-8", errors="ignore").strip()
                except Exception:
                    continue

                if not line:
                    continue

                # Enviar al servidor
                if not ws_connected:
                    continue

                try:
                    if args.raw:
                        # Modo crudo: el servidor parsea
                        sio.emit("sensor-csv", line)
                    else:
                        # Modo parseado: enviamos JSON
                        data = parse_csv(line)
                        if data is None:
                            stats["errores_parse"] += 1
                            continue
                        sio.emit("sensor-data", data)

                    stats["enviados"] += 1

                    # Log cada 50 paquetes para no saturar la consola
                    if stats["enviados"] % 50 == 0:
                        print(f"📤 [{stats['enviados']}] {line}")

                except Exception as e:
                    stats["errores_ws"] += 1
                    if stats["errores_ws"] % 10 == 1:
                        print(f"⚠️  Error enviando: {e}")

        except serial.SerialException as e:
            print(f"⚠️  Error serial: {e}")
            print("   Reintentando en 3 segundos...")
            time.sleep(3)

        except KeyboardInterrupt:
            print("\n\n🛑 Detenido por el usuario")
            elapsed = time.time() - stats["inicio"]
            print(f"   Paquetes enviados: {stats['enviados']}")
            print(f"   Tiempo activo: {int(elapsed)}s")
            break

    # Limpiar
    try:
        sio.disconnect()
    except Exception:
        pass

if __name__ == "__main__":
    main()
