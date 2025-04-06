import tkinter
import urllib.request

root_url = "http://192.168.4.1"
window = tkinter.Tk()
window.title("Interfaz de control")

def send_request(url):
    try:
        urllib.request.urlopen(url)
    except Exception as e:
        print(f"Error de request: {e}")

def turn_led_on():
    send_request(root_url + "/ledon")
    lbl_status.config(text="LED ON", fg="green")

def turn_led_off():
    send_request(root_url + "/ledoff")
    lbl_status.config(text="LED OFF", fg="red")

def on_closing():
    window.destroy()

# Header
headline = tkinter.Label(window, text="Controlador de LED", fg="blue", font=("Arial", 20))
headline.grid(column=0, row=0, columnspan=2, pady=10)

# Botones
btn_on = tkinter.Button(window, text="ON", command=turn_led_on, bg="green", fg="white", font=("Arial", 16))
btn_off = tkinter.Button(window, text="OFF", command=turn_led_off, bg="red", fg="white", font=("Arial", 16))
btn_on.grid(column=0, row=1, padx=10)
btn_off.grid(column=1, row=1, padx=10)

# Labels
lbl_status = tkinter.Label(window, text="Connect to ESP32-AP network", font=("Arial", 14))
lbl_status.grid(column=0, row=2, columnspan=2)

# Evento cerrar ventana
window.protocol("WM_DELETE_WINDOW", on_closing)

# Loop
window.mainloop()
