# render.py Graham Seamans

import collections
import numpy as np
import os

PIXEL_WIDTH = 2.2
PALETTE = ",-_+*^c#%@"

point = collections.namedtuple("point", ["x", "y"])


class render:
    def __init__(self):
        self.projection = np.array([[1, 0, 0], [0, 1, 0]])
        self.pre_screen = []
        self.post_screen = []
        self.screen_height = 0
        self.screen_width = 0
        self.pixels = 0
        self.terminal_check()
        self.reset_buffers()
        os.system("clear")
        os.system("tput civis")

    def __del__(self):
        os.system("tput cnorm")

    def terminal_check(self):
        term = os.get_terminal_size()
        if term.columns != self.screen_width or term.lines != self.screen_height:
            size = min(int(term.columns / PIXEL_WIDTH), term.lines)
            self.screen_height, self.screen_width = size, int(size * PIXEL_WIDTH)
            self.pixels = self.screen_width * self.screen_height
            self.reset_buffers()

    def reset_buffers(self):
        for i in range(self.screen_width):
            self.pre_screen.append([])
            self.post_screen.append([])
            for _ in range(self.screen_height):
                self.pre_screen[i].append(" ")
                self.post_screen[i].append(" ")

    def render(self):
        self.terminal_check()
        command_buffer = ""
        # not very pythonic but it's ~60% faster and this was slow
        for x in range(self.screen_width):
            for y in range(self.screen_height):
                if self.pre_screen[x][y] != self.post_screen[x][y]:
                    command_buffer += f"\x1B[{y};{x}H{self.post_screen[x][y]}"
                    self.pre_screen[x][y] = self.post_screen[x][y]
                self.post_screen[x][y] = " "
        os.system(f' echo "{command_buffer}"')

    def to_buff(self, shape):
        for triangle in shape.tris_to_render:
            tri, shade = self.parse_tri(triangle)
            projected_tri = self.project_tri(tri, shape)
            self.triangle_raster(projected_tri, shade)

    def parse_tri(self, triangle):
        tri = triangle[:-1].astype("int32")
        shade = triangle[-1]
        return tri, shade

    def project_tri(self, tri, shape):
        projected_tri = []
        for vect in shape.rotated[tri]:
            projected_tri.append(self.vect_to_screen(vect))
        return projected_tri

    def vect_to_screen(self, vect):
        vect = self.projection @ vect
        vect = self.stretch_shift_to_screen(vect)
        return self.vect_to_point(vect)

    def stretch_shift_to_screen(self, vect):
        half_screen = [self.screen_width // 2, self.screen_height // 2]
        vect *= half_screen
        vect += half_screen
        return (int(vect[0]), int(vect[1]))

    def vect_to_point(self, vect):
        return point(vect[0], vect[1])

    def triangle_raster(self, vects, shade):
        # http://www.sunshine2k.de/coding/java/TriangleRasterization/
        #       TriangleRasterization.html
        shade = self.get_shade(shade)
        vects.sort(key=lambda p: p.y)
        a, b, c = vects
        if a.y == b.y:
            self.flat_triangle(c, a, b, shade)
        elif b.y == c.y:
            self.flat_triangle(a, b, c, shade)
        else:
            v4 = self.middle_vertex(a, b, c)
            self.flat_triangle(a, b, v4, shade)
            self.flat_triangle(c, b, v4, shade)

    def get_shade(self, shade):
        if shade < 0:
            return "."
        else:
            return PALETTE[int(shade * 10)]

    def middle_vertex(self, a, b, c):
        dy = b.y - a.y
        v4x = int(dy * self.inv_slope(a, c)) + a.x
        return point(v4x, b.y)

    def flat_triangle(self, pointy, flat1, flat2, shade):
        assert flat1.y == flat2.y
        flat1, flat2 = self.swap_for_ascending_x(flat1, flat2)
        slope1, slope2 = self.slopes(pointy, flat1, flat2)
        step, y_flat = self.raster_movement(pointy, flat1)
        x1 = pointy.x
        x2 = pointy.x

        for y in range(pointy.y, y_flat, step):
            self.horiz_line(round(x1), round(x2), y, shade)
            x1 += slope1
            x2 += slope2

    def swap_for_ascending_x(self, a, b):
        if a.x > b.x:
            return (b, a)
        else:
            return (a, b)

    def slopes(self, pointy, flat1, flat2):
        slope1 = self.inv_slope(pointy, flat1)
        slope2 = self.inv_slope(pointy, flat2)
        if pointy.y > flat1.y:
            slope1 *= -1
            slope2 *= -1
        return slope1, slope2

    def inv_slope(self, a, b):
        return self.safe_div(a.x - b.x, a.y - b.y)

    def safe_div(self, a, b):
        if b == 0:
            return 0
        else:
            return a / b

    def raster_movement(self, pointy, flat):
        if pointy.y > flat.y:
            step = -1
            y_flat = flat.y - 1
        else:
            step = 1
            y_flat = flat.y
        return step, y_flat

    def horiz_line(self, x1, x2, y, shade):
        for x in range(x1, x2):
            self.post_screen[x][y] = shade
