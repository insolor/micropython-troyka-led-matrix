# Micropython driver for Troyka Led Matrix for ESP8266
# Based on https://github.com/amperka/TroykaLedMatrix

from machine import I2C, Pin
from micropython import const

i2c = I2C(scl=Pin(0, Pin.OUT), sda=Pin(2, Pin.OUT))
I2C_ADDR_BASE = const(0x60)

MATRIX_SIZE_8X8 = const(0)
MATRIX_SIZE_7X9 = const(1)
MATRIX_SIZE_6X10 = const(2)
MATRIX_SIZE_5X11 = const(3)
MATRIX_SIZE_MASK = const(3)

MATRIX_MIN_ROWS = const(8)
MATRIX_MAX_ROWS = const(11)
MATRIX_MIN_COLS = const(5)
MATRIX_MAX_COLS = const(8)

AUDIO_GAIN_0DB = const(0)
AUDIO_GAIN_3DB = const(1)
AUDIO_GAIN_6DB = const(2)
AUDIO_GAIN_9DB = const(3)
AUDIO_GAIN_12DB = const(4)
AUDIO_GAIN_15DB = const(5)
AUDIO_GAIN_18DB = const(6)
AUDIO_GAIN_M6DB = const(7)
AUDIO_GAIN_MASK = const(7)

ROW_CURRENT_05MA = const(0)

REG_ADDR_CONFIGURATION = const(0x00)
REG_ADDR_COLUMN_DATA = const(0x01)
REG_ADDR_UPDATE_COLUMN = const(0x0C)
REG_ADDR_LIGHTING_EFFECT = const(0x0D)
REG_ADDR_AUDIO_EQUALIZER = const(0x0F)

BIT_CONFIG_SSD = const(7)
BIT_CONFIG_AUDIO_EN = const(2)
BIT_CONFIG_ADM = const(0)

ROW_CURRENT_MASK = const(0xF)

BIT_EFFECT_AUDIO_GAIN = const(4)
BIT_EFFECT_ROW_CURRENT = const(0)


def _BV(value):
    return 1 << value


class TroykaLedMatrix:
    def _writeReg(self, address, data):
        self.i2c.writeto_mem(self._i2c_address, address, data.to_bytes(1, 'little'))
    
    def _makeConfigReg(self):
        data = 0
        data |= self._shut_down and (1 << BIT_CONFIG_SSD)
        data |= self._audio_input and (1 << BIT_CONFIG_AUDIO_EN)
        data |= self._matrixSize << BIT_CONFIG_ADM
        return data
    
    def _makeEffectReg(self):
        data = ((self._audioInputGain << BIT_EFFECT_AUDIO_GAIN) | 
                (self._currentLimit << BIT_EFFECT_ROW_CURRENT))
        return data
    
    def setCurrentLimit(self, value):
        self._currentLimit = value & ROW_CURRENT_MASK
        self._writeReg(REG_ADDR_LIGHTING_EFFECT, self._makeEffectReg())
    
    def setMatrixSize(self, value):
        self._matrixSize = (value & MATRIX_SIZE_MASK)
        data = self._makeConfigReg()
        self._writeReg(REG_ADDR_CONFIGURATION, data)
        if self._matrixSize == MATRIX_SIZE_8X8:
            self._width = 8
            self._height = 8
        elif self._matrixSize == MATRIX_SIZE_7X9:
            self._width = 7
            self._height = 9
        elif self._matrixSize == MATRIX_SIZE_6X10:
            self._width = 6
            self._height = 10
        elif self._matrixSize == MATRIX_SIZE_5X11:
            self._width = 5
            self._height = 11
    
    def _getRow(self, y):
        # rotation is not implemented yet
        return self._data[y % self._height]
    
    def _updateDisplay(self):
        for i in range(self._height):
            data = self._getRow(i)
            self._writeReg(REG_ADDR_COLUMN_DATA + i, data)
        
        self._writeReg(REG_ADDR_UPDATE_COLUMN, 0xff)
    
    def clear(self):
        self._data = bytearray(MATRIX_MAX_ROWS)
        self._updateDisplay()
    
    def draw_pixel(self, x, y):
        i = x % 8
        j = y % MATRIX_MAX_ROWS
        self._data[j] |= 1 << i
        self._updateDisplay()
    
    def clear_pixel(self, x, y):
        i = x % 8
        j = y % MATRIX_MAX_ROWS
        self._data[j] &= ~(1 << i)
        self._updateDisplay()
    
    def __init__(self, i2c=i2c, address=I2C_ADDR_BASE, matrix_size = MATRIX_SIZE_8X8):
        self._i2c_address = address
        self.i2c = i2c
        self._shut_down = False
        self._audio_input = False
        self._audioEqualizer = False
        self._audioInputGain = AUDIO_GAIN_0DB
        self.setCurrentLimit(ROW_CURRENT_05MA)
        self.setMatrixSize(matrix_size)
        self._writeReg(REG_ADDR_CONFIGURATION, self._makeConfigReg())
        self._writeReg(REG_ADDR_LIGHTING_EFFECT, self._makeEffectReg())
        
        self._data = bytearray(MATRIX_MAX_ROWS)
