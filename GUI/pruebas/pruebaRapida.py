import tkinter as tk
from PIL import Image, ImageTk

# Create the main GUI window
root = tk.Tk()
root.title("Image Resizer")

image = Image.open("godsplan.jpg")  # Replace with your image file path

resized_image = image.resize((250, 200))

img = ImageTk.PhotoImage(resized_image)

panel = tk.Label(image=img)
panel.image = img  # Required to prevent image from being garbage collected
panel.pack()

# Run the GUI application
root.mainloop()
