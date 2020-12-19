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
import collections


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
        os.system(f' echo "\x1B[{self.screen_height - 1};{0}Hall done"')
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
        projection = np.array([[1, 0, 0], [0, 1, 0]])

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

    def to_buff(self, shape):
        for triangle in shape.tris_to_render:
            tri = triangle[:-1].astype("int32")
            shade = triangle[-1]
            projected_tri = []
            for vect in shape.rotated[tri]:
                x, y = self.vect_to_screen(vect)
                projected_tri.append((x, y))
            self.triangle_raster(projected_tri, shade)

    def safe_div(self, a, b):
        if b == 0:
            return 0
        else:
            return a / b

    def triangle_raster(self, vects, shade):
        # http://www.sunshine2k.de/coding/java/TriangleRasterization/
        #       TriangleRasterization.html

        # all of the triangle is the same shade, might as well do it here
        shade = self.get_shade(shade)

        # sorting by y value
        vects.sort(key=lambda x: x[1])

        # no top half
        if vects[0][1] == vects[1][1]:
            self.flat_top_triangle(vects[0], vects[1], vects[2], shade)
        # no bottom half
        elif vects[1][1] == vects[2][1]:
            self.flat_bottom_triangle(vects[0], vects[1], vects[2], shade)
        # no flat side
        else:
            # getting middle vertex for the triangle split
            long_inv_slope = self.safe_div(
                (vects[0][0] - vects[2][0]), (vects[0][1] - vects[2][1])
            )
            dy = vects[1][1] - vects[0][1]
            v4x = int(dy * long_inv_slope) + vects[0][0]
            v4 = (v4x, vects[1][1])

            self.flat_bottom_triangle(vects[0], vects[1], v4, shade)
            self.flat_top_triangle(vects[1], v4, vects[2], shade)

    def flat_bottom_triangle(self, vect1, vect2, vect3, shade):
        # vect1 is pointing away from flat line

        if vect2[0] > vect3[0]:
            swap = vect2
            vect2 = vect3
            vect3 = swap

        slope2 = self.safe_div((vect1[0] - vect2[0]), (vect1[1] - vect2[1]))
        slope3 = self.safe_div((vect1[0] - vect3[0]), (vect1[1] - vect3[1]))
        x2 = vect1[0]
        x3 = vect1[0]
        for y in range(vect1[1], vect2[1], 1):
            self.horiz_line(int(x2), int(x3), y, shade)
            x2 += slope2
            x3 += slope3

    def flat_top_triangle(self, vect1, vect2, vect3, shade):
        # vect3 is always pointing away from flat line

        if vect1[0] > vect2[0]:
            swap = vect1
            vect1 = vect2
            vect2 = swap

        slope1 = self.safe_div((vect3[0] - vect1[0]), (vect3[1] - vect1[1]))
        slope2 = self.safe_div((vect3[0] - vect2[0]), (vect3[1] - vect2[1]))
        x1 = vect3[0]
        x2 = vect3[0]
        # -1 after upper bound removes a gap between the triangle halves
        for y in range(vect3[1], vect2[1] - 1, -1):
            self.horiz_line(int(x1), int(x2), y, shade)
            x1 -= slope1
            x2 -= slope2

    def horiz_line(self, x1, x2, y, shade):
        for x in range(x1, x2):
            self.change(x, y, shade)

    def get_shade(self, shade):
        shades = ",-+=*^c#%@"
        if shade < 0:
            return "."
        shade = int(shade * 10)
        return shades[shade]


class shape:
    def __init__(self):
        self.angle = 0
        self.points = None
        self.rotated = None
        self.tris = None
        self.tris_to_render = None

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

        norms = self.surface_norms()
        norms = self.normalize_v3(norms)

        light = np.array([0, 1, 0])
        shading = np.dot(norms, light)
        self.tris_to_render = np.append(self.tris, np.transpose([shading]), axis=1)

        view = np.array([0, 0, -1])
        seen_mask = np.dot(norms, view)
        self.tris_to_render = self.tris_to_render[seen_mask > 0]

    def surface_norms(self):
        # taken from: https://sites.google.com/site/dlampetest/python/
        #       calculating-normals-of-a-triangle-mesh-using-numpy
        # so cool, got to get better at slicing
        tris_verts = self.rotated[self.tris]
        norms = np.cross(
            tris_verts[::, 1] - tris_verts[::, 0], tris_verts[::, 2] - tris_verts[::, 0]
        )
        return norms

    def normalize_v3(self, arr):
        # taken from: https://sites.google.com/site/dlampetest/python/
        #       calculating-normals-of-a-triangle-mesh-using-numpy
        # so cool, got to get better at slicing
        """ Normalize a numpy array of 3 component vectors shape=(n,3) """
        lens = np.sqrt(arr[:, 0] ** 2 + arr[:, 1] ** 2 + arr[:, 2] ** 2)
        arr[:, 0] /= lens
        arr[:, 1] /= lens
        arr[:, 2] /= lens
        return arr


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
        self.tris = np.array(
            [
                [2, 5, 6],
                [2, 1, 5],
                [1, 0, 4],
                [1, 4, 5],
                [3, 2, 6],
                [3, 6, 7],
                [0, 3, 7],
                [0, 7, 4],
                [7, 6, 5],
                [7, 5, 4],
                [2, 3, 0],
                [3, 0, 2],
            ]
        )
        self.render = None


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
        self.tris = np.array([[0, 2, 3], [0, 3, 1], [0, 1, 2], [1, 3, 2]])
        self.render = None


profiler = cProfile.Profile()
profiler.enable()

r = render()
cube = cube()
tetrahedron = tetrahedron()
for i in range(1000):
    cube.spin()
    tetrahedron.spin()
    r.to_buff(cube)
    r.to_buff(tetrahedron)
    r.render()
    time.sleep(0.005)

profiler.disable()
stats = pstats.Stats(profiler)
stats.strip_dirs().sort_stats("tottime").print_stats(10)
