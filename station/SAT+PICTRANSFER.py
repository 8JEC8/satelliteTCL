from machine import UART, Pin, I2C
import network
import socket
import time
from time import sleep_ms
import _thread
import sys
import dht
import machine
import os
from ina219 import INA219

ssid = "pasteles"
password = "chocolates"

is_sending = 0 # Flag; 0=False, 1=True, 2=RSSI, 3=LED ON, 4=LED OFF, 5=Temp, 6=Giroscopio, 7=Potencia
LED = Pin(33, Pin.OUT) #LED, Pin D33

spi = machine.SPI(1,
                  baudrate=5000000,  # Velocidad de 5 MHz
                  polarity=0,
                  phase=0,
                  sck=machine.Pin(18),
                  mosi=machine.Pin(23),
                  miso=machine.Pin(19))

cs = machine.Pin(5, machine.Pin.OUT)

sd = machine.SDCard(slot=2)
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd") #Montar sd

uart = UART(2, baudrate=9600, tx=17, rx=16)

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000, timeout=1000)
ina = INA219(i2c)
STH_addr = 0x44

######################## Clase de MPU 6050
class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        
        # Despertar MPU6050
        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')  # 0x6B, despertarlo

        # Rango de Acelerómetro
        self.i2c.writeto_mem(self.addr, 0x1C, b'\x00')  # ±2g (0x00)

        # Rango de Giroscopio
        self.i2c.writeto_mem(self.addr, 0x1B, b'\x00')  # ±250°/s (0x00))
    
    def get_raw_accel(self):
        try:
            data = self.i2c.readfrom_mem(self.addr, 0x3B, 6)
            ax = int.from_bytes(data[0:2], 'big')
            ay = int.from_bytes(data[2:4], 'big')
            az = int.from_bytes(data[4:6], 'big')

            # Convertir a valores negativos
            if ax > 32767:
                ax -= 65536
            if ay > 32767:
                ay -= 65536
            if az > 32767:
                az -= 65536

            # Convertir a unidades reales (g), +-2g: dividir por 16384
            ax = ax / 16384.0
            ay = ay / 16384.0
            az = az / 16384.0
            return ax, ay, az
        except Exception as e:
            print("Error leyendo acelerómetro:", e)
            return 0, 0, 0

    def get_raw_gyro(self):
        try:
            data = self.i2c.readfrom_mem(self.addr, 0x43, 6)
            gx = int.from_bytes(data[0:2], 'big')
            gy = int.from_bytes(data[2:4], 'big')
            gz = int.from_bytes(data[4:6], 'big')

            # Convertir a valores negativos
            if gx > 32767:
                gx -= 65536
            if gy > 32767:
                gy -= 65536
            if gz > 32767:
                gz -= 65536

            # Convertir a unidades reales (°/s), +-250 grados/s: dividir por 131
            gx = gx / 131.0  
            gy = gy / 131.0
            gz = gz / 131.0
            return gx, gy, gz
        except Exception as e:
            print("Error leyendo Giroscopio:", e)
            return 0, 0, 0

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

def mp3_command(cmd, param1=0x00, param2=0x00):
    mp3_packet = bytearray(10)
    mp3_packet[0] = 0x7E
    mp3_packet[1] = 0xFF
    mp3_packet[2] = 0x06
    mp3_packet[3] = cmd
    mp3_packet[4] = 0x00
    mp3_packet[5] = param1
    mp3_packet[6] = param2

    checksum = 0xFFFF - (sum(mp3_packet[1:7])) + 1
    mp3_packet[7] = (checksum >> 8) & 0xFF
    mp3_packet[8] = checksum & 0xFF
    mp3_packet[9] = 0xEF

    uart.write(mp3_packet)

def play_track(track_number):
    mp3_command(0x03, (track_number >> 8) & 0xFF, track_number & 0xFF)

def set_volume(volume):
    mp3_command(0x06, 0x00, volume)  # Volumen de 0-30 (0x1E es max; 18: 0x18)

def print_message(is_sending, message):
    if is_sending==1: #Mensaje original desde STA
        sys.stdout.write("Satélite (STA): " + message)  # Print mandando
    elif is_sending==2: #Telemetría
        sys.stdout.write(message)
        client_socket.send(message.encode())
    elif is_sending==0: #Acknowledge
        sys.stdout.write("Est. Terrestre (AP): " + message)  # Print recibiendo
        ack="M_RECIBIDO -> " + message
        client_socket.send(ack.encode())
    sys.stdout.write("\n")

def receive_messages():
    while True:
        try:
            og_data = client_socket.recv(1024).decode()
            if not og_data:
                break          
            data = og_data.strip()        
            parts = data.split()       
            if not parts:
                continue
              
            command = parts[0]         
            arg = parts[1] if len(parts) > 1 else None

            if command == ".RSSI":
                print_message(is_sending=0, message=og_data)
                rssi = str(sta.status('rssi'))
                telem = "RES_COM -> RSSI: " + rssi + "dBm"
                print_message(is_sending=2, message=telem)

            elif command == ".LEDON":
                print_message(is_sending=0, message=og_data)
                if LED.value() == 1:
                    telem = "RES_COM -> LED YA ESTÁ ON"
                    print_message(is_sending=2, message=telem)
                else:
                    LED.value(1)
                    telem = "RES_COM -> LED ON"
                    print_message(is_sending=2, message=telem)

            elif command == ".LEDOFF":
                print_message(is_sending=0, message=og_data)
                if LED.value() == 0:
                    telem = "RES_COM -> LED YA ESTÁ OFF"
                    print_message(is_sending=2, message=telem)
                else:
                    LED.value(0)
                    telem = "RES_COM -> LED OFF"
                    print_message(is_sending=2, message=telem)

            elif command == ".TEMP":
                print_message(is_sending=0, message=og_data)
                try:
                    temp, hum = read_sth31()
                    telem = "RES_COM -> Temperatura: {:.2f} °C  |  Humedad: {:.2f} %".format(temp, hum)
                    print_message(is_sending=2, message=telem)
                except OSError as e:
                    telem = f"Lectura de STH31 falló: {e}"
                    print_message(is_sending=2, message=telem)

            elif command == ".GYRO":
                print_message(is_sending=0, message=og_data)
                try:
                    ax, ay, az = mpu.get_raw_accel()
                    gx, gy, gz = mpu.get_raw_gyro()
                    telem = (
                        "RES_COM:\n" +
                        "ACC -> X: {:.4f} g, Y: {:.4f} g, Z: {:.4f} g\n".format(ax, ay, az) +
                        "GYR -> X: {:.4f} °/s, Y: {:.4f} °/s, Z: {:.4f} °/s".format(gx, gy, gz)
                    )
                    print_message(is_sending=2, message=telem)
                except OSError as e:
                    telem = f"Lectura de MPU6050 falló: {e}"
                    print_message(is_sending=2, message=telem)

            elif command == ".POW":
                print_message(is_sending=0, message=og_data)
                try:
                    voltage = ina.bus_voltage
                    current = ina.current
                    power = voltage * (current / 1000)
                    telem = (
                        "RES_COM:\n" +
                        "Voltaje   (V): {:.3f} V\n".format(voltage) +
                        "Corriente (I): {:.3f} mA\n".format(current) +
                        "Potencia  (W): {:.3f} W".format(power)
                    )
                    print_message(is_sending=2, message=telem)
                except OSError as e:
                    telem = f"Lectura de INA219 falló: {e}"
                    print_message(is_sending=2, message=telem)

            elif command == ".PICLIST":
                print_message(is_sending=0, message=og_data)
                try:
                    files = os.listdir('/sd')
                    telem="RES_COM:\n" + \
                          f"Archivos en microSD: {files}"
                    print_message(is_sending=2, message=telem)
                except OSError as e:
                    telem = f"Lectura de microSD falló: {e}"
                    print_message(is_sending=2, message=telem)
                  
            elif command == ".PIC":
                print_message(is_sending=0, message=command)
                if not arg or arg not in os.listdir("/sd"):
                    telem = "RES_COM -> Error: Archivo No Encontrado o Argumento Faltante"
                    print_message(is_sending=2, message=telem)
                    continue
                
                filename = "/sd/" + arg
                chunk_size = 1024
                               
                try:
                    file_size = os.stat(filename)[6]
                    client_socket.send(str(file_size).encode())
                    time.sleep(1) # TIEMPO DEPENDE DE TAMAÑO DE ARCHIVO
                    with open(filename, 'rb') as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            client_socket.send(chunk)
                    print_message(is_sending=2, message='RES_COM -> Imagen enviada exitosamente')
                except Exception as e:
                    telem = f"Envío de imagen falló: {e}"
                    print_message(is_sending=2, message=telem)

            elif command in (".VOL1", ".VOL2", ".VOL3"):
                print_message(is_sending=0, message=og_data)
                vol = {".VOL1": 0x08, ".VOL2": 0x12, ".VOL3": 0x18}[command]
                set_volume(vol)
                levels = {".VOL1": "Bajo", ".VOL2": "Medio", ".VOL3": "Alto"}
                telem = f"RES_COM -> Volumen Configurado: {levels[command]}"
                print_message(is_sending=2, message=telem)

            elif command.startswith(".TRACK"):
                track_commands = {
                    ".TRACK1": (1, "Empire State of Mind"),
                    ".TRACK2": (2, "Ni**as In Paris"),
                    ".TRACK3": (3, "Praise The Lord"),
                    ".TRACK4": (4, "Through the Wire"),
                    ".TRACK5": (5, "RICKY"),
                    ".TRACK6": (6, "Me Against the World"),
                    ".TRACK7": (7, "I Love It"),
                    ".TRACK8": (8, "Poker Face"),
                    ".TRACK9": (9, "Born This Way"),
                    ".TRACK10": (10, "Bad Romance"),
                    ".TRACK11": (11, "Firework"),
                    ".TRACK12": (12, "Blank Space"),
                    ".TRACK13": (13, "Hotline Bling"),
                    ".TRACK14": (14, "Life Is Good"),
                    ".TRACK15": (15, "In My Feelings")
                }

                if command in track_commands:
                    print_message(is_sending=0, message=og_data)
                    track_number, title = track_commands[command]
                    time.sleep(0.5)
                    play_track(track_number)
                    telem = f"RES_COM -> Escuchando: {title}"
                    print_message(is_sending=2, message=telem)
                else:
                    telem = f"RES_COM -> No hay canción asignada a: {command}"
                    print_message(is_sending=2, message=telem)

            elif command == ".STOP":
                print_message(is_sending=0, message=og_data)
                mp3_command(0x16)
                telem = "RES_COM -> Reproducción Detenida"
                print_message(is_sending=2, message=telem)

            elif command == ".PAUSE":
                print_message(is_sending=0, message=og_data)
                mp3_command(0x0E)
                telem = "RES_COM -> Canción Pausada"
                print_message(is_sending=2, message=telem)

            elif command == ".RESUME":
                print_message(is_sending=0, message=og_data)
                mp3_command(0x0D)
                telem = "RES_COM -> Canción Reanudada"
                print_message(is_sending=2, message=telem)
          
            else:
                print_message(is_sending=0, message=og_data)

        except Exception as e:
            print("Error recibiendo mensaje de Estación Terrestre (AP):", e)
            break

######################## Setup de STA
set_volume(0x18) # VOL3 en vez de VOLMAX por defecto
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
    time.sleep(8)
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
    message = input("")
    print_message(is_sending=1, message=message)
    if message=="":
      print("TERMINAL_ERROR: Mensaje vacío")
      continue
    client_socket.send(message.encode())  # Enviar mensaje