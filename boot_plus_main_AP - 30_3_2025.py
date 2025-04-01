import socket
import _thread
import sys
import network

ssid = "ESP Tamales con Limón"
password = ""

is_sending = 0 # Flag; 0=False, 1=True
connection_active = False # Flag, True=Conn activa, False=Conn desactivada
conn = None  # Será global
server_socket = None  # Será global

def print_message(is_sending, message):
    if is_sending==1:
        sys.stdout.write("    Est. Terrestre (AP): " + message)  # Print mandando
    elif is_sending==0:
        sys.stdout.write("    Satélite (STA): " + message)  # Print recibiendo
    sys.stdout.write("\n")

def receive_messages():
    while True:
        if not connection_active: #Si conexión activa==True: False, se recibe mensaje; Si conexión activa==False: True, "continue" reinicia while True
          continue
          
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
              
            # Print mensaje STA al recibir
            print_message(is_sending=0, message=data)
        
        except OSError: #Excepción 1: Mensaje no ACK por STA debido a conexión cerrada MANUALMENTE con sock.DISCONN
            print("    Mensaje no reconocido por Satélite (STA), se confirma cerrado de Socket")
            break
          
        except Exception as e: #Excepción 2: Errores genéricos
            print("    Error recibiendo mensaje de Satélite (STA):", e)
            break

def connect_socket():
  global conn, server_socket, connection_active

  if connection_active==True:
    print("    La conexión ya existe")
    return

  if server_socket:
    server_socket.close() #Cerrar server socket si ya está creado
    
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET: Internet Protocol version 4; SOCK_STREAM: Protocolo TCP
  server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Puerto puede ser reusado inmediatamente
  server_socket.bind(('0.0.0.0', 1234))  # Cualquier puerto de uso general, no reservado, cualquier IP
  server_socket.listen(1) # Esuchar a 1 usuario
  print("    AP (You: Est. Terrestre) Esperando a STA (Satélite)...")
  
  conn, addr = server_socket.accept()
  connection_active = True
  print(f"Conectado a {addr}")
  sys.stdout.write("\n")
  _thread.start_new_thread(receive_messages, ()) # Mandar y recibir simultaneamente
  
def disconnect_socket():
  global conn, connection_active, server_socket
  if conn: # En caso que conn este abierto
    conn.close()
    conn = None
    print("    Socket Cerrado: Est. Terrestre (AP)")
  else: # En caseo que conn esté cerrado
    print("    La conexión ya está cerrada")
    
  if server_socket:
    server_socket.close()
    server_socket = None
    
  connection_active = False
  
######################## Setup de AP
ap = network.WLAN(network.AP_IF)  # Crear AP
ap.config(essid=ssid, password=password)  
ap.active(True)  # Activar

sys.stdout.write("\n")
sys.stdout.write("\n")
print("AP activado")
print("SSID:", ssid)
print("IP Address:", ap.ifconfig()[0])  # Print IP
print("LISTA DE COMANDOS: command.list")
######################## Envio de Mensajes

while True:
    is_sending = 1 # Enviando mensaje
    message = input("")
    if message=="":
      print("    TERMINAL_ERROR: Mensaje vacío")
      continue
    elif message=="command.list":
      print("'sat.CON'     : Conectar con STA")
      print("'sat.DC'      : Desconectar de STA")
      print("'sat.RSSI'    : Desplegar valor de RSSI")
      print("'sat.LED ON'  : Encender LED")
      print("'sat.LED OFF' : Apagar LED")
      continue
    elif message=="sat.CON":
      connect_socket()
    elif message=="sat.DC":
      disconnect_socket()
      continue

    if not connection_active:
      print("    ¡NO CONEXIÓN! El mensaje no fue enviado.")
      continue  # Reiniciar while True
          
    conn.send(message.encode())