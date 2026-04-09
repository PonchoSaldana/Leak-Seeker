#!/usr/bin/env python3
"""
============================================================
bridge.py — Puente Serial MCU → Servidor Web (Socket.IO)
Los Tlaloques · SEG-01 · Genius Arena Hackathon 2026

Uso:
    python3 bridge.py
    python3 bridge.py --port /dev/ttyHS1 --server https://leak-seeker.onrender.com
    python3 bridge.py --list-ports

Dependencias:
    pip install pyserial python-socketio[client] websocket-client
============================================================
"""

import argparse
import sys
import os
import time
import threading
import termios
import tty
import serial
import serial.tools.list_ports
import socketio

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════
DEFAULT_PORT   = "/dev/ttyHS1"
DEFAULT_BAUD   = 9600
DEFAULT_SERVER = "https://leak-seeker.onrender.com"

UMBRAL_VIB    = 200    # counts
UMBRAL_PRES_H = 500    # kPa
UMBRAL_PRES_L = 10     # kPa
UMBRAL_FLOW   = 0.3    # L/min

# ══════════════════════════════════════════════════════════════
# ARGUMENTOS
# ══════════════════════════════════════════════════════════════
parser = argparse.ArgumentParser(description="Puente Serial → Socket.IO — Leak-Seeker")
parser.add_argument("-p", "--port",   default=DEFAULT_PORT)
parser.add_argument("-b", "--baud",   type=int, default=DEFAULT_BAUD)
parser.add_argument("-s", "--server", default=DEFAULT_SERVER)
parser.add_argument("--raw",          action="store_true",
                    help="Enviar CSV crudo (el servidor parsea)")
parser.add_argument("--invert-valve", action="store_true", default=True,
                    help="Invertir lógica de válvula (0=cerrada). Activo por defecto.")
parser.add_argument("--valve-closed-on", type=int, default=0,
                    help="Valor del pin que indica válvula CERRADA (default: 0)")
parser.add_argument("--list-ports",   action="store_true")
args = parser.parse_args()

if args.list_ports:
    print("\n📡 Puertos seriales disponibles:")
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("   (ninguno detectado)")
    for p in ports:
        print(f"   {p.device} — {p.description}")
    # Detectar también dispositivos tty en /dev/
    print("\n📁 Dispositivos tty en /dev/:")
    for name in sorted(os.listdir('/dev/')):
        if 'tty' in name.lower() or 'hs' in name.lower():
            print(f"   /dev/{name}")
    sys.exit(0)

print(f"""
╔══════════════════════════════════════════════════╗
║          💧 Leak-Seeker Bridge v2.0             ║
║          Serial MCU → Servidor Web              ║
╚══════════════════════════════════════════════════╝

  Puerto serial   : {args.port} @ {args.baud} baud
  Servidor        : {args.server}
  Modo            : {'CSV crudo' if args.raw else 'JSON parseado'}
  Válvula cerrada : pin == {args.valve_closed_on}
""")

# ══════════════════════════════════════════════════════════════
# ESTADÍSTICAS
# ══════════════════════════════════════════════════════════════
stats = {
    "enviados": 0,
    "errores_parse": 0,
    "inicio": time.time(),
}

# ══════════════════════════════════════════════════════════════
# SOCKET.IO
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
    print("✅ [WS] Conectado al servidor")

@sio.event
def disconnect():
    global ws_connected
    ws_connected = False
    print("❌ [WS] Desconectado — reintentando...")

def conectar_servidor():
    while True:
        try:
            print(f"🔄 Conectando a {args.server}...")
            sio.connect(args.server, transports=["websocket"])
            break
        except Exception as e:
            print(f"⚠️  Error de conexión: {e} — reintentando en 3s...")
            time.sleep(3)

# ══════════════════════════════════════════════════════════════
# PARSEAR CSV  →  dict JSON
# Formato MCU:  pt01,pt02,vt01,vt02,ft_delta,valveStatus\n
# ══════════════════════════════════════════════════════════════
def parse_csv(line):
    try:
        parts = line.strip().split(",")
        if len(parts) < 6:
            return None

        pt01     = float(parts[0])
        pt02     = float(parts[1])
        vt01     = int(float(parts[2]))
        vt02     = int(float(parts[3]))
        ft_delta = float(parts[4])
        valve_raw = int(float(parts[5]))

        vibration = max(abs(vt01), abs(vt02))
        pressure  = (pt01 + pt02) / 2.0
        flow      = abs(ft_delta)

        # ── Lógica de válvula ─────────────────────────
        # PIN=0 → válvula CERRADA (actuador activo)
        # PIN=1 → válvula ABIERTA (operación normal)
        valve_closed = (valve_raw == args.valve_closed_on)

        return {
            "vibration"  : round(vibration, 2),
            "pressure"   : round(pressure, 2),
            "flow"       : round(flow, 3),
            "pt01"       : round(pt01, 2),
            "pt02"       : round(pt02, 2),
            "vt01"       : vt01,
            "vt02"       : vt02,
            "ftDelta"    : round(ft_delta, 3),
            "alertVib"   : vibration > UMBRAL_VIB,
            "alertPres"  : pressure > UMBRAL_PRES_H or pressure < UMBRAL_PRES_L,
            "alertFlow"  : flow > UMBRAL_FLOW,
            "valveClosed": valve_closed,
            "timestamp"  : int(time.time() * 1000),
        }
    except Exception:
        return None

# ══════════════════════════════════════════════════════════════
# LECTURA SERIAL ROBUSTA (byte a byte)
# Funciona con hardware UART nativo (ttyHS, ttyAMA, ttyS)
# Evita el bug "returned no data" de PySerial con readline()
# ══════════════════════════════════════════════════════════════
def abrir_uart(port, baud):
    """
    Abre un UART nativo de Linux usando os.open() + termios.
    Evita interferencias del sistema operativo y control de flujo
    que rompen el readline() de PySerial en puertos de hardware.
    """
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    
    # Desactivar el modo non-blocking para lectura sincrónica
    flags = fcntl_get(fd)
    fcntl_set(fd, flags & ~os.O_NONBLOCK)

    # Configurar termios (velocidad y modo raw)
    attrs = termios.tcgetattr(fd)

    # Velocidades disponibles en termios
    BAUD_MAP = {
        9600  : termios.B9600,
        19200 : termios.B19200,
        38400 : termios.B38400,
        57600 : termios.B57600,
        115200: termios.B115200,
    }
    baud_flag = BAUD_MAP.get(baud, termios.B9600)

    attrs[4] = baud_flag   # ispeed
    attrs[5] = baud_flag   # ospeed

    # Modo raw: sin eco, sin señales, sin conversión de CR/LF
    attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK |
                  termios.ISTRIP | termios.INLCR  | termios.IGNCR  |
                  termios.ICRNL  | termios.IXON)
    attrs[1] &= ~termios.OPOST
    attrs[2] &= ~(termios.CSIZE | termios.PARENB)
    attrs[2] |=  termios.CS8
    attrs[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON |
                  termios.ISIG | termios.IEXTEN)

    # VMIN=0, VTIME=20 → devuelve lo que hay en 2s, nunca bloquea indefinidamente
    attrs[6][termios.VMIN]  = 0
    attrs[6][termios.VTIME] = 20

    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    termios.tcflush(fd, termios.TCIOFLUSH)
    return fd

def leer_linea_fd(fd, timeout=2.0):
    """Lee bytes del fd hasta encontrar \\n o timeout."""
    buf = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            ch = os.read(fd, 1)
        except BlockingIOError:
            time.sleep(0.005)
            continue
        except OSError:
            return None
        if not ch:
            time.sleep(0.005)
            continue
        if ch == b'\n':
            return buf.decode("utf-8", errors="ignore").strip()
        buf += ch
    return None  # timeout

def fcntl_get(fd):
    import fcntl
    return fcntl.fcntl(fd, fcntl.F_GETFL)

def fcntl_set(fd, flags):
    import fcntl
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)

# ══════════════════════════════════════════════════════════════
# HEARTBEAT
# ══════════════════════════════════════════════════════════════
def heartbeat():
    while True:
        time.sleep(10)
        elapsed = time.time() - stats["inicio"]
        freq = stats["enviados"] / elapsed if elapsed > 0 else 0
        ws  = "✅ WS" if ws_connected else "❌ WS"
        print(f"[HB] {ws} | Enviados: {stats['enviados']} | "
              f"{freq:.1f} pkt/s | Uptime: {int(elapsed)}s")

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
def main():
    threading.Thread(target=conectar_servidor, daemon=True).start()
    threading.Thread(target=heartbeat, daemon=True).start()
    time.sleep(2)

    while True:
        fd = None
        try:
            print(f"🔌 Abriendo {args.port} con lectura nativa...")
            fd = abrir_uart(args.port, args.baud)
            print(f"✅ Puerto abierto: {args.port}")

            while True:
                line = leer_linea_fd(fd, timeout=3.0)

                if line is None:
                    # Timeout — MCU puede no estar enviando aún
                    continue
                if not line:
                    continue

                if not ws_connected:
                    continue

                if args.raw:
                    sio.emit("sensor-csv", line)
                else:
                    data = parse_csv(line)
                    if data is None:
                        stats["errores_parse"] += 1
                        continue
                    sio.emit("sensor-data", data)

                stats["enviados"] += 1
                if stats["enviados"] % 20 == 0:
                    valve_str = "🔒 CERRADA" if data.get("valveClosed") else "🔓 abierta"
                    print(f"📤 [{stats['enviados']}] P={data['pressure']:.1f}kPa "
                          f"V={data['vibration']} F={data['flow']:.2f}L/m "
                          f"Válvula={valve_str}")

        except KeyboardInterrupt:
            print("\n🛑 Detenido por el usuario")
            elapsed = time.time() - stats["inicio"]
            print(f"   Paquetes enviados : {stats['enviados']}")
            print(f"   Uptime            : {int(elapsed)}s")
            break
        except Exception as e:
            print(f"⚠️  Error: {e}")
            print("   Reintentando en 3s...")
            time.sleep(3)
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except Exception:
                    pass

    try:
        sio.disconnect()
    except Exception:
        pass

if __name__ == "__main__":
    main()
