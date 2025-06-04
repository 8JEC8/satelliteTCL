import ubinascii
import os
import machine
"""
if __name__=="__main__":
    sd = machine.SDCard(slot=2)
    os.mount(os.VfsFat(sd), "/sd")
"""


def convert_image_to_base64(input_file, output_file):
    try:
        with open(input_file, "rb") as fin, open(output_file, "w") as fout:
            while True:
                chunk = fin.read(512)
                if not chunk:
                    break
                b64 = ubinascii.b2a_base64(chunk).strip()
                fout.write(b64.decode("utf-8") + "\n")
        print("Conversión completada. Archivo base64 guardado como:", output_file)
    except Exception as e:
        print("ERROR en la conversión:", e)

# Ejecuta la conversión automáticamente
#convert_image_to_base64()

