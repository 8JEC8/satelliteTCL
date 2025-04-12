import socket
import _thread
import sys
import network
import time

ssid = "ESP Tamales con Limón"
password = ""

is_sending = 0  # Flag; 0=False, 1=True
connection_active = False  # Flag, True=Conn activa, False=Conn desactivada
conn = None  # Será global
server_socket = None  # Será global

log_file = open("ap_log.txt", "w") # Abrir log

def log_message(message):
    t = time.localtime()
    timestamp = "[08/04/2025]" + "[{:02d}:{:02d}:{:02d}]".format(*t[3:6])  # Fecha manual, T en 00:00:00 (2 Digitos en tiempo)
    formatted_message = f"{timestamp} {message}"
    sys.stdout.write(formatted_message + "\n")
    log_file.write(formatted_message + "\n")
    log_file.flush()  # Escribir inmediatamente

def receive_messages():
    global conn, connection_active

    while True:
        if not connection_active: #Si conexión activa, try; Si conexión no activa, reiniciar while True
            continue

        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            log_message(f"Satélite (STA): {data}")

        except OSError:
            log_message("Desconexión detectada. Reiniciando socket...")
            break

        except Exception as e:
            log_message(f"Error recibiendo mensaje de Satélite (STA): {e}")
            break

    # Reset de conn, intentar conexión otra vez
    if conn:
        conn.close()
        conn = None

    connection_active = False
    connection_loop() 

def connection_loop():
    global conn, server_socket, connection_active
    connection_active = False
    try:
        if server_socket:
            server_socket.close()
    except:
        pass

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 1234))
    server_socket.listen(1)
    log_message("AP (You: Est. Terrestre) Esperando a STA (Satélite)...")

    conn, addr = server_socket.accept()
    connection_active = True
    log_message(f"Conectado a {addr}")
    log_message("LISTA DE COMANDOS: command.list")
    sys.stdout.write("\n")
    _thread.start_new_thread(receive_messages, ())

######################## Setup de AP
ap = network.WLAN(network.AP_IF)  # Crear AP
ap.config(essid=ssid, password=password)
ap.active(True)  # Activar

sys.stdout.write("\n\n")
log_message("AP activado")
log_message(f"SSID: {ssid}")
log_message(f"IP Address: {ap.ifconfig()[0]}")

connection_loop()  # Iniciar escuchando la primera conexión

######################## Envio de Mensajes

while True:
    is_sending = 1  # Enviando mensaje
    message = input("")
    if message == "":
        log_message("TERMINAL_ERROR: Mensaje vacío")
        continue
    
    elif message == "command.list":
        log_message(message)
        log_message("'sat.RSSI'    : Desplegar valor de RSSI")
        log_message("'sat.LED ON'  : Encender LED")
        log_message("'sat.LED OFF' : Apagar LED")
        log_message("'sat.TEMP'    : Temperatura y Humedad")
        log_message("'sat.GYRO'    : Acelerómetro y Giroscopio")
        log_message("'sat.POW'     : Potencia (V,I,W)")
        continue

    if not connection_active:
        log_message("¡NO CONEXIÓN! El mensaje no fue enviado.")
        continue

    try:
        conn.send(message.encode())
        log_message(f"Est. Terrestre (AP): {message}")
    except Exception as e:
        log_message(f"Error al enviar mensaje: {e}")
        connection_active = False
        conn = None
