import tkinter as tk
from tkinter import ttk

# Crear ventana principal
root = tk.Tk()
root.title("Interfaz de Sensores")
root.geometry("600x500")
root.resizable(False, False)

# Frame superior derecho para conexión
connection_frame = ttk.LabelFrame(root, text="Conexión")
connection_frame.place(relx=0.7, rely=0.02, relwidth=0.28, relheight=0.15)

connect_button = ttk.Button(connection_frame, text="Conectar")
connect_button.pack(pady=5)

connection_status = ttk.Label(connection_frame, text="Desconectado", foreground="red")
connection_status.pack()

# Frame para sensores
sensors_frame = ttk.LabelFrame(root, text="Sensores")
sensors_frame.place(relx=0.05, rely=0.2, relwidth=0.9, relheight=0.35)

# Botones de sensores
btn_gyro = ttk.Button(sensors_frame, text="Giroscopio")
btn_gyro.grid(row=0, column=0, padx=10, pady=10)

btn_temp = ttk.Button(sensors_frame, text="Temperatura")
btn_temp.grid(row=0, column=1, padx=10, pady=10)

btn_energy = ttk.Button(sensors_frame, text="Consumo de Energía")
btn_energy.grid(row=0, column=2, padx=10, pady=10)

# Caja de resultados de sensores
sensor_output = tk.Text(sensors_frame, height=4, width=60)
sensor_output.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

# Frame estilo terminal
terminal_frame = ttk.LabelFrame(root, text="Terminal")
terminal_frame.place(relx=0.05, rely=0.6, relwidth=0.9, relheight=0.35)

# Caja de texto tipo terminal
terminal_output = tk.Text(terminal_frame, height=8, width=70, state='disabled', bg='black', fg='green2')
terminal_output.pack(padx=10, pady=5)

# Entrada de comandos
terminal_entry = ttk.Entry(terminal_frame)
terminal_entry.pack(fill='x', padx=10, pady=5)

# Ejecutar aplicación
root.mainloop()

