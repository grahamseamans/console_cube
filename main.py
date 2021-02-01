# main.py Graham Seamans 2020

import cProfile
from math import cos
from math import sin
from math import sqrt
import os
import pstats
import time

import numpy as np


class render:
    def __init__(self):
        self.projection = np.array([[1, 0, 0], [0, 1, 0]])

        self.pre_screen = []
        self.post_screen = []

        self.screen_height = 0
        self.screen_width = 0
        self.old_height = 0
        self.old_width = 0

        self.terminal_check()
        self.set_buffers()

        self.pixels = self.screen_width * self.screen_height

        os.system("clear")
        os.system("tput civis")

    def __del__(self):
        os.system("tput cnorm")

    def set_buffers(self):
        for i in range(self.screen_width):
            self.pre_screen.append([])
            self.post_screen.append([])
            for _ in range(self.screen_height):
                self.pre_screen[i].append(" ")
                self.post_screen[i].append(" ")

    def terminal_check(self):
        term = os.get_terminal_size()
        resized_window = False
        if term.columns != self.old_width:
            resized_window = True
            self.old_width = term.columns
        if term.lines != self.old_height:
            resized_window = True
            self.old_height = term.lines
        if resized_window:
            size = min(int(term.columns / 2.2), term.lines)
            self.screen_height, self.screen_width = size, int(size * 2.2)
            self.pixels = self.screen_width * self.screen_height
            self.set_buffers()

    def render(self):
        self.terminal_check()
        # not very pythonic but it's ~60% faster than using a nested
        # enumerate zip looping structure and this is the slowest part
        # of the program
        buffer = ""
        for x in range(self.screen_width):
            for y in range(self.screen_height):
                if self.pre_screen[x][y] != self.post_screen[x][y]:
                    buffer += f"\x1B[{y};{x}H{self.post_screen[x][y]}"
                    self.pre_screen[x][y] = self.post_screen[x][y]
                self.post_screen[x][y] = " "
        os.system(f' echo "{buffer}"')

    def parse_tri(self, triangle):
        tri = triangle[:-1].astype("int32")
        shade = triangle[-1]
        return (tri, shade)

    def stretch_shift_to_screen(self, vect):
        half_width = (self.screen_width // 2) - 1
        half_height = (self.screen_height // 2) - 1
        half_screen = [half_width, half_height]
        vect *= half_screen
        vect += half_screen
        return round(vect[0]), round(vect[1])

    def vect_to_screen(self, vect):
        vect = self.projection @ vect
        x, y = self.stretch_shift_to_screen(vect)
        return x, y

    def project_tri(self, tri, shape):
        projected_tri = []
        for vect in shape.rotated[tri]:
            x, y = self.vect_to_screen(vect)
            projected_tri.append((x, y))
        return projected_tri

    def to_buff(self, shape):
        for triangle in shape.tris_to_render:
            (tri, shade) = self.parse_tri(triangle)
            projected_tri = self.project_tri(tri, shape)
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
        # 0 is x, 1 is y
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
        # 0 is x, 1 is y
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
            self.post_screen[x][y] = shade

    def get_shade(self, shade):
        shades = ",-_+*^c#%@"
        if shade < 0:
            return "."
        else:
            return shades[int(shade * 10)]


class environment:
    def __init__(self) -> None:
        self.light_source = np.array([0, 1, 0])
        self.camera = np.array([0, 0, -1])
        self.shapes = []
        self.renderer = render()

    def add_shape(self, shape):
        self.shapes.append(shape)

    def spin_shapes(self):
        for shape in self.shapes:
            shape.spin()

    def time_step(self):
        self.spin_shapes()
        self.shading()
        self.who_is_seen()
        self.render_shapes()

    def render_shapes(self):
        for shape in self.shapes:
            self.renderer.to_buff(shape)
        self.renderer.render()

    def shading(self):
        for shape in self.shapes:
            shading = np.dot(shape.surface_normals, self.light_source)
            shading = np.transpose([shading])
            shape.tris_to_render = np.append(shape.tris, shading, axis=1)

    def who_is_seen(self):
        for shape in self.shapes:
            seen_mask = np.dot(shape.surface_normals, self.camera)
            shape.seen_tris_mask(seen_mask)


class shape:
    def __init__(self, spin=0.01):
        self.angle = 0
        self.spin_change = spin
        self.points = None
        self.rotated = None
        self.tris = None
        self.tris_to_render = None
        self.rotation_matrix = None
        self.surface_normals = None

    def calculate_rotation_matrix(self):
        self.rotation_matrix = self.x_rotation() @ self.y_rotation() @ self.z_rotation()

    def x_rotation(self):
        return np.array(
            [
                [1, 0, 0],
                [0, cos(self.angle), -sin(self.angle)],
                [0, sin(self.angle), cos(self.angle)],
            ]
        )

    def y_rotation(self):
        return np.array(
            [
                [cos(self.angle), 0, -sin(self.angle)],
                [0, 1, 0],
                [sin(self.angle), 0, cos(self.angle)],
            ]
        )

    def z_rotation(self):
        return np.array(
            [
                [cos(self.angle), -sin(self.angle), 0],
                [sin(self.angle), cos(self.angle), 0],
                [0, 0, 1],
            ]
        )

    def update_rotated_points(self):
        rotated_points = []
        for point in self.points:
            rotated_points.append(self.rotation_matrix @ point)
        self.rotated = np.asarray(rotated_points)

    def spin(self):
        self.angle += self.spin_change
        self.calculate_rotation_matrix()
        self.update_rotated_points()
        self.calculate_surface_normals()

    def seen_tris_mask(self, seen_mask):
        self.tris_to_render = self.tris_to_render[seen_mask > 0]

    def calculate_surface_normals(self):
        # https://sites.google.com/site/dlampetest/python/
        #       calculating-normals-of-a-triangle-mesh-using-numpy
        tris_verts = self.rotated[self.tris]  # epic that this works
        self.surface_normals = np.cross(
            tris_verts[::, 1] - tris_verts[::, 0], tris_verts[::, 2] - tris_verts[::, 0]
        )
        self.surface_normals = self.normalize_v3(self.surface_normals)

    def normalize_v3(self, arr):
        # https://sites.google.com/site/dlampetest/python/
        #        calculating-normals-of-a-triangle-mesh-using-numpy
        lens = np.sqrt(arr[:, 0] ** 2 + arr[:, 1] ** 2 + arr[:, 2] ** 2)
        arr[:, 0] /= lens
        arr[:, 1] /= lens
        arr[:, 2] /= lens
        return arr


class cube(shape):
    def __init__(self, spin=0.01):
        super().__init__(spin)
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
    def __init__(self, spin=0.01):
        super().__init__(spin)
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

env = environment()
env.add_shape(cube())
env.add_shape(tetrahedron(spin=-0.01))

for i in range(10000):
    env.time_step()
    time.sleep(0.01)

profiler.disable()
stats = pstats.Stats(profiler)
stats.strip_dirs().sort_stats("tottime").print_stats(10)
