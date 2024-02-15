import pymem
import struct
import numpy as np
import ctypes
import win32api
import pygetwindow as gw
from OpenGL.raw.GLU import gluPerspective, gluLookAt
from consts import *
from OpenGL.GL import *
from offsets import *
import time
from OpenGL.GLUT import glutInit, glutCreateWindow, glutReshapeWindow, glutDisplayFunc, glutIdleFunc, GLUT_DOUBLE, \
    GLUT_RGB, GLUT_DEPTH
from os import system
import mouse
from OpenGL.GLU import *
from utils import *
import glfw
import threading
import keyboard
from pynput.mouse import Listener, Button

time.sleep(5)

enable_aimbot = False

def on_click(x, y, button, pressed):
    global enable_aimbot
    if button == Button.left:
        if pressed:
            enable_aimbot = True
        else:
            enable_aimbot = False

def mouse_listener():
    with Listener(on_click=on_click) as listener:
        listener.join()

# Запуск слухача миші в окремому потоці
mouse_thread = threading.Thread(target=mouse_listener)
mouse_thread.start()



class Debugger:

    def __init__(self, process_name):
        self.process = pymem.Pymem(process_name)
        self.base_address = self.process.base_address

    def read_process_memory(self, address, size):
        data = self.process.read_bytes(address, size)
        return data

    def get_rect(self, header) -> tuple:
        window = gw.getWindowsWithTitle(header)
        return (window[0].width, window[0].height)

    def close(self):
        self.process.close()
        del self


class Quake:

    def __init__(self):
        self.debugger = Debugger('cnq3-x64.exe')
        glfw.init()

    def get_player_coords(self, max_players=32):
        player_coords_address = self.debugger.base_address + player_coords_address_offset
        player_coords = []

        for i in range(max_players - 1):
            current_player_coords_address = player_coords_address + i * player_chunk_offset
            current_player_coords_data = self.debugger.read_process_memory(current_player_coords_address, FLOAT_SIZE * COORDINATES)
            current_player_coords = get_vector3(current_player_coords_data)

            if current_player_coords != (0.0, 0.0, 0.0):
                player_coords.append(current_player_coords)

        return player_coords

    def get_camera_coords(self) -> tuple:
        return struct.unpack('<fff',
                             self.debugger.read_process_memory(self.debugger.base_address + camera_address_offset,
                                                               FLOAT_SIZE * COORDINATES))

    def get_camera_direction(self) -> tuple:
        return get_vector3(self.debugger.read_process_memory(self.debugger.base_address + camera_address_offset + FLOAT_SIZE * 3, FLOAT_SIZE * COORDINATES))

    def get_fov(self) -> tuple:
        return struct.unpack('<f', self.debugger.read_process_memory(
            self.debugger.base_address + camera_address_fov_offset, 4))[0]

    def are_coordinates_approximately_equal(self, coord1, coord2, tolerance=27):
        return all(abs(round(getattr(a, 'x', a) - getattr(b, 'x', b), 6)) < tolerance for a, b in zip(coord1, coord2))

    def draw_players(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glColor3f(1, 0, 0)

        for player_coords in self.get_player_coords():
            if not self.are_coordinates_approximately_equal(player_coords, self.get_camera_coords()):
                win_x, win_y = self.project_3d_to_2d(player_coords)
                win_y = abs(win_y - 480)
                #print(
                #    f"My camera coords: {self.get_camera_coords()}\nDirection: {self.get_camera_direction()}\nUp: {self.get_up()}\nPlayer coords: {player_coords}\n Window coords: {win_x} {win_y}")

                drag_x = win_x - 328
                drag_y = win_y - (480 - 255)

                if enable_aimbot:
                    relative_move(int(drag_x) * 5, int(drag_y) * 5)

                glBegin(GL_POINTS)
                glVertex3f(player_coords[0], player_coords[1], player_coords[2])
                glEnd()

        glFlush()

    def project_3d_to_2d(self, coords):
        model_view = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)

        win_x, win_y, win_z = gluProject(coords[0], coords[1], coords[2], model_view, projection, viewport)
        return win_x, win_y

    def get_up(self):

        return get_vector3(self.debugger.read_process_memory(
            self.debugger.base_address + camera_address_offset + FLOAT_SIZE * 6, FLOAT_SIZE * COORDINATES))

    def run(self):
        try:
            window_rect = self.debugger.get_rect('cnq3')

            # Initialize GLFW
            if not glfw.init():
                raise RuntimeError("Could not initialize GLFW")

            # Create a windowed mode window and its OpenGL context
            glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
            window = glfw.create_window(640, 480, "Quake Window", None, None)
            if not window:
                glfw.terminate()
                raise RuntimeError("Could not create window")

            # Make the window's context current
            glfw.make_context_current(window)

            while not glfw.window_should_close(window):
                camera_pos = np.array(self.get_camera_coords())
                camera_direction = np.array(self.get_camera_direction())
                up = np.array(self.get_up())
                fov = self.get_fov()
                # Set the viewport
                glViewport(0, 0, window_rect[0], window_rect[1])

                # Projection matrix
                glMatrixMode(GL_PROJECTION)
                glLoadIdentity()
                gluPerspective(fov, window_rect[0] / window_rect[1], 0.1, 1000.0)

                # Model view matrix
                glMatrixMode(GL_MODELVIEW)
                glLoadIdentity()
                gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                          camera_pos[0] + camera_direction[0], camera_pos[1] + camera_direction[1],
                          camera_pos[2] + camera_direction[2],
                          0, 0, 1)

                # Draw players
                self.draw_players()

                # Swap front and back buffers
                glfw.swap_buffers(window)

                # Poll for and process events
                glfw.poll_events()

            glfw.terminate()

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    quake = Quake()
    quake.run()

