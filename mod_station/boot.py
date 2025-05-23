from machine import Pin, I2C
import network
import socket
import time
from time import sleep_ms
import _thread
import sys
import dht
from ina219 import INA219
from mpu6050 import MPU6050

ssid = "ESP Tamales con Limón"
password = ""

is_sending = 0 # Flag; 0=False, 1=True, 2=RSSI, 3=LED ON, 4=LED OFF, 5=Temp, 6=Giroscopio, 7=Potencia
LED = Pin(33, Pin.OUT) #LED, Pin D33

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000, timeout=1000)
ina = INA219(i2c)
STH_addr = 0x44

mpu = MPU6050(i2c)

######################## Funciones del Programa

def read_sth31():
    i2c.writeto(STH_addr, bytes([0x24, 0x00])) # Comando de de una lectura (0x24, 0x00)
    sleep_ms(15)  # Esperar medida

    # Lectura de 6 bytes: Temp MSB, Temp LSB, Temp CRC, Hum MSB, Hum LSB, Hum CRC
    data = i2c.readfrom(STH_addr, 6)

    # Combinar 2 bytes de T. y H.
    raw_temp = data[0] << 8 | data[1]
    raw_hum = data[3] << 8 | data[4]

    # Conversión (datasheet)
    temperatura = -45 + (175 * raw_temp / 65535.0)
    humedad = 100 * raw_hum / 65535.0 # Valor máximo de 16bits

    return temperatura, humedad

def print_message(is_sending, message):
    if is_sending==1:
        sys.stdout.write("Satélite (STA): " + message)  # Print mandando
    elif is_sending in [2, 3, 4, 5, 6, 7]:
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
            elif data=="sat.TEMP":
                print_message(is_sending=0, message=data)
                try:
                  temp, hum = read_sth31()
                  data="RES_COM -> " + "Temperatura: {:.2f} °C  |  Humedad: {:.2f} %".format(temp, hum)
                  print_message(is_sending=5, message=data)
                except OSError as e:
                  data=(f"Lectura de STH31 falló: {e}")
                  print_message(is_sending=5, message=data)
            elif data=="sat.GYRO":
                print_message(is_sending=0, message=data)
                try:
                  ax, ay, az = mpu.get_raw_accel()
                  gx, gy, gz = mpu.get_raw_gyro()
                  data="RES_COM:\n" + \
                       "ACC -> X: {:.4f} g, Y: {:.4f} g, Z: {:.4f} g\n".format(ax, ay, az) + \
                       "GYR -> X: {:.4f} °/s, Y: {:.4f} °/s, Z: {:.4f} °/s".format(gx, gy, gz)
                  print_message(is_sending=6, message=data)
                except OSError as e:
                  data=(f"Lectura de MPU6050 falló: {e}")
                  print_message(is_sending=6, message=data)
            elif data=="sat.POW":
                print_message(is_sending=0, message=data)
                try:
                  voltage = ina.bus_voltage
                  current = ina.current
                  power = voltage * (current / 1000)  # Calcular potencia
                  data="RES_COM:\n" + \
                     "Voltaje   (V): {:.3f} V\n".format(voltage) + \
                     "Corriente (I): {:.3f} mA\n".format(current) + \
                     "Potencia  (W): {:.3f} W".format(power)
                  print_message(is_sending=7, message=data)
                except OSError as e:
                    data=(f"Lectura de STH21 falló: {e}")
                    print_message(is_sending=7, message=data)
          
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
connected = False
while not connected:
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, port))
        connected = True
    except OSError as e:
        print("AP aún no está escuchando el socket. Reintentando en 3 segundos...")
        time.sleep(3)

print("Socket conectado con AP correctamente.")

######################## Recepción y Envío Simultaneo
_thread.start_new_thread(receive_messages, ()) # Recibir simultaneamente

while True:
    is_sending = 1 # Enviando mensaje
    time.sleep(10)
    message = "***Conexión Activa***"  # Cada 10 segundos, mencionar que conexión sigue activa
    if message=="":
      print("TERMINAL_ERROR: Mensaje vacío")
      continue
    client_socket.send(message.encode())  # Enviar mensaje
