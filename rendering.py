import os
import numpy as np
from math import cos
from math import sin
import time
import sys
import cProfile
import pstats

screen_height = 100
screen_width = 200
pixels = screen_width * screen_height


class render:
    def __init__(self):
        self.pre_screen = []
        self.post_screen = []

        for _ in range(pixels):
            self.pre_screen.append("@")

        for _ in range(pixels):
            self.post_screen.append(" ")

        os.system("clear")
        os.system("tput civis")

    def __del__(self):
        os.system(f' echo "\x1B[{screen_height};{0}Hrenderer all done"')
        os.system("tput cnorm")

    def cordinates_from_index(self, i):
        y = i // screen_width
        x = i % screen_width
        return (x, y)

    def index_from_cordinates(self, x, y):
        return (y * screen_width) + x

    def render(self):
        buffer_ = ''
        for j, (post, pre) in enumerate(zip(self.post_screen, self.pre_screen)):
            if pre != post:
                x, y = self.cordinates_from_index(j)
                buffer_ += f"\x1B[{y};{x}H{post}"
                self.pre_screen[j] = self.post_screen[j]

        os.system(f' echo "{buffer_}"')

        for i in range(len(self.post_screen)):
            self.post_screen[i] = ' '

    def change(self, x, y, new_pixel):
        i = self.index_from_cordinates(x, y)
        self.post_screen[i] = new_pixel

    def plotLine(self, x0, y0, x1, y1):
            # Bresenham
            d_x =  abs(x1-x0)
            if x0 < x1:
                sx = 1
            else:
                sx = -1

            d_y = -abs(y1-y0)
            if y0 < y1:
                sy = 1
            else:
                sy = -1

            err = d_x+d_y

            self.change(x0, y0, '.')
            while x0 != x1 and y0 != y1:
                self.change(x0, y0, '.')
                e2 = 2*err
                if (e2 >= d_y):
                    err += d_y
                    x0 += sx
                if (e2 <= d_x):
                    err += d_x
                    y0 += sy



def translate_to_screen(point):
    half_width = screen_width // 2
    half_height = screen_height // 2
    x = point[0] * half_width
    y = point[1] * half_height
    x = int(x + half_width)
    y = int(y + half_height)
    if x == screen_width:
        x -= 1
    if y == screen_height:
        y -= 1
    return x, y


points = np.array(
    [
        [-0.5, -0.5, -0.5],
        [0.5, -0.5, -0.5],
        [0.5, 0.5, -0.5],
        [-0.5, 0.5, -0.5],
        [-0.5, -0.5, 0.5],
        [0.5, -0.5, 0.5],
        [0.5, 0.5, 0.5],
        [-0.5, 0.5, 0.5],
    ]
)

profiler = cProfile.Profile()
profiler.enable()

r = render()
angle = 0.0

for i in range(10000):

    rotationX = np.array(
        [
            [1, 0, 0],
            [0, cos(angle), -sin(angle)],
            [0, sin(angle), cos(angle)]
        ]
    )

    rotationY = np.array(
        [
            [cos(angle), 0, -sin(angle)],
            [0, 1, 0],
            [sin(angle), 0, cos(angle)]
        ]
    )

    rotationZ = np.array(
        [
            [cos(angle), -sin(angle), 0],
            [sin(angle), cos(angle), 0],
            [0, 0, 1]
        ]
    )

    angle += .02
    
    projected_points = []
    for point in points:
        rotated = rotationX @ rotationY @ rotationZ @ point
      
        distance = 2
        
        '''
        z = rotated[2]
        z = 1/(distance - z)
        z = 1 + z
        '''
        z = 1
        projection = np.array(
            [
                [1/z, 0, 0],
                [0, 1/z, 0]
            ]
        )

        projected = projection @ rotated
        x, y = translate_to_screen(projected)
        projected_points.append((x,y))

    for i in range(4):
        r.plotLine(*projected_points[i], *projected_points[(i + 1) % 4])
        r.plotLine(*projected_points[4], *projected_points[5])
        r.plotLine(*projected_points[5], *projected_points[6])
        r.plotLine(*projected_points[6], *projected_points[7])
        r.plotLine(*projected_points[7], *projected_points[4])
        # r.plotLine(*projected_points[i + 4], *projected_points[((i + 1) % 4) + 4])
        r.plotLine(*projected_points[i], *projected_points[i + 4])

    for x, y in projected_points:
        r.change(x, y, '#')
        
          
    # r.change(x, y, "#")

    r.render()

    time.sleep(.01)


profiler.disable()
stats = pstats.Stats(profiler)
stats.strip_dirs().sort_stats("tottime").print_stats(10)
