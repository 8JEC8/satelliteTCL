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

# Abrir/Crear log, sobreescribir
log_file = open("ap_log.txt", "w")

######################## Funciones del Programa
def log_message(message):
    t = time.localtime()
    timestamp = "[04/04/2025]" + "[{:02d}:{:02d}:{:02d}]".format(*t[3:6])  # Fecha manual, T en 00:00:00 (2 Digitos en tiempo)

    formatted_message = f"{timestamp} {message}"

    sys.stdout.write(formatted_message + "\n")
    log_file.write(formatted_message + "\n")
    log_file.flush()  # Escribir inmediatamente

def receive_messages():
    while True:
        if not connection_active:
            continue
          
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
              
            # Log received message from STA
            log_message(f"Satélite (STA): {data}")
        
        except OSError:
            log_message("    Mensaje no reconocido por Satélite (STA), se confirma cerrado de Socket")
            break
          
        except Exception as e:
            log_message(f"    Error recibiendo mensaje de Satélite (STA): {e}")
            break

def connect_socket():
    global conn, server_socket, connection_active

    if connection_active:
        log_message("La conexión ya existe")
        return

    if server_socket:
        server_socket.close()  # Cerrar server socket si ya está creado
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 1234))
    server_socket.listen(1)
    log_message("AP (You: Est. Terrestre) Esperando a STA (Satélite)...")
  
    conn, addr = server_socket.accept()
    connection_active = True
    log_message(f"Conectado a {addr}")

    _thread.start_new_thread(receive_messages, ()) #Al conectar socket, recepción simultanea

def disconnect_socket():
    global conn, connection_active, server_socket

    if conn:
        conn.close()
        conn = None
        log_message("Socket Cerrado: Est. Terrestre (AP)")
    else:
        log_message("La conexión ya está cerrada")
    
    if server_socket:
        server_socket.close()
        server_socket = None
    
    connection_active = False

######################## Setup de AP
ap = network.WLAN(network.AP_IF)  # Crear AP
ap.config(essid=ssid, password=password)
ap.active(True)  # Activar

sys.stdout.write("\n\n")
log_message("AP activado")
log_message(f"SSID: {ssid}")
log_message(f"IP Address: {ap.ifconfig()[0]}")
log_message("LISTA DE COMANDOS: command.list")

######################## Envio de Mensajes
while True:
    is_sending = 1  # Enviando mensaje
    message = input("")
    if message == "":
        log_message("TERMINAL_ERROR: Mensaje vacío")
        continue
    elif message == "command.list":
        log_message("'sat.CON'     : Conectar con STA")
        log_message("'sat.DC'      : Desconectar de STA")
        log_message("'sat.RSSI'    : Desplegar valor de RSSI")
        log_message("'sat.LED ON'  : Encender LED")
        log_message("'sat.LED OFF' : Apagar LED")
        continue
    elif message == "sat.CON":
        connect_socket()
        continue
    elif message == "sat.DC":
        disconnect_socket()
        continue

    if not connection_active:
        log_message("¡NO CONEXIÓN! El mensaje no fue enviado.")
        continue  # Reiniciar while True
          
    conn.send(message.encode())
    log_message(f"Est. Terrestre (AP): {message}")
          
    conn.send(message.encode())
    log_message(f"Est. Terrestre (AP): {message}")
