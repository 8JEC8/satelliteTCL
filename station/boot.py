from machine import Pin
import network
import socket
import time
import _thread
import sys

ssid = "ESP Tamales con Limón"
password = ""

is_sending = 0 # Flag; 0=False, 1=True, 2=RSSI, 3=LED ON, 4=LED OFF, 5=Temp, 6=Potencia, 7=Giroscopio
LED = Pin(23, Pin.OUT) #LED, Pin D23

######################## Funciones del Programa
def print_message(is_sending, message):
    if is_sending==1:
        sys.stdout.write("Satélite (STA): " + message)  # Print mandando
    elif is_sending in [2, 3, 4]:
        sys.stdout.write(message)
        client_socket.send(message.encode())
    elif is_sending==0:
        sys.stdout.write("Est. Terrestre (AP): " + message)  # Print recibiendo
        ack="M_RECIBIDO -> " + message
        client_socket.send(ack.encode())
    sys.stdout.write("\n")

def receive_messages():
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            
            if data=="sat.RSSI":
                print_message(is_sending=0, message=data)
                rssi=str(sta.status('rssi'))
                data="RES_COM -> RSSI: " + rssi + "dBm"
                print_message(is_sending=2, message=data)
            elif data=="sat.LED ON":
                if LED.value()==1:
                  print_message(is_sending=0, message=data)
                  data="RES_COM -> LED YA ESTÁ ON"
                  print_message(is_sending=3, message=data)
                else:
                  print_message(is_sending=0, message=data)
                  LED.value(1)
                  data="RES_COM -> LED ON"
                  print_message(is_sending=3, message=data)
            elif data=="sat.LED OFF":
                if LED.value()==0:
                  print_message(is_sending=0, message=data)
                  data="RES_COM -> LED YA ESTÁ OFF"
                  print_message(is_sending=4, message=data)
                else:
                  print_message(is_sending=0, message=data)
                  LED.value(0)
                  data="RES_COM -> LED OFF"
                  print_message(is_sending=4, message=data)
          
            else:
              # Print mensaje AP al recibir
              print_message(is_sending=0, message=data)
                        
        except Exception as e:
            print("Error recibiendo mensaje de Estación Terrestre (AP)::", e)
            break

######################## Setup de STA
sta = network.WLAN(network.STA_IF)  # Crear STA
sta.active(False) 
sta.active(True)  # Activar

# Conectar a AP
sys.stdout.write("\n")
sys.stdout.write("\n")
print("STA (You: Satélite) Conectando a AP (Est. Terrestre)...")
sta.connect(ssid, password)

# Esperar conexión
while not sta.isconnected():
    time.sleep(3)
    print("Intentando conectar...")

print("Conectado")
print("IP:", sta.ifconfig()[0]) # Print IP
sys.stdout.write("\n")

######################## Configuración de Socket
# Cliente (TCP)
server_ip = "192.168.4.1"  # IP de AP
port = 1234 #Puerto de AP

# Socket de Servidor
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET: Internet Protocol version 4; SOCK_STREAM: TCP
client_socket.connect((server_ip, port)) 

######################## Recepción y Envío Simultaneo
_thread.start_new_thread(receive_messages, ()) # Recibir simultaneamente

while True:
    is_sending = 1 # Enviando mensaje
    message = input("")  # Input
    if message=="":
      print("TERMINAL_ERROR: Mensaje vacío")
      continue
    client_socket.send(message.encode())  # Enviar mensaje
    client_socket.send(message.encode())  # Send the message
    
# Cerrar socket
client_socket.close()
