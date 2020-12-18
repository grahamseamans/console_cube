import os
import numpy as np
from math import cos
from math import sin
from math import sqrt
import math
import time
import sys
import cProfile
import pstats


class render:
    def __init__(self):
        self.pre_screen = []
        self.post_screen = []

        self.screen_height = 100
        self.screen_width = 200
        self.pixels = self.screen_width * self.screen_height

        self.terminal_check()
        self.set_buffers()

        os.system("clear")
        os.system("tput civis")

    def __del__(self):
        os.system(f' echo "\x1B[{self.screen_height};{0}Hall done"')
        os.system("tput cnorm")

    def set_buffers(self):
        if self.pixels != len(self.pre_screen):
            self.pre_screen = []
            for _ in range(self.pixels):
                self.pre_screen.append(" ")

        if self.pixels != len(self.post_screen):
            self.post_screen = []
            for _ in range(self.pixels):
                self.post_screen.append(" ")

    def terminal_check(self):
        term = os.get_terminal_size()
        if term.columns != self.screen_width:
            self.screen_width = term.columns
        if term.lines != self.screen_height:
            self.screen_height = term.lines
        self.pixels = self.screen_width * self.screen_height
        self.set_buffers()

    def cordinates_from_index(self, i):
        y = i // self.screen_width
        x = i % self.screen_width
        return (x, y)

    def index_from_cordinates(self, x, y):
        return (y * self.screen_width) + x

    def vect_to_screen(self, vect):
        """
        distance = 4
        z = rotated[2]
        z = 1/(distance - z)
        z = 1 + z
        """
        z = 1

        projection = np.array([[1 / z, 0, 0], [0, 1 / z, 0]])

        point = projection @ vect

        half_width = self.screen_width // 2
        half_height = self.screen_height // 2
        x = point[0] * half_width
        y = point[1] * half_height
        x = int(x + half_width)
        y = int(y + half_height)
        if x == self.screen_width:
            x -= 1
        if y == self.screen_height:
            y -= 1
        return x, y

    def render(self):
        self.terminal_check()
        buffer_ = ""
        for i, (post, pre) in enumerate(zip(self.post_screen, self.pre_screen)):
            if pre != post:
                x, y = self.cordinates_from_index(i)
                buffer_ += f"\x1B[{y};{x}H{post}"
                self.pre_screen[i] = self.post_screen[i]
            self.post_screen[i] = " "

        os.system(f' echo "{buffer_}"')

    def change(self, x, y, new_pixel):
        if 0 <= x < self.screen_width and 0 <= y < self.screen_height:
            i = self.index_from_cordinates(x, y)
            if abs(i) < self.pixels:
                self.post_screen[i] = new_pixel

    def plotLine(self, x0, y0, x1, y1):
        # Bresenham
        d_x = abs(x1 - x0)
        d_y = -abs(y1 - y0)

        if x0 < x1:
            sx = 1
        else:
            sx = -1

        if y0 < y1:
            sy = 1
        else:
            sy = -1

        err = d_x + d_y

        self.change(x0, y0, ".")
        while x0 != x1 and y0 != y1:
            self.change(x0, y0, ".")
            e2 = 2 * err
            if e2 >= d_y:
                err += d_y
                x0 += sx
            if e2 <= d_x:
                err += d_x
                y0 += sy

    def wireframe_from_points_tetrahedron(self, tetrahedron):
        projected_points = []

        for vect in tetrahedron.rotated:
            x, y = self.vect_to_screen(vect)
            projected_points.append((x, y))

        for i in range(4):
            for j in range(i, 4):
                self.plotLine(*projected_points[i], *projected_points[j])

        for x, y in projected_points:
            self.change(x, y, "#")

    def wireframe_from_points_cube(self, cube):
        projected_points = []

        for vect in cube.rotated:
            x, y = self.vect_to_screen(vect)
            projected_points.append((x, y))

        for i in range(4):
            self.plotLine(*projected_points[i], *projected_points[(i + 1) % 4])
            self.plotLine(*projected_points[i], *projected_points[i + 4])

        self.plotLine(*projected_points[4], *projected_points[5])
        self.plotLine(*projected_points[5], *projected_points[6])
        self.plotLine(*projected_points[6], *projected_points[7])
        self.plotLine(*projected_points[7], *projected_points[4])

        for x, y in projected_points:
            self.change(x, y, "#")


class shape:
    def __init__(self):
        self.angle = 0
        self.points = None
        self.rotated = None

    def spin(self, change=0.01, X=True, Y=True, Z=True):
        self.angle += change
        if X:
            rotationX = np.array(
                [
                    [1, 0, 0],
                    [0, cos(self.angle), -sin(self.angle)],
                    [0, sin(self.angle), cos(self.angle)],
                ]
            )
        else:
            rotationX = np.eye(3)

        if Y:
            rotationY = np.array(
                [
                    [cos(self.angle), 0, -sin(self.angle)],
                    [0, 1, 0],
                    [sin(self.angle), 0, cos(self.angle)],
                ]
            )
        else:
            rotationY = np.eye(3)

        if Z:
            rotationZ = np.array(
                [
                    [cos(self.angle), -sin(self.angle), 0],
                    [sin(self.angle), cos(self.angle), 0],
                    [0, 0, 1],
                ]
            )
        else:
            rotationZ = np.eye(3)

        rotated = []
        for point in self.points:
            rotated.append(rotationX @ rotationY @ rotationZ @ point)
        self.rotated = np.asarray(rotated)


class cube(shape):
    def __init__(self):
        self.angle = 0
        len = 1 / sqrt(3)
        self.points = np.array(
            [
                [-len, -len, -len],
                [len, -len, -len],
                [len, len, -len],
                [-len, len, -len],
                [-len, -len, len],
                [len, -len, len],
                [len, len, len],
                [-len, len, len],
            ]
        )
        self.rotated = None


class tetrahedron(shape):
    def __init__(self):
        self.angle = 0
        self.points = np.array(
            [
                [sqrt(8 / 9), 0, -1 / 3],
                [-sqrt(2 / 9), sqrt(2 / 3), -1 / 3],
                [-sqrt(2 / 9), -sqrt(2 / 3), -1 / 3],
                [0, 0, 1],
            ]
        )
        self.rotated = None


profiler = cProfile.Profile()
profiler.enable()

r = render()
cube = cube()
tetrahedron = tetrahedron()
for i in range(10000):
    cube.spin(-0.01, X=True, Y=True, Z=True)
    tetrahedron.spin(0.01, X=True, Y=True, Z=True)
    r.wireframe_from_points_cube(cube)
    r.wireframe_from_points_tetrahedron(tetrahedron)
    r.render()
    time.sleep(0.005)

profiler.disable()
stats = pstats.Stats(profiler)
stats.strip_dirs().sort_stats("tottime").print_stats(10)
