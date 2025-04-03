from machine import I2C, Pin
from time import sleep

# Setup
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)

# Checar conexoión
INA219_ADDR = 0x40
devices = i2c.scan()
if INA219_ADDR not in devices:
    print("INA219 not found at 0x%02X" % INA219_ADDR)
else:
    print("INA219 found at 0x%02X" % INA219_ADDR)
    
    from ina219 import INA219
    
    ina = INA219(i2c)  
    
    while True:
        try:
            voltage = ina.bus_voltage  
            current = ina.current      
            power = voltage * (current / 1000)  # Calcular potencia
            
            print("V: {:.3f} V".format(voltage))
            print("I: {:.3f} mA".format(current))
            print("P: {:.3f} W".format(power))
            print("-" * 20)
        except Exception as e:
            print("Error reading sensor:", e)
        sleep(1)
