import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import subprocess
import sys
import threading
import os

class PicocomTerminal:
    def __init__(self, root):
        self.root = root
        root.title("Picocom Terminal Controller")
        self.picocom_process = None
        self.serial_thread = None
        self.running = False
        
        # Create main frames
        self.connection_frame = tk.LabelFrame(root, text="Serial Connection", padx=5, pady=5)
        self.connection_frame.pack(pady=10, fill=tk.X)
        
        self.command_frame = tk.LabelFrame(root, text="Command Interface", padx=5, pady=5)
        self.command_frame.pack(pady=10, fill=tk.X)
        
        self.output_frame = tk.LabelFrame(root, text="Output", padx=5, pady=5)
        self.output_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Connection controls
        tk.Label(self.connection_frame, text="Device:").grid(row=0, column=0, padx=5)
        self.device_entry = ttk.Combobox(self.connection_frame, values=self.get_serial_devices(), width=15)
        self.device_entry.grid(row=0, column=1, padx=5)
        self.device_entry.set("/dev/ttyUSB0")
        
        tk.Label(self.connection_frame, text="Baud Rate:").grid(row=0, column=2, padx=5)
        self.baudrate_var = tk.StringVar(value="115200")
        self.baudrate_menu = ttk.Combobox(self.connection_frame, 
                                        textvariable=self.baudrate_var, 
                                        values=["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_menu.grid(row=0, column=3, padx=5)
        
        self.connect_button = tk.Button(self.connection_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=4, padx=5)
        
        # Command interface
        self.command_entry = tk.Entry(self.command_frame, width=50)
        self.command_entry.pack(side=tk.LEFT, padx=5)
        self.command_entry.bind("<Return>", lambda event: self.send_to_picocom())
        
        self.send_button = tk.Button(self.command_frame, text="Send", command=self.send_to_picocom)
        self.send_button.pack(side=tk.LEFT, padx=5)
        
        # Special picocom commands
        self.ctrl_a_button = tk.Button(self.command_frame, text="Ctrl+A", command=lambda: self.send_special_command('\x01'))
        self.ctrl_a_button.pack(side=tk.LEFT, padx=5)
        
        self.ctrl_x_button = tk.Button(self.command_frame, text="Ctrl+X", command=lambda: self.send_special_command('\x18'))
        self.ctrl_x_button.pack(side=tk.LEFT, padx=5)
        
        self.ctrl_u_button = tk.Button(self.command_frame, text="Ctrl+U", command=lambda: self.send_special_command('\x15'))
        self.ctrl_u_button.pack(side=tk.LEFT, padx=5)
        
        # Output display
        self.output_text = scrolledtext.ScrolledText(
            self.output_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Redirect stdout to the text widget
        sys.stdout = TextRedirector(self.output_text, "stdout")
        sys.stderr = TextRedirector(self.output_text, "stderr")
        
    def get_serial_devices(self):
        """Try to detect common serial devices"""
        common_devices = [
            "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1",
            "/dev/ttyS0", "/dev/ttyS1", "COM1", "COM2", "COM3", "COM4"
        ]
        return [d for d in common_devices if os.path.exists(d)] or common_devices
    
    def toggle_connection(self):
        if self.running:
            self.disconnect_picocom()
        else:
            self.connect_picocom()
    
    def connect_picocom(self):
        device = self.device_entry.get()
        baudrate = self.baudrate_var.get()
        
        if not device:
            messagebox.showerror("Error", "Please specify a serial device")
            return
            
        try:
            # Start picocom in a subprocess
            self.picocom_process = subprocess.Popen(
                ['picocom', '-b', baudrate, device],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start thread to read output
            self.running = True
            self.serial_thread = threading.Thread(target=self.read_picocom_output, daemon=True)
            self.serial_thread.start()
            
            self.connect_button.config(text="Disconnect")
            print(f"Connected to {device} at {baudrate} baud")
            
        except Exception as e:
            print(f"Error starting picocom: {str(e)}", file=sys.stderr)
    
    def disconnect_picocom(self):
        if self.picocom_process:
            try:
                # Send picocom exit command (Ctrl+A, Ctrl+X)
                self.picocom_process.stdin.write('\x01\x18')
                self.picocom_process.stdin.flush()
                self.picocom_process.terminate()
            except:
                pass
            
        self.running = False
        if self.serial_thread and self.serial_thread.is_alive():
            self.serial_thread.join(timeout=1)
            
        self.connect_button.config(text="Connect")
        print("Disconnected from serial device")
    
    def read_picocom_output(self):
        """Thread function to read picocom output"""
        while self.running and self.picocom_process:
            try:
                output = self.picocom_process.stdout.readline()
                if output:
                    print(output.strip())
                else:
                    # Process ended
                    self.running = False
                    self.root.after(100, lambda: self.connect_button.config(text="Connect"))
                    break
            except:
                break
    
    def send_to_picocom(self):
        if not self.running or not self.picocom_process:
            messagebox.showwarning("Warning", "Not connected to picocom")
            return
            
        command = self.command_entry.get()
        if not command.strip():
            return
            
        try:
            self.picocom_process.stdin.write(command + '\n')
            self.picocom_process.stdin.flush()
            self.command_entry.delete(0, tk.END)
        except Exception as e:
            print(f"Error sending command: {str(e)}", file=sys.stderr)
    
    def send_special_command(self, command):
        if not self.running or not self.picocom_process:
            messagebox.showwarning("Warning", "Not connected to picocom")
            return
            
        try:
            self.picocom_process.stdin.write(command)
            self.picocom_process.stdin.flush()
        except Exception as e:
            print(f"Error sending special command: {str(e)}", file=sys.stderr)
    
    def on_closing(self):
        self.disconnect_picocom()
        self.root.destroy()

class TextRedirector:
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag
    
    def write(self, text):
        self.widget.configure(state="normal")
        self.widget.insert(tk.END, text, (self.tag,))
        self.widget.configure(state="disabled")
        self.widget.see(tk.END)
    
    def flush(self):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = PicocomTerminal(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
