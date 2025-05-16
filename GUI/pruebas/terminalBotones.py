import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import sys

class TerminalCommandSender:
    def __init__(self, root):
        self.root = root
        root.title("Terminal Command Sender")
        
        # Create main frames
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=10)
        
        self.middle_frame = tk.Frame(root)
        self.middle_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.bottom_frame = tk.Frame(root)
        self.bottom_frame.pack(pady=10)
        
        # Command entry
        self.command_label = tk.Label(self.top_frame, text="Enter Command:")
        self.command_label.pack(side=tk.LEFT)
        
        self.command_entry = tk.Entry(self.top_frame, width=50)
        self.command_entry.pack(side=tk.LEFT, padx=5)
        self.command_entry.bind("<Return>", lambda event: self.send_command())
        
        # Command buttons
        self.send_button = tk.Button(self.top_frame, text="Send", command=self.send_command)
        self.send_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = tk.Button(self.top_frame, text="Clear", command=self.clear_output)
        self.clear_button.pack(side=tk.LEFT)
        
        # Output display
        self.output_text = scrolledtext.ScrolledText(
            self.middle_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Predefined commands buttons
        self.create_predefined_buttons()
        
        # Redirect stdout and stderr to the text widget
        sys.stdout = TextRedirector(self.output_text, "stdout")
        sys.stderr = TextRedirector(self.output_text, "stderr")
        
    def create_predefined_buttons(self):
        commands = [
            ("List Files", "ls"),
            ("List All Files", "ls -la"),
            ("Current Directory", "pwd"),
            ("System Info", "uname -a"),
            ("Disk Usage", "df -h"),
            ("Python Version", "python --version")
        ]
        
        for text, cmd in commands:
            button = tk.Button(
                self.bottom_frame,
                text=text,
                command=lambda c=cmd: self.set_and_send_command(c)
            )
            button.pack(side=tk.LEFT, padx=5)
    
    def set_and_send_command(self, command):
        self.command_entry.delete(0, tk.END)
        self.command_entry.insert(0, command)
        self.send_command()
    
    def send_command(self):
        command = self.command_entry.get()
        if not command.strip():
            messagebox.showwarning("Warning", "Please enter a command")
            return
        
        self.output_text.insert(tk.END, f"\n$ {command}\n")
        self.output_text.see(tk.END)
        
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Read output in real-time
            while True:
                output = process.stdout.readline()
                error = process.stderr.readline()
                
                if output == '' and error == '' and process.poll() is not None:
                    break
                
                if output:
                    print(output.strip())
                if error:
                    print(error.strip(), file=sys.stderr)
                
                self.root.update()
                
        except Exception as e:
            print(f"Error executing command: {str(e)}", file=sys.stderr)
    
    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

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
    app = TerminalCommandSender(root)
    root.mainloop()
