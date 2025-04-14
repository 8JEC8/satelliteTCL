# TODO: Use logger for messages
class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        
        # Despertar MPU6050
        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')  # 0x6B, despertarlo

        # Rango de Acelerómetro
        self.i2c.writeto_mem(self.addr, 0x1C, b'\x00')  # ±2g (0x00)

        # Rango de Giroscopio
        self.i2c.writeto_mem(self.addr, 0x1B, b'\x00')  # ±250°/s (0x00))
    
    def get_raw_accel(self):
        try:
            data = self.i2c.readfrom_mem(self.addr, 0x3B, 6)
            ax = int.from_bytes(data[0:2], 'big')
            ay = int.from_bytes(data[2:4], 'big')
            az = int.from_bytes(data[4:6], 'big')

            # Convertir a valores negativos
            if ax > 32767:
                ax -= 65536
            if ay > 32767:
                ay -= 65536
            if az > 32767:
                az -= 65536

            # Convertir a unidades reales (g), +-2g: dividir por 16384
            ax = ax / 16384.0
            ay = ay / 16384.0
            az = az / 16384.0
            return ax, ay, az
        except Exception as e:
            print("Error leyendo acelerómetro:", e)
            return 0, 0, 0

    def get_raw_gyro(self):
        try:
            data = self.i2c.readfrom_mem(self.addr, 0x43, 6)
            gx = int.from_bytes(data[0:2], 'big')
            gy = int.from_bytes(data[2:4], 'big')
            gz = int.from_bytes(data[4:6], 'big')

            # Convertir a valores negativos
            if gx > 32767:
                gx -= 65536
            if gy > 32767:
                gy -= 65536
            if gz > 32767:
                gz -= 65536

            # Convertir a unidades reales (°/s), +-250 grados/s: dividir por 131
            gx = gx / 131.0  
            gy = gy / 131.0
            gz = gz / 131.0
            return gx, gy, gz
        except Exception as e:
            print("Error leyendo Giroscopio:", e)
            return 0, 0, 0
