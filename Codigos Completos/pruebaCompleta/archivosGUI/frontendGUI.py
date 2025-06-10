import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, filedialog
from PIL import Image, ImageTk
import serial
import serial.tools.list_ports
import threading
import queue
import re
from PIL import Image, ImageTk
import main
import subprocess
import os
import time
import base64
import request

class TerminalMicroPython:
    def __init__(self, root):
        self.root=root
        root.title("Interfaz de usuario sistema satelital")

        #Frame de ajustes
        self.settings_frame=ttk.LabelFrame(root, text="Ajustes de conexión")
        self.settings_frame.pack(pady=5, padx=5, fill=tk.X)
   
        # Seleccionador de IP
        self.ip_var = tk.StringVar(value='192.168.0.1')
        ttk.Label(self.settings_frame, text="IPv4:").grid(row=0, column=0, padx=5)
        self.ip_entry=ttk.Entry(self.settings_frame, width=14, textvariable=self.ip_var)
        self.ip_entry.grid(row=0, column=1, padx=5)

        # Seleccionador de puerto
        ttk.Label(self.settings_frame, text="Puerto:").grid(row=0, column=2, padx=5)
        self.port_var = tk.StringVar(value="8080")
        self.port_box = ttk.Entry(
                self.settings_frame,
                width=6,
                textvariable=self.port_var)
        self.port_box.grid(row=0, column=3, padx=5)

        # Nombre nuestro para identificación remota
        ttk.Label(self.settings_frame, text="L Name:").grid(row=0, column=4, padx=5)
        self.lname_var = tk.StringVar(value="rodro")
        self.hostname_box = ttk.Entry(
                self.settings_frame,
                width=10,
                textvariable=self.lname_var)
        self.hostname_box.grid(row=0, column=5, padx=5)

        # Nombre simbólico que damos al host remoto
        ttk.Label(self.settings_frame, text="R Name:").grid(row=0, column=6, padx=5)
        self.rname_var = tk.StringVar(value="earth")
        self.remote_host = ttk.Entry(
                self.settings_frame,
                width=10,
                textvariable=self.rname_var)
        self.remote_host.grid(row=0, column=7, padx=5)
        
        #Botón conectar y desconectar
        self.connect_button = ttk.Button(
                self.settings_frame,
                text="Conectar",
                command=self.toggle_connection)
        self.connect_button.grid(row=0, column=8, padx=5)

        #Frame general central
        self.general_frame=ttk.Frame(root)
        self.general_frame.pack(pady=5, padx=5, fill=tk.X)

        #Frame de botones de comandos
        self.commands_frame=ttk.LabelFrame(self.general_frame, text="Comandos sensores")
        self.commands_frame.grid(row=0, column=0, padx=5, pady=5)
        
        #Frame de lecturas
        self.readings_frame=ttk.LabelFrame(self.general_frame, text="Lecturas")
        self.readings_frame.grid(row=0,column=1, padx=5, pady=5)
        
        #Frame de visualización de imágenes
        self.image_frame = ttk.LabelFrame(self.general_frame, text="Visualización de imágenes")
        self.image_frame.grid(row=0, column=2, padx=5, pady=5)
        
        #Frame de terminal
        self.terminal_frame = ttk.LabelFrame(self.general_frame, text="Terminal")
        self.terminal_frame.grid(row=0, column=3, padx=5, pady=5)

        # Entrada para nombre de archivo de imagen
        ttk.Label(self.image_frame, text="Archivo de imagen:").pack(pady=(5,0))
        self.image_entry = ttk.Entry(self.image_frame, width=20)
        self.image_entry.pack(pady=5, padx=5)
        
        # Botón para buscar imagen
        ttk.Button(
            self.image_frame,
            text="Buscar imagen",
            command=self.browse_image
        ).pack(pady=5)
        
        # Botón para mostrar imagen
        ttk.Button(
            self.image_frame,
            text="Mostrar imagen",
            command=self.display_image
        ).pack(pady=5)

        # Botón para seleccionar imagen remota
        ttk.Label(self.image_frame, text="Archivo remoto").pack(pady=(5,0))
        self.remote_entry = ttk.Entry(self.image_frame, width=20)
        self.remote_entry.pack(pady=5, padx=5)
        
        #Botón obtener imágen
        self.guardar_btn = ttk.Button(self.image_frame, text="Solicitar archivo", command=self.recibir_imagen_desde_esp32)
        self.guardar_btn.pack(pady=5)

        # Canvas para mostrar la imagen
        self.image_canvas = tk.Canvas(self.image_frame, width=1000, height=600, bg='white')
        self.image_canvas.pack(pady=5)
        self.image_label = ttk.Label(self.image_frame, text="Imagen no cargada")
        self.image_label.pack()
        
        # Botón de control de LED
        self.led_state = False
        self.led_button =ttk.Button(
                self.commands_frame,
                text="Encender LED",
                command=self.toggle_led,
                state="disabled"
            )
        self.led_button.grid(row=0,column=0, padx=5)

        self.dirlist_button =ttk.Button(
                self.commands_frame,
                text="Listar archivos",
                command=self.req_ls,
                state="disabled"
            )
        self.dirlist_button.grid(row=1,column=0, padx=5)
        
        # Sensor readings display notebook (tabbed interface)
        self.readings_frame = ttk.LabelFrame(root, text="Lecturas")
        self.readings_frame.pack(pady=5, padx=5, fill=tk.X)
        
        # Temperature/Humidity tab
        self.temp_frame = ttk.LabelFrame(self.readings_frame, text="Clima")
        self.temp_frame.grid(row=0, column=0, padx=5)

        ttk.Label(self.temp_frame, text="Temperatura:").grid(row=0, column=0, padx=5, sticky="e")
        self.temp_var = tk.StringVar(value="--.- °C")
        ttk.Label(self.temp_frame, textvariable=self.temp_var, font=('Arial', 12)).grid(row=0, column=1, padx=5, sticky="w")
        
        ttk.Label(self.temp_frame, text="Humedad:").grid(row=2, column=0, padx=5, sticky="e")
        self.humidity_var = tk.StringVar(value="--.- %")
        ttk.Label(self.temp_frame, textvariable=self.humidity_var, font=('Arial', 12)).grid(row=2, column=1, padx=5, sticky="w")
         
        # Power tab
        
        self.power_frame = ttk.LabelFrame(self.readings_frame,text="Potencia")
        self.power_frame.grid(row=0, column=1, padx=5)

        ttk.Label(self.power_frame, text="Voltaje:").grid(row=0, column=0, padx=5, sticky="e")
        self.voltage_var = tk.StringVar(value="--.- V")
        ttk.Label(self.power_frame, textvariable=self.voltage_var, font=('Arial', 12)).grid(row=0, column=1, padx=5, sticky="w")
        
        ttk.Label(self.power_frame, text="Corriente:").grid(row=1, column=0, padx=5, sticky="e")
        self.current_var = tk.StringVar(value="--.- mA")
        ttk.Label(self.power_frame, textvariable=self.current_var, font=('Arial', 12)).grid(row=1, column=1, padx=5, sticky="w")
        
        ttk.Label(self.power_frame, text="Potencia:").grid(row=2, column=0, padx=5, sticky="e")
        self.power_var = tk.StringVar(value="--.- W")
        ttk.Label(self.power_frame, textvariable=self.power_var, font=('Arial', 12)).grid(row=2, column=1, padx=5, sticky="w")
        
        # Gyroscope tab
        self.gyro_frame = ttk.LabelFrame(self.readings_frame,text="Gyro")
        self.gyro_frame.grid(row=0, column=2, padx=5)

        ttk.Label(self.gyro_frame, text="X:").grid(row=0, column=0, padx=5, sticky="e")
        self.gyro_x_var = tk.StringVar(value="--.- °/s")
        ttk.Label(self.gyro_frame, textvariable=self.gyro_x_var, font=('Arial', 12)).grid(row=0, column=1, padx=5, sticky="w")
        
        ttk.Label(self.gyro_frame, text="Y:").grid(row=1, column=0, padx=5, sticky="e")
        self.gyro_y_var = tk.StringVar(value="--.- °/s")
        ttk.Label(self.gyro_frame, textvariable=self.gyro_y_var, font=('Arial', 12)).grid(row=1, column=1, padx=5, sticky="w")
        
        ttk.Label(self.gyro_frame, text="Z:").grid(row=2, column=0, padx=5, sticky="e")
        self.gyro_z_var = tk.StringVar(value="--.- °/s")
        ttk.Label(self.gyro_frame, textvariable=self.gyro_z_var, font=('Arial', 12)).grid(row=2, column=1, padx=5, sticky="w")
        
        # RSSI tab
        self.rssi_frame = ttk.LabelFrame(self.readings_frame, text="Señal")
        self.rssi_frame.grid(row=0, column=3, padx=5)

        ttk.Label(self.rssi_frame, text="RSSI:").grid(row=0, column=0, padx=5, sticky="e")
        self.rssi_var = tk.StringVar(value="--- dBm")
        ttk.Label(self.rssi_frame, textvariable=self.rssi_var, font=('Arial', 12)).grid(row=0, column=1, padx=5, sticky="w")
        
        # Terminal output
        self.output_text = scrolledtext.ScrolledText(
            self.terminal_frame,
            wrap=tk.WORD,
            width=60,
            height=25,
            bg="black",
            fg="white",
            insertbackground="white",
            state="disabled"
        )
        self.output_text.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        
        # Command entry (for sending MicroPython code)
        self.command_entry = ttk.Entry(self.terminal_frame, width=80)
        self.command_entry.pack(pady=5, padx=5, fill=tk.X)
        self.command_entry.bind("<Return>", self.send_to_micropython)
        
        #Manejo de threads
        self.serial_port = None
        self.serial_thread = None
        self.running = False
        self.output_queue = queue.Queue()
        
        # Variables para manejo de imágenes
        self.current_image = None
        self.image_path = ""
        
        # Start polling for new output
        self.root.after(100, self.poll_serial_output)
    
    def browse_image(self):
        """Abre un diálogo para seleccionar una imagen"""
        filepath = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if filepath:
            self.image_path = filepath
            self.image_entry.delete(0, tk.END)
            self.image_entry.insert(0, filepath)
    
    def display_image(self):
        """Muestra la imagen seleccionada en el canvas"""
        if not self.image_path:
            messagebox.showwarning("Advertencia", "Por favor selecciona una imagen primero")
            return
        
        try:
            # Limpiar canvas anterior
            self.image_canvas.delete("all")
            
            # Abrir imagen y redimensionar manteniendo aspect ratio
            img = Image.open(self.image_path)
            resized_image=img.resize((960,540))
            img.thumbnail((1200, 1200), Image.LANCZOS)
            
            # Convertir para tkinter
            self.current_image = ImageTk.PhotoImage(resized_image)
            
            # Mostrar imagen en el canvas
            self.image_canvas.create_image(
                500, 300,  # Centro del canvas
                image=self.current_image,)
            
            # Mostrar nombre del archivo
            filename = self.image_path.split("/")[-1]
            self.image_label.config(text=filename)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{str(e)}")
            self.image_label.config(text="Error al cargar imagen")
    def refresh_ports(self):
        """Actualizar puertos al usar seleccionador"""
        ports= [port.device for port in serial.tools.list_ports.comports()]
        self.port_combobox["values"]=ports
        if ports:
            self.port_combobox.set(ports[0])
    def toggle_connection(self):
        ''' Conectar a host remoto '''
        self.connect_button['state'] = 'disabled'
        main.setExtId(self.lname_var.get())
        main.connectTo(self.rname_var.get(), self.ip_var.get(), int(self.port_var.get()))
        main.setPrinter(self.print_output)
        self.led_button["state"] = "normal"
        for btn in self.commands_frame.winfo_children():
            btn["state"] = "normal"

        # start status refresh thread
        self._parseStats() # it loops itself

    def _parseStats(self):
        allStats = main.getPhysicalStatus()
        self.temp_var.set('{:.2f} ºC'.format(allStats[0][0]))
        self.humidity_var.set('{:.2f} %'.format(allStats[0][1]))

        self.voltage_var.set('{:.2f} V'.format(float(allStats[1][0])))
        self.current_var.set('{:.2f} mA'.format(float(allStats[1][1])))
        self.power_var.set('{:.2f} mW'.format(float(allStats[1][0] * allStats[1][1])))

        self.gyro_x_var.set('{:.2f} º/s'.format(allStats[2][0]))
        self.gyro_y_var.set('{:.2f} º/s'.format(allStats[2][1]))
        self.gyro_z_var.set('{:.2f} º/s'.format(allStats[2][2]))

        self.rssi_var.set('{} dBm'.format(allStats[3][0]))

        self.led_button.config(text=f'{('Encender', 'Apagar')[allStats[4][0]]} LED')
        threading.Timer(.5, self._parseStats).start()

    def connect_serial(self):
        """Abrir conexión serial"""
        port=self.port_combobox.get()
        baudrate=self.baudrate_var.get()

        if not port:
            messagebox.showerror("Error", "Puerto no seleccionado!")
            return False

        try:
            self.serial_port=serial.Serial(port, int(baudrate), timeout=1)
            self.running= True
            self.serial_thread=threading.Thread(
                    target=self.read_serial_data,
                    daemon=True
            )
            self.serial_thread.start()
            self.print_output(f"Conectado a {port} a {baudrate} baud\n")
            self.print_output("Presiona ENTER para mander comandos\n")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Fallo la conexión: \n{str(e)}")
            return False

    def toggle_led(self):
        """Cambia el estado del led"""
        main.commands.handleRequestLed(self.rname_var.get())

    def req_ls(self):
        main.commands.commandReqFiles(self.rname_var.get())

    def send_predefined_command(self, command):
        """Manda algun comando predefinido"""
        
        if not (self.serial_port and self.serial_port.is_open):
            messagebox.showerror("Error", "Host remoto no conectado.")
            return

        try:
            self.print_output(f">>> {command}\n")
        except Exception as e:
            self.print_output(f"\nFailed to send command: {str(e)}\n")
    
    def poll_serial_output(self):

        while not self.output_queue.empty():
            data=self.output_queue.get()
            self.print_output(data)

            if "RES_COM -> Temperatura:" in data:
                self.parse_temperature_data(data)
            elif "RSSI:" in data:
                self.parse_rssi_data(data)
            elif "GYR ->" in data:
                self.parse_gyro_data(data)
            elif "Voltaje" in data or "Corriente" in data or "Potencia" in data:
                self.parse_power_data(data)
                
        self.root.after(100, self.poll_serial_output)

    def send_to_micropython(self, event=None):
        command = self.command_entry.get()
        self.command_entry.delete(0, tk.END)

        if not command.strip():
            return

        exec(command)
        self.print_output(f">>> {command}\n")
    
    def print_output(self, text):
        """Imprime texto a la terminal"""
        self.output_text.configure(state="normal")
        self.output_text.insert(tk.END, text)
        self.output_text.configure(state="disabled")
        self.output_text.see(tk.END)

    def recibir_imagen_desde_esp32(self):
        main.commands.handleRequestFile(self.rname_var.get(), self.remote_entry.get())
        return

if __name__=="__main__":
    root=tk.Tk()
    app=TerminalMicroPython(root)
    root.mainloop()
    main.setPrinter(app.print_output)
