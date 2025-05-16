import tkinter as tk
from tkinter import scrolledtext
import subprocess
import sys
import threading

class MinimalTerminal:
    def __init__(self, root):
        self.root = root
        root.title("Minimal Terminal")
        
        # Command entry
        self.command_entry = tk.Entry(root, width=80)
        self.command_entry.pack(pady=5, padx=5, fill=tk.X)
        self.command_entry.bind("<Return>", self.execute_command)
        self.command_entry.focus_set()
        
        # Output display
        self.output_text = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            width=100,
            height=30,
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.output_text.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        
        # Process management
        self.current_process = None
        self.running = False
        
        # Redirect stdout/stderr
        sys.stdout = TextRedirector(self.output_text, "stdout")
        sys.stderr = TextRedirector(self.output_text, "stderr")
        
        print("Ready. Type commands like 'ls' or 'picocom -b 115200 /dev/ttyUSB0'")
    
    def execute_command(self, event=None):
        command = self.command_entry.get()
        self.command_entry.delete(0, tk.END)
        
        if not command.strip():
            return
            
        print(f"$ {command}")
        
        # If a process is running, send input to it
        if self.running and self.current_process:
            try:
                self.current_process.stdin.write(command + "\n")
                self.current_process.stdin.flush()
                return
            except:
                self.running = False
                
        # Otherwise start a new process
        try:
            self.current_process = subprocess.Popen(
                command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.running = True
            
            # Start threads to handle output
            threading.Thread(target=self.read_output, args=(self.current_process.stdout,), daemon=True).start()
            threading.Thread(target=self.read_output, args=(self.current_process.stderr,), daemon=True).start()
            
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def read_output(self, stream):
        while self.running:
            try:
                output = stream.readline()
                if output:
                    print(output.strip())
                else:
                    break
            except:
                break
        
        self.running = False

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
    terminal = MinimalTerminal(root)
    root.mainloop()
