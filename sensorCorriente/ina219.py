from machine import I2C
from micropython import const
_READ = const(0x01)

# Config Register (R/W)
_REG_CONFIG = const(0x00)
_CONFIG_RESET = const(0x8000)  # Reset Bit

_CONFIG_BVOLTAGERANGE_MASK = const(0x2000)  # Bus Voltage Range Mask
_CONFIG_BVOLTAGERANGE_16V = const(0x0000)  # 0-16V Range
_CONFIG_BVOLTAGERANGE_32V = const(0x2000)  # 0-32V Range

_CONFIG_GAIN_MASK = const(0x1800)     # Gain Mask
_CONFIG_GAIN_1_40MV = const(0x0000)   # Gain 1, 40mV Range
_CONFIG_GAIN_2_80MV = const(0x0800)   # Gain 2, 80mV Range
_CONFIG_GAIN_4_160MV = const(0x1000)  # Gain 4, 160mV Range
_CONFIG_GAIN_8_320MV = const(0x1800)  # Gain 8, 320mV Range

_CONFIG_BADCRES_MASK = const(0x0780)   # Bus ADC Resolution Mask
_CONFIG_BADCRES_9BIT = const(0x0080)   # 9-bit bus res = 0..511
_CONFIG_BADCRES_10BIT = const(0x0100)  # 10-bit bus res = 0..1023
_CONFIG_BADCRES_11BIT = const(0x0200)  # 11-bit bus res = 0..2047
_CONFIG_BADCRES_12BIT = const(0x0400)  # 12-bit bus res = 0..4097

_CONFIG_SADCRES_MASK = const(0x0078)              # Shunt ADC Res. &  Avg. Mask
_CONFIG_SADCRES_9BIT_1S_84US = const(0x0000)      # 1 x 9-bit shunt sample
_CONFIG_SADCRES_10BIT_1S_148US = const(0x0008)    # 1 x 10-bit shunt sample
_CONFIG_SADCRES_11BIT_1S_276US = const(0x0010)    # 1 x 11-bit shunt sample
_CONFIG_SADCRES_12BIT_1S_532US = const(0x0018)    # 1 x 12-bit shunt sample
_CONFIG_SADCRES_12BIT_2S_1060US = const(0x0048)   # 2 x 12-bit sample average
_CONFIG_SADCRES_12BIT_4S_2130US = const(0x0050)   # 4 x 12-bit sample average
_CONFIG_SADCRES_12BIT_8S_4260US = const(0x0058)   # 8 x 12-bit sample average
_CONFIG_SADCRES_12BIT_16S_8510US = const(0x0060)  # 16 x 12-bit sample average
_CONFIG_SADCRES_12BIT_32S_17MS = const(0x0068)    # 32 x 12-bit sample average
_CONFIG_SADCRES_12BIT_64S_34MS = const(0x0070)    # 64 x 12-bit sample average
_CONFIG_SADCRES_12BIT_128S_69MS = const(0x0078)   # 128 x 12-bit sample average

_CONFIG_MODE_MASK = const(0x0007)  # Operating Mode Mask
_CONFIG_MODE_POWERDOWN = const(0x0000)
_CONFIG_MODE_SVOLT_TRIGGERED = const(0x0001)
_CONFIG_MODE_BVOLT_TRIGGERED = const(0x0002)
_CONFIG_MODE_SANDBVOLT_TRIGGERED = const(0x0003)
_CONFIG_MODE_ADCOFF = const(0x0004)
_CONFIG_MODE_SVOLT_CONTINUOUS = const(0x0005)
_CONFIG_MODE_BVOLT_CONTINUOUS = const(0x0006)
_CONFIG_MODE_SANDBVOLT_CONTINUOUS = const(0x0007)

# SHUNT VOLTAGE REGISTER (R)
_REG_SHUNTVOLTAGE = const(0x01)

# BUS VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE = const(0x02)

# POWER REGISTER (R)
_REG_POWER = const(0x03)

# CURRENT REGISTER (R)
_REG_CURRENT = const(0x04)

# CALIBRATION REGISTER (R/W)
_REG_CALIBRATION = const(0x05)
# pylint: enable=bad-whitespace


def _to_signed(num):
    if num > 0x7FFF:
        num -= 0x10000
    return num


class INA219:
    """Driver for the INA219 current sensor"""
    def __init__(self, i2c_device: I2C, addr: int = 0x40):
        self.i2c_device = i2c_device

        self.i2c_addr = addr
        self.buf = bytearray(2)
        # Multiplier in mA used to determine current from raw reading
        self._current_lsb = 0
        # Multiplier in W used to determine power from raw reading
        self._power_lsb = 0

        # Set chip to known config values to start
        self._cal_value = 4096
        self.set_calibration_32V_2A()

    def _write_register(self, reg, value):
        self.buf[0] = (value >> 8) & 0xFF
        self.buf[1] = value & 0xFF
        self.i2c_device.writeto_mem(self.i2c_addr, reg, self.buf)

    def _read_register(self, reg):
        self.i2c_device.readfrom_mem_into(self.i2c_addr, reg & 0xff, self.buf)
        value = (self.buf[0] << 8) | (self.buf[1])
        return value

    @property
    def shunt_voltage(self):
        """The shunt voltage (between V+ and V-) in Volts (so +-.327V)"""
        value = _to_signed(self._read_register(_REG_SHUNTVOLTAGE))
        # The least signficant bit is 10uV which is 0.00001 volts
        return value * 0.00001

    @property
    def bus_voltage(self):
        """The bus voltage (between V- and GND) in Volts"""
        raw_voltage = self._read_register(_REG_BUSVOLTAGE)

        # Shift to the right 3 to drop CNVR and OVF and multiply by LSB
        # Each least signficant bit is 4mV
        voltage_mv = _to_signed(raw_voltage >> 3) * 4
        return voltage_mv * 0.001

    @property
    def current(self):
        """The current through the shunt resistor in milliamps."""
        # Sometimes a sharp load will reset the INA219, which will
        # reset the cal register, meaning CURRENT and POWER will
        # not be available ... athis by always setting a cal
        # value even if it's an unfortunate extra step
        self._write_register(_REG_CALIBRATION, self._cal_value)

        # Now we can safely read the CURRENT register!
        raw_current = _to_signed(self._read_register(_REG_CURRENT))
        return raw_current * self._current_lsb

    def set_calibration_32V_2A(self):  # pylint: disable=invalid-name

        self._current_lsb = .1  # Current LSB = 100uA per bit
        self._cal_value = 4096
        self._power_lsb = .002  # Power LSB = 2mW per bit
        self._write_register(_REG_CALIBRATION, self._cal_value)

        # Set Config register to take into account the settings above
        config = (_CONFIG_BVOLTAGERANGE_32V |
                  _CONFIG_GAIN_8_320MV |
                  _CONFIG_BADCRES_12BIT |
                  _CONFIG_SADCRES_12BIT_1S_532US |
                  _CONFIG_MODE_SANDBVOLT_CONTINUOUS)
        self._write_register(_REG_CONFIG, config)

    def set_calibration_32V_1A(self):  # pylint: disable=invalid-name
        self._current_lsb = 0.04  # In milliamps

        # 5. Compute the calibration register
        # Cal = trunc (0.04096 / (Current_LSB * RSHUNT))
        # Cal = 10240 (0x2800)

        self._cal_value = 10240

        # 6. Calculate the power LSB
        # PowerLSB = 20 * CurrentLSB
        # PowerLSB = 0.0008 (800uW per bit)
        self._power_lsb = 0.0008
        self._write_register(_REG_CALIBRATION, self._cal_value)

        # Set Config register to take into account the settings above
        config = (_CONFIG_BVOLTAGERANGE_32V |
                  _CONFIG_GAIN_8_320MV |
                  _CONFIG_BADCRES_12BIT |
                  _CONFIG_SADCRES_12BIT_1S_532US |
                  _CONFIG_MODE_SANDBVOLT_CONTINUOUS)
        self._write_register(_REG_CONFIG, config)

    def set_calibration_16V_400mA(self):  # pylint: disable=invalid-name
        self._current_lsb = 0.05  # in milliamps
        self._cal_value = 8192
        self._power_lsb = 0.001
        self._write_register(_REG_CALIBRATION, self._cal_value)

        config = (_CONFIG_BVOLTAGERANGE_16V |
                  _CONFIG_GAIN_1_40MV |
                  _CONFIG_BADCRES_12BIT |
                  _CONFIG_SADCRES_12BIT_1S_532US |
                  _CONFIG_MODE_SANDBVOLT_CONTINUOUS)
        self._write_register(_REG_CONFIG, config)
