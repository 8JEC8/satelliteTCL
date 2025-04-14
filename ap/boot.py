import socket
import _thread
import sys
import network_interface as ni
import logger as logs

is_sending = 0  # Flag; 0=False, 1=True
connection_active = False  # Flag, True=Conn activa, False=Conn desactivada
conn = None  # Será global
server_socket = None  # Será global

nif = ni.Nif()
log = logs.Logger('Main', 'main.log')

def receive_messages():
    global conn, connection_active

    while True:
        if not connection_active: #Si conexión activa, try; Si conexión no activa, reiniciar while True
            continue

        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            log.info(f"Satélite (STA): {data}")

        except OSError:
            log.info("Desconexión detectada. Reiniciando socket...")
            break

        except Exception as e:
            log.info(f"Error recibiendo mensaje de Satélite (STA): {e}")
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
    log.info("AP (You: Est. Terrestre) Esperando a STA (Satélite)...")

    conn, addr = server_socket.accept()
    connection_active = True
    log.info(f"Conectado a {addr}")
    log.info("LISTA DE COMANDOS: command.list")
    sys.stdout.write("\n")
    _thread.start_new_thread(receive_messages, ())


nif.setup_ap()
connection_loop()

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
