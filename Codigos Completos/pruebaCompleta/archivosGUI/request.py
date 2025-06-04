import serial
import time
import subprocess
import os
import platform

SERIAL_PORT = '/dev/ttyUSB0'       # Change to your port (e.g., '/dev/ttyUSB0')
BAUD_RATE = 115200
B64_FILENAME = 'image_received.b64'
JPG_FILENAME = 'image_decoded.jpg'

def request_image_and_save_b64():
    b64_lines = []
    print("Connecting to ESP32...")

    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
        time.sleep(2)
        ser.reset_input_buffer()

        print("Sending GET request...")
        ser.write(('GET'+"\r\n").encode())

        skipped_lines=0

        while True:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue
            if skipped_lines<5:
                skipped_lines+=1
                continue
            if line == "===START===":
                continue
            """if line == "GET":
                continue"""
            if line == "===END===":
                break
            if line.startswith("ERROR:"):
                print("ESP32 error:", line)
                return
            b64_lines.append(line)

    print("Saving base64 data...")
    with open(B64_FILENAME, 'w') as f:
        for line in b64_lines:
            f.write(line + '\n')

    print(f"Saved Base64 as {B64_FILENAME}")

def decode_with_terminal():
    system = platform.system()
    cmd = f"base64 -d {B64_FILENAME} > {JPG_FILENAME}"

    print(f"Decoding using command: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode == 0:
        print(f"Decoded image saved to {JPG_FILENAME}")
    else:
        print("Decoding failed.")
    

if __name__=="__main__":
    request_image_and_save_b64()
    decode_with_terminal()
