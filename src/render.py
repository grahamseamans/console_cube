# render.py Graham Seamans

import collections
import numpy as np
import os


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

    def triangle_raster(self, vects, shade):
        # http://www.sunshine2k.de/coding/java/TriangleRasterization/
        #       TriangleRasterization.html

        shade = self.get_shade(shade)
        vects.sort(key=lambda x: x[1])
        point = collections.namedtuple("point", ["x", "y"])
        a = point(vects[0][0], vects[0][1])
        b = point(vects[1][0], vects[1][1])
        c = point(vects[2][0], vects[2][1])

        if a.y == b.y:
            self.flat_triangle(c, a, b, shade)
        elif b.y == c.y:
            self.flat_triangle(a, b, c, shade)
        else:
            v4 = self.middle_vertex(a, b, c)
            self.flat_triangle(a, b, v4, shade)
            self.flat_triangle(c, b, v4, shade)

    def middle_vertex(self, a, b, c):
        point = collections.namedtuple("point", ["x", "y"])
        long_inv_slope = self.inv_slope(a, c)
        dy = b.y - a.y
        v4x = int(dy * long_inv_slope) + a.x
        return point(v4x, b.y)

    def flat_triangle(self, pointy, flat1, flat2, shade):
        assert flat1.y == flat2.y
        flat1, flat2 = self.swap_for_ascending_x(flat1, flat2)
        slope1, slope2 = self.slopes(pointy, flat1, flat2)
        step, y_flat = self.raster_movement(pointy, flat1)
        x1 = pointy.x
        x2 = pointy.x

        for y in range(pointy.y, y_flat, step):
            self.horiz_line(int(x1), int(x2), y, shade)
            x1 += slope1
            x2 += slope2

    def slopes(self, pointy, flat1, flat2):
        slope1 = self.inv_slope(pointy, flat1)
        slope2 = self.inv_slope(pointy, flat2)
        if pointy.y > flat1.y:
            slope1 *= -1
            slope2 *= -1
        return slope1, slope2

    def raster_movement(self, pointy, flat):
        if pointy.y > flat.y:
            step = -1
            y_flat = flat.y - 1
        else:
            step = 1
            y_flat = flat.y
        return step, y_flat

    def inv_slope(self, a, b):
        return self.safe_div(a.x - b.x, a.y - b.y)

    def safe_div(self, a, b):
        if b == 0:
            return 0
        else:
            return a / b

    def swap_for_ascending_x(self, a, b):
        if a.x > b.x:
            return (b, a)
        else:
            return (a, b)

    def horiz_line(self, x1, x2, y, shade):
        for x in range(x1, x2):
            self.post_screen[x][y] = shade

    def get_shade(self, shade):
        shades = ",-_+*^c#%@"
        if shade < 0:
            return "."
        else:
            return shades[int(shade * 10)]
