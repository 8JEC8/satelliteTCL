import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import queue
import re

class MicroPythonTerminal:
    def __init__(self, root):
        self.root = root
        root.title("MicroPython Serial Terminal")
        
        # Serial settings frame
        self.settings_frame = ttk.LabelFrame(root, text="Serial Settings")
        self.settings_frame.pack(pady=5, padx=5, fill=tk.X)
        
        # Port selection
        ttk.Label(self.settings_frame, text="Port:").grid(row=0, column=0, padx=5)
        self.port_combobox = ttk.Combobox(self.settings_frame, width=15)
        self.port_combobox.grid(row=0, column=1, padx=5)
        self.refresh_ports()
        
        # Baud rate (MicroPython default: 115200)
        ttk.Label(self.settings_frame, text="Baud Rate:").grid(row=0, column=2, padx=5)
        self.baudrate_var = tk.StringVar(value="115200")
        self.baudrate_combobox = ttk.Combobox(
            self.settings_frame, 
            width=10, 
            textvariable=self.baudrate_var,
            values=["9600", "19200", "38400", "57600", "115200"]
        )
        self.baudrate_combobox.grid(row=0, column=3, padx=5)
        
        # Connect/Disconnect button
        self.connect_button = ttk.Button(
            self.settings_frame, 
            text="Connect", 
            command=self.toggle_connection
        )
        self.connect_button.grid(row=0, column=4, padx=5)
        
        # Reset button (soft reset MicroPython)
        self.reset_button = ttk.Button(
            self.settings_frame,
            text="Reset (CTRL+D)",
            command=self.reset_micropython,
            state="disabled"
        )
        self.reset_button.grid(row=0, column=5, padx=5)
        
        # Command buttons frame
        self.commands_frame = ttk.LabelFrame(root, text="Quick Commands")
        self.commands_frame.pack(pady=5, padx=5, fill=tk.X)
        
        # LED Toggle Button (switches between LED.ON and LED.OFF)
        self.led_state = False  # Track LED state
        self.led_button = ttk.Button(
            self.commands_frame,
            text="LED OFF",
            command=self.toggle_led,
            state="disabled"
        )
        self.led_button.pack(side=tk.LEFT, padx=5)
        
        # Predefined command buttons
        ttk.Button(
            self.commands_frame,
            text="Commands list",
            command=lambda: self.send_predefined_command("command.list"),
            state="disabled"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            self.commands_frame,
            text="RSSI",
            command=lambda: self.send_predefined_command(".RSSI"),
            state="disabled"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            self.commands_frame,
            text="Power consumption",
            command=lambda: self.send_predefined_command(".POW"),
            state="disabled"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            self.commands_frame,
            text="Temperature",
            command=lambda: self.send_predefined_command(".TEMP"),
            state="disabled"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            self.commands_frame,
            text="Gyroscope reading",
            command=lambda: self.send_predefined_command(".GYRO"),
            state="disabled"
        ).pack(side=tk.LEFT, padx=5)
        
        # Sensor readings display notebook (tabbed interface)
        self.sensor_notebook = ttk.Notebook(root)
        self.sensor_notebook.pack(pady=5, padx=5, fill=tk.X)
        
        # Temperature/Humidity tab
        self.temp_frame = ttk.Frame(self.sensor_notebook)
        self.sensor_notebook.add(self.temp_frame, text="Environment")
        
        ttk.Label(self.temp_frame, text="Temperature:").grid(row=0, column=0, padx=5, sticky="e")
        self.temp_var = tk.StringVar(value="--.- °C")
        ttk.Label(self.temp_frame, textvariable=self.temp_var, font=('Arial', 12)).grid(row=0, column=1, padx=5, sticky="w")
        
        ttk.Label(self.temp_frame, text="Humidity:").grid(row=0, column=2, padx=5, sticky="e")
        self.humidity_var = tk.StringVar(value="--.- %")
        ttk.Label(self.temp_frame, textvariable=self.humidity_var, font=('Arial', 12)).grid(row=0, column=3, padx=5, sticky="w")
        
        # Power tab
        self.power_frame = ttk.Frame(self.sensor_notebook)
        self.sensor_notebook.add(self.power_frame, text="Power")
        
        ttk.Label(self.power_frame, text="Voltage:").grid(row=0, column=0, padx=5, sticky="e")
        self.voltage_var = tk.StringVar(value="--.- V")
        ttk.Label(self.power_frame, textvariable=self.voltage_var, font=('Arial', 12)).grid(row=0, column=1, padx=5, sticky="w")
        
        ttk.Label(self.power_frame, text="Current:").grid(row=1, column=0, padx=5, sticky="e")
        self.current_var = tk.StringVar(value="--.- mA")
        ttk.Label(self.power_frame, textvariable=self.current_var, font=('Arial', 12)).grid(row=1, column=1, padx=5, sticky="w")
        
        ttk.Label(self.power_frame, text="Power:").grid(row=2, column=0, padx=5, sticky="e")
        self.power_var = tk.StringVar(value="--.- W")
        ttk.Label(self.power_frame, textvariable=self.power_var, font=('Arial', 12)).grid(row=2, column=1, padx=5, sticky="w")
        
        # Gyroscope tab
        self.gyro_frame = ttk.Frame(self.sensor_notebook)
        self.sensor_notebook.add(self.gyro_frame, text="Gyroscope")
        
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
        self.rssi_frame = ttk.Frame(self.sensor_notebook)
        self.sensor_notebook.add(self.rssi_frame, text="Signal")
        
        ttk.Label(self.rssi_frame, text="RSSI:").grid(row=0, column=0, padx=5, sticky="e")
        self.rssi_var = tk.StringVar(value="--- dBm")
        ttk.Label(self.rssi_frame, textvariable=self.rssi_var, font=('Arial', 12)).grid(row=0, column=1, padx=5, sticky="w")
        
        # Terminal output
        self.output_text = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            width=80,
            height=15,  # Reduced height to make room for sensor notebook
            bg="black",
            fg="white",
            insertbackground="white"
        )
        self.output_text.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        
        # Command entry (for sending MicroPython code)
        self.command_entry = ttk.Entry(root, width=80)
        self.command_entry.pack(pady=5, padx=5, fill=tk.X)
        self.command_entry.bind("<Return>", self.send_to_micropython)
        
        # Serial port & thread management
        self.serial_port = None
        self.serial_thread = None
        self.running = False
        self.output_queue = queue.Queue()
        
        # Start polling for new output
        self.root.after(100, self.poll_serial_output)
    
    def refresh_ports(self):
        """Update available serial ports in the dropdown"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combobox["values"] = ports
        if ports:
            self.port_combobox.set(ports[0])
    
    def toggle_connection(self):
        """Connect or disconnect from the MicroPython board"""
        if self.serial_port and self.serial_port.is_open:
            self.disconnect_serial()
            self.connect_button["text"] = "Connect"
            self.reset_button["state"] = "disabled"
            self.led_button["state"] = "disabled"
            for btn in self.commands_frame.winfo_children():
                btn["state"] = "disabled"
        else:
            if self.connect_serial():
                self.connect_button["text"] = "Disconnect"
                self.reset_button["state"] = "normal"
                self.led_button["state"] = "normal"
                for btn in self.commands_frame.winfo_children():
                    btn["state"] = "normal"
    
    def connect_serial(self):
        """Open the serial connection to MicroPython"""
        port = self.port_combobox.get()
        baudrate = self.baudrate_var.get()
        
        if not port:
            messagebox.showerror("Error", "No port selected!")
            return False
        
        try:
            self.serial_port = serial.Serial(port, int(baudrate), timeout=1)
            self.running = True
            self.serial_thread = threading.Thread(
                target=self.read_serial_data,
                daemon=True
            )
            self.serial_thread.start()
            self.print_output(f"Connected to {port} @ {baudrate} baud\n")
            self.print_output("Press ENTER to send MicroPython commands\n")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect:\n{str(e)}")
            return False
    
    def disconnect_serial(self):
        """Close the serial connection"""
        if self.serial_port and self.serial_port.is_open:
            self.running = False
            self.serial_port.close()
            self.print_output("\nDisconnected\n")
    
    def reset_micropython(self):
        """Send a soft reset command (CTRL+D) to MicroPython"""
        if not (self.serial_port and self.serial_port.is_open):
            messagebox.showerror("Error", "Not connected to a serial port!")
            return
        
        try:
            # Send CTRL+D (ASCII 4) to soft-reset MicroPython
            self.serial_port.write(b'\x04')
            self.print_output("\n>> Sent soft reset (CTRL+D)\n")
        except Exception as e:
            self.print_output(f"\nFailed to reset: {str(e)}\n")
    
    def toggle_led(self):
        """Toggle between LED.ON and LED.OFF"""
        if not (self.serial_port and self.serial_port.is_open):
            messagebox.showerror("Error", "Not connected to a serial port!")
            return
        
        try:
            if self.led_state:
                command = ".LEDOFF"
                self.led_button["text"] = "LED OFF"
            else:
                command = ".LEDON"
                self.led_button["text"] = "LED ON"
            
            self.serial_port.write((command + "\r\n").encode())
            self.print_output(f">>> {command}\n")
            self.led_state = not self.led_state  # Toggle state
        except Exception as e:
            self.print_output(f"\nFailed to toggle LED: {str(e)}\n")
    
    def send_predefined_command(self, command):
        """Send a predefined command"""
        if not (self.serial_port and self.serial_port.is_open):
            messagebox.showerror("Error", "Not connected to a serial port!")
            return
        
        try:
            self.serial_port.write((command + "\r\n").encode())
            self.print_output(f">>> {command}\n")
        except Exception as e:
            self.print_output(f"\nFailed to send command: {str(e)}\n")
    
    def read_serial_data(self):
        """Thread: Continuously read data from MicroPython"""
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.readline().decode("utf-8", errors="replace")
                    self.output_queue.put(data)
            except Exception as e:
                self.output_queue.put(f"\nSerial error: {str(e)}\n")
                break
    
    def poll_serial_output(self):
        """Check for new serial data and display it"""
        while not self.output_queue.empty():
            data = self.output_queue.get()
            self.print_output(data)
            
            # Parse different types of sensor data
            if "RES_COM -> Temperatura:" in data:
                self.parse_temperature_data(data)
            elif "RSSI:" in data:
                self.parse_rssi_data(data)
            elif "GYR ->" in data:
                self.parse_gyro_data(data)
            elif "Voltaje" in data or "Corriente" in data or "Potencia" in data:
                self.parse_power_data(data)
                
        self.root.after(100, self.poll_serial_output)
    
    def parse_temperature_data(self, data):
        """Extract temperature and humidity values from the response"""
        try:
            match = re.search(r"Temperatura:\s*([\d.]+)\s*°C\s*\|\s*Humedad:\s*([\d.]+)\s*%", data)
            if match:
                temp = match.group(1)
                humidity = match.group(2)
                self.temp_var.set(f"{temp} °C")
                self.humidity_var.set(f"{humidity} %")
        except Exception as e:
            print(f"Error parsing temperature data: {e}")
    
    def parse_rssi_data(self, data):
        """Extract RSSI value from the response"""
        try:
            match = re.search(r"RSSI:\s*(-?\d+)dBm", data)
            if match:
                rssi = match.group(1)
                self.rssi_var.set(f"{rssi} dBm")
        except Exception as e:
            print(f"Error parsing RSSI data: {e}")
    
    def parse_gyro_data(self, data):
        """Extract gyroscope values from the response"""
        try:
            match = re.search(r"GYR -> X:\s*(-?[\d.]+)\s*°/s,\s*Y:\s*(-?[\d.]+)\s*°/s,\s*Z:\s*(-?[\d.]+)\s*°/s", data)
            if match:
                x = match.group(1)
                y = match.group(2)
                z = match.group(3)
                self.gyro_x_var.set(f"{x} °/s")
                self.gyro_y_var.set(f"{y} °/s")
                self.gyro_z_var.set(f"{z} °/s")
        except Exception as e:
            print(f"Error parsing gyroscope data: {e}")
    
    def parse_power_data(self, data):
        """Extract power values from the response"""
        try:
            if "Voltaje" in data:
                match = re.search(r"Voltaje\s*\(V\):\s*([\d.-]+)\s*V", data)
                if match:
                    self.voltage_var.set(f"{match.group(1)} V")
            elif "Corriente" in data:
                match = re.search(r"Corriente\s*\(I\):\s*([\d.-]+)\s*mA", data)
                if match:
                    self.current_var.set(f"{match.group(1)} mA")
            elif "Potencia" in data:
                match = re.search(r"Potencia\s*\(W\):\s*([\d.-]+)\s*W", data)
                if match:
                    self.power_var.set(f"{match.group(1)} W")
        except Exception as e:
            print(f"Error parsing power data: {e}")
    
    def send_to_micropython(self, event=None):
        """Send a command to MicroPython"""
        if not (self.serial_port and self.serial_port.is_open):
            messagebox.showerror("Error", "Not connected to a serial port!")
            return
        
        command = self.command_entry.get()
        self.command_entry.delete(0, tk.END)
        
        if not command.strip():
            return
        
        try:
            self.serial_port.write((command + "\r\n").encode())
            self.print_output(f">>> {command}\n")
        except Exception as e:
            self.print_output(f"\nFailed to send: {str(e)}\n")
    
    def print_output(self, text):
        """Helper to print text to the terminal"""
        self.output_text.configure(state="normal")
        self.output_text.insert(tk.END, text)
        self.output_text.configure(state="disabled")
        self.output_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = MicroPythonTerminal(root)
    root.mainloop()
