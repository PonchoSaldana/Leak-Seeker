#!/usr/bin/env python
"""
Serial Data Collection CSV (continuo hasta Ctrl+C)
"""
import argparse
import os
import serial
import serial.tools.list_ports

# =======================
# CONFIGURACIÓN
# =======================
DEFAULT_BAUD = 115200
DEFAULT_LABEL = "datos"

# =======================
# ARGUMENTOS
# =======================
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", required=True)
parser.add_argument("-b", "--baud", type=int, default=DEFAULT_BAUD)
parser.add_argument("-d", "--directory", default=".")
parser.add_argument("-l", "--label", default=DEFAULT_LABEL)
args = parser.parse_args()

# =======================
# MOSTRAR PUERTOS
# =======================
print("\nPuertos disponibles:")
for p, d, h in serial.tools.list_ports.comports():
    print(f"  {p} : {d}")

# =======================
# PREPARAR CSV
# =======================
os.makedirs(args.directory, exist_ok=True)
csv_path = os.path.join(args.directory, f"{args.label}.csv")

if not os.path.exists(csv_path):
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("valor1,valor2,valor3\n")  # <-- AJUSTA A TU SENSOR

# =======================
# SERIAL
# =======================
ser = serial.Serial(args.port, args.baud, timeout=1)
print(f"\nConectado a {args.port}")
print(f"Capturando indefinidamente — Ctrl+C para detener\n")

# =======================
# LOOP PRINCIPAL
# =======================
contador = 0
try:
    while True:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            continue
        print(f"RX [{contador+1}]: {line}")
        with open(csv_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        contador += 1
except KeyboardInterrupt:
    print(f"\nDetenido manualmente — {contador} líneas guardadas")
finally:
    ser.close()
    print("Puerto cerrado")
    print(f"Archivo final: {csv_path}")