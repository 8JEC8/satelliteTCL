import socket
import _thread
import sys
import network
import time

ssid = "pasteles"
password = "chocolates"

is_sending = 0  # Flag; 0=False, 1=True
connection_active = False  # Flag, True=Conn activa, False=Conn desactivada
conn = None  # Será global
server_socket = None  # Será global
new_image_filename = None

log_file = open("ap_log.txt", "w") # Abrir log

def log_message(message):
    t = time.localtime()
    timestamp = "[05/05/2025]" + "[{:02d}:{:02d}:{:02d}]".format(*t[3:6])  # Fecha manual, T en 00:00:00 (2 Digitos en tiempo)
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

            if data == "M_RECIBIDO -> .PIC":
                log_message("RES_COM -> Iniciando recepción de imagen...")
            
                file_size_str = conn.recv(1024).decode().strip() # Leer tamaño antes de llamar receive_image()
                if not file_size_str.isdigit():
                    log_message(file_size_str)
                    continue
            
                expected_size = int(file_size_str)
                receive_image(expected_size)

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

def receive_image(expected_size):
    global conn, new_image_filename
    received_file = new_image_filename #mpremote connect COM3 fs cp :/JPG_recv_AP.jpg C:\Users\ecast\Downloads

    log_message(f"Esperando {expected_size} bytes")

    received = 0
    chunk_size = 1024

    with open(received_file, 'wb') as f:
        while received < expected_size:
            data = conn.recv(min(chunk_size, expected_size - received))
            if not data:
                break
            f.write(data)
            received += len(data)
            log_message(f"Se recibieron {received}/{expected_size} bytes")

    log_message(f"Imagen guardada: {received_file}")

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
ap.config(ssid=ssid, password=password, security=3)
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
        log_message("'.RSSI'    : Desplegar valor de RSSI")
        log_message("'.LEDON'   : Encender LED")
        log_message("'.LEDOFF'  : Apagar LED")
        log_message("'.TEMP'    : Temperatura y Humedad")
        log_message("'.GYRO'    : Acelerómetro y Giroscopio")
        log_message("'.POW'     : Potencia (V,I,W)")
        log_message("'.PICLIST' : Lista de Archivos en SAT microSD")
        log_message("'.PIC ###' : Recibir foto seleccionada (###)")
        log_message("'.PLAYLIST': Lista de canciones")
        log_message("'.VOL#'    : Ajustar volumen (#=1(bajo), #=2(medio), #=3(alto)")
        log_message("'.STOP'    : Detener canción")
        log_message("'.PAUSE'   : Pausar canción")
        log_message("'.RESUME'  : Reanudar canción")
        continue

    elif message.startswith(".PIC"):
        parts = message.split()
        if len(parts) == 2:
            new_image_filename = parts[1]  # Save the intended name
  
    elif message == ".PLAYLIST":
        log_message(message)
        log_message("'.TRACK1'  : Empire State of Mind")
        log_message("'.TRACK2'  : Ni**as In Paris")
        log_message("'.TRACK3'  : Praise The Lord")
        log_message("'.TRACK4'  : Through the Wire")
        log_message("'.TRACK5'  : RICKY")
        log_message("'.TRACK6'  : Me Against the World")
        log_message("'.TRACK7'  : I Love It")
        log_message("'.TRACK8'  : Poker Face")
        log_message("'.TRACK9'  : Born This Way")
        log_message("'.TRACK10' : Bad Romance")
        log_message("'.TRACK11' : Firework")
        log_message("'.TRACK12' : Blank Space")
        log_message("'.TRACK13' : Hotline Bling")
        log_message("'.TRACK14' : Life Is Good")
        log_message("'.TRACK15' : In My Feelings")
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
        conn = Nonegugguggugguggugguggugguggugguggug