STH_addr = 0x44
def read_sth31(i2c):
    res = (0 ,0)
    try:
        i2c.writeto(STH_addr, bytes([0x24, 0x00])) # Comando de de una lectura (0x24, 0x00)
        #sleep_ms(5)  # Esperar medida

        # Lectura de 6 bytes: Temp MSB, Temp LSB, Temp CRC, Hum MSB, Hum LSB, Hum CRC
        data = i2c.readfrom(STH_addr, 6)

        # Combinar 2 bytes de T. y H.
        raw_temp = data[0] << 8 | data[1]
        raw_hum = data[3] << 8 | data[4]

        # Conversión (datasheet)
        temperatura = -45 + (175 * raw_temp / 65535.0)
        humedad = 100 * raw_hum / 65535.0 # Valor máximo de 16bits
        res = (temperatura, humedad)
    except OSError:
        pass

    return res
