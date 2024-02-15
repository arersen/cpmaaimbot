import struct
import win32api
import ctypes
import time

def get_vector3(data: bytearray) -> tuple:
    return struct.unpack('<fff', data)


INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001

# Структура для інформації про мишу
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("mi", MOUSEINPUT)]

def relative_move(dx, dy):
    mouse_input = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, None)
    input_structure = INPUT(INPUT_MOUSE, mouse_input)
    inputs = (INPUT * 1)(input_structure)
    ctypes.windll.user32.SendInput(1, ctypes.byref(inputs), ctypes.sizeof(INPUT))
