import sys
import time
import select

FILENAME = 'image.b64'  # Must already exist on ESP32

def send_base64_file():
    try:
        with open(FILENAME, 'r') as f:
            for line in f:
                print(line.strip())  # Strip newline
        print("===END===")  # Marker for PC
    except Exception as e:
        print("ERROR:", e)

def wait_for_serial_command():
    print("ESP32 ready. Waiting for GET...")
    while True:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            command = sys.stdin.readline().strip()
            if command == 'GET':
                send_base64_file()
        time.sleep(0.1)

wait_for_serial_command()

