import network
import machine
import usocket as socket
import time

# Configurar Access Point
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='ESP32-AP', password='shining', authmode=network.AUTH_WPA_WPA2_PSK)

print("Access Point inicializado")
print("SSID: ESP32-AP, Password: shining")
print("IP address:", ap.ifconfig()[0])

led_pin = 2

# Set up the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 80))
server.listen(1)

print("Server is listening...")

# Función para los requests
def handle_request(request):
    if "GET /ledon" in request:
        machine.Pin(led_pin, machine.Pin.OUT).on()
        print("LED is ON now")
    elif "GET /ledoff" in request:
        machine.Pin(led_pin, machine.Pin.OUT).off()
        print("LED is OFF now")

# Loop
while True:
    client, addr = server.accept()
    request = client.recv(1024).decode('utf-8')
    print(request) #Imprime la solicitud para ver que todo bien

    handle_request(request)

    response = "HTTP/1.1 200 OK\r\nContent-type:text/html\r\nConnection: close\r\n\r\n<html><body><h1>ESP32 Web Server</h1></body></html>"
    client.send(response)
    client.close()

    time.sleep(1)  # Delay para evitar spam bugs y cualquier otro problema
