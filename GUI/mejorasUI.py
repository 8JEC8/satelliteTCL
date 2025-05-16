import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# Función para manejar el envío de comandos en la terminal
def enviar_comando(event=None):
    comando = terminal_entry.get()
    if comando.strip() != "":
        terminal_output.config(state='normal')
        terminal_output.insert(tk.END, f"> {comando}\n")
        terminal_output.see(tk.END)
        terminal_output.config(state='disabled')
        terminal_entry.delete(0, tk.END)

# Función para limpiar la terminal
def limpiar_terminal():
    terminal_output.config(state='normal')
    terminal_output.delete(1.0, tk.END)
    terminal_output.config(state='disabled')

# Crear ventana principal
root = tk.Tk()
root.title("Interfaz de Sensores y Control")
root.geometry("980x640")
root.resizable(False, False)

# Frame de conexión
connection_frame = ttk.LabelFrame(root, text="Conexión")
connection_frame.place(x=20, y=20, width=300, height=120)

connect_button = ttk.Button(connection_frame, text="Conectar")
connect_button.pack(pady=5)

connection_status = ttk.Label(connection_frame, text="Desconectado", foreground="red")
connection_status.pack()

# Frame sensores
sensors_frame = ttk.LabelFrame(root, text="Sensores")
sensors_frame.place(x=20, y=160, width=300, height=160)

sensor_labels = {}
def crear_sensor(nombre, fila):
    btn = ttk.Button(sensors_frame, text=nombre)
    btn.grid(row=fila, column=0, padx=10, pady=10)
    lbl = ttk.Label(sensors_frame, text="---")
    lbl.grid(row=fila, column=1, padx=10)
    sensor_labels[nombre] = lbl

crear_sensor("Giroscopio", 0)
crear_sensor("Temperatura", 1)
crear_sensor("Consumo Energía", 2)

# Frame actuador LED
actuator_frame = ttk.LabelFrame(root, text="Actuador LED")
actuator_frame.place(x=350, y=160, width=300, height=160)

led_button = ttk.Button(actuator_frame, text="Activar LED")
led_button.pack(pady=10)

led_status = ttk.Label(actuator_frame, text="Apagado", foreground="gray")
led_status.pack()

# Frame de imagen
image_frame = ttk.LabelFrame(root, text="Recepción de Imagen")
image_frame.place(x=700, y=20, width=260, height=300)

filename_entry = ttk.Entry(image_frame)
filename_entry.pack(pady=5, padx=10, fill='x')
filename_entry.insert(0, "imagen.jpg")

receive_img_btn = ttk.Button(image_frame, text="Recibir Imagen")
receive_img_btn.pack(pady=5)

# Mostrar imagen
try:
    image = Image.open("godsplan.jpg")
    resized_image = image.resize((200, 200))
    img = ImageTk.PhotoImage(resized_image)
    panel = tk.Label(image_frame, image = img)
    panel.image=img
    panel.pack(expand=False, padx=0, pady=0, fill = "none")

except Exception as e:
    img_placeholder = ttk.Label(image_frame, text="[ Imagen no encontrada ]", background="lightgray", anchor="center")
    img_placeholder.pack(expand=False, fill='both', padx=10, pady=10)

# Frame terminal
terminal_frame = ttk.LabelFrame(root, text="Terminal")
terminal_frame.place(x=20, y=360, width=940, height=240)

terminal_output = tk.Text(terminal_frame, height=8, bg='black', fg='green2', state='disabled')
terminal_output.pack(padx=10, pady=(5,0), fill='both', expand=True)

terminal_entry = ttk.Entry(terminal_frame)
terminal_entry.pack(fill='x', padx=10, pady=(5,2))
terminal_entry.bind("<Return>", enviar_comando)

clear_button = ttk.Button(terminal_frame, text="Clear", command=limpiar_terminal)
clear_button.pack(pady=(0,5))

# Ejecutar aplicación
root.mainloop()

